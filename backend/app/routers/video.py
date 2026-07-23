import shutil
import uuid
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import crud, schemas, models
from ..database import get_db
from ..auth import get_current_user
from ..services import video_processing, pose_estimation, biomechanics, annotation

router = APIRouter(prefix="/videos", tags=["Videos"])

# backend/app/routers/video.py -> parents[2] = backend/ -> backend/uploads
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"

STAFF_ROLES = ("coach", "physiotherapist", "sports_scientist", "admin")


def _require_athlete_profile(current_user: models.User, db: Session) -> models.AthleteProfile:
    profile = crud.get_athlete_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="No athlete profile for this account -- only athletes upload videos.",
        )
    return profile


def _check_can_view(video: models.UploadedVideo, current_user: models.User, db: Session):
    if current_user.role in STAFF_ROLES:
        return
    profile = crud.get_athlete_by_user_id(db, current_user.id)
    if not profile or profile.athlete_id != video.athlete_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this video")


def _pose_rows_to_frame_metrics(pose_rows: list[models.PoseData]) -> list[biomechanics.FrameMetrics]:
    """Reconstructs FrameMetrics from what's already stored in the DB,
    so summaries can be recomputed on GET without re-running pose
    estimation on the video every time."""
    result = []
    for row in pose_rows:
        ja = row.joint_angles or {}
        result.append(
            biomechanics.FrameMetrics(
                frame_number=row.frame_number,
                left_knee_angle=ja.get("left_knee"),
                right_knee_angle=ja.get("right_knee"),
                left_elbow_angle=ja.get("left_elbow"),
                right_elbow_angle=ja.get("right_elbow"),
                left_hip_angle=ja.get("left_hip"),
                right_hip_angle=ja.get("right_hip"),
                trunk_lean_deg=ja.get("trunk_lean_deg"),
                knee_valgus_proxy=ja.get("knee_valgus_proxy"),
                knee_symmetry_diff=ja.get("knee_symmetry_diff"),
            )
        )
    return result


def _to_video_response(video: models.UploadedVideo) -> schemas.VideoResponse:
    return schemas.VideoResponse(
        video_id=video.video_id,
        athlete_id=video.athlete_id,
        file_name=video.file_name,
        upload_date=video.upload_date,
        status=video.status,
        error_message=video.error_message,
        has_annotated_video=bool(video.annotated_video_path),
    )


@router.post("/upload", response_model=schemas.VideoDetailResponse, status_code=201)
def upload_video(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Saves the video, then processes it SYNCHRONOUSLY (extract frames ->
    pose estimation -> biomechanics -> annotated video) before
    responding. That's fine for Milestone 2/3 testing with short clips,
    but the architecture doc's Redis/queue component exists for a
    reason -- for real usage this should become a background job so an
    upload request doesn't hang for the length of a full video's worth
    of pose inference.
    """
    profile = _require_athlete_profile(current_user, db)

    try:
        video_processing.validate_upload_filename(file.filename)
    except video_processing.InvalidVideoError as e:
        raise HTTPException(status_code=400, detail=str(e))

    athlete_dir = UPLOAD_DIR / str(profile.athlete_id)
    athlete_dir.mkdir(parents=True, exist_ok=True)

    video_id = uuid.uuid4()
    dest_path = athlete_dir / f"{video_id}{Path(file.filename).suffix.lower()}"

    with dest_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        info = video_processing.get_video_info(str(dest_path))
    except video_processing.InvalidVideoError as e:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))

    video = crud.create_video(db, video_id, profile.athlete_id, file.filename, str(dest_path))
    crud.update_video_status(db, video.video_id, "processing")

    raw_annotated_path = athlete_dir / f"{video_id}_annotated_raw.mp4"
    annotated_path = athlete_dir / f"{video_id}_annotated.mp4"

    frame_metrics: list[biomechanics.FrameMetrics] = []
    try:
        with pose_estimation.PoseEstimator() as estimator, \
             annotation.AnnotatedVideoWriter(str(raw_annotated_path), info.width, info.height) as ann_writer:

            for frame_number, frame_rgb in video_processing.extract_frames(str(dest_path)):
                keypoints = estimator.estimate(frame_rgb)

                metrics = None
                if keypoints is not None:
                    metrics = biomechanics.analyze_frame(frame_number, keypoints)
                    frame_metrics.append(metrics)

                    crud.add_pose_data(
                        db,
                        video_id=video.video_id,
                        frame_number=frame_number,
                        joint_coordinates={
                            name: {"x": p.x, "y": p.y, "visibility": p.visibility}
                            for name, p in keypoints.items()
                        },
                        joint_angles={
                            "left_knee": metrics.left_knee_angle,
                            "right_knee": metrics.right_knee_angle,
                            "left_elbow": metrics.left_elbow_angle,
                            "right_elbow": metrics.right_elbow_angle,
                            "left_hip": metrics.left_hip_angle,
                            "right_hip": metrics.right_hip_angle,
                            "trunk_lean_deg": metrics.trunk_lean_deg,
                            "knee_valgus_proxy": metrics.knee_valgus_proxy,
                            "knee_symmetry_diff": metrics.knee_symmetry_diff,
                        },
                    )

                # Written for every sampled frame regardless of detection,
                # so the annotated video's motion still flows -- frames
                # with no detection just get a "no person detected" tag
                # instead of being silently dropped (that would jump-cut
                # the playback and hide how often detection is failing).
                ann_writer.write(frame_rgb, keypoints, metrics)

    except FileNotFoundError as e:
        # pose model .task file hasn't been downloaded yet
        crud.update_video_status(db, video.video_id, "failed", error_message=str(e))
        raise HTTPException(status_code=503, detail=str(e))
    except video_processing.InvalidVideoError as e:
        crud.update_video_status(db, video.video_id, "failed", error_message=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    if not frame_metrics:
        raw_annotated_path.unlink(missing_ok=True)
        crud.update_video_status(
            db, video.video_id, "failed",
            error_message="No person detected in any analyzed frame. Try a clearer, well-lit, single-person clip.",
        )
    else:
        # OpenCV's mp4v output isn't reliably browser-playable (shows as
        # corrupted color noise in most <video> tags) -- re-encode to
        # real H.264 before exposing it. If that fails (no ffmpeg on
        # this machine), fall back to no annotated video rather than
        # serving a file that'll look broken to the user.
        if annotation.reencode_for_browser(str(raw_annotated_path), str(annotated_path)):
            video.annotated_video_path = str(annotated_path)
        raw_annotated_path.unlink(missing_ok=True)
        db.commit()
        crud.update_video_status(db, video.video_id, "completed")

    video = crud.get_video(db, video.video_id)
    summary = biomechanics.summarize(frame_metrics) if frame_metrics else None

    return schemas.VideoDetailResponse(
        video_id=video.video_id,
        athlete_id=video.athlete_id,
        file_name=video.file_name,
        upload_date=video.upload_date,
        status=video.status,
        error_message=video.error_message,
        has_annotated_video=bool(video.annotated_video_path),
        biomechanics_summary=summary,
    )


@router.get("/", response_model=list[schemas.VideoResponse])
def list_my_videos(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = _require_athlete_profile(current_user, db)
    videos = crud.get_videos_for_athlete(db, profile.athlete_id)
    return [_to_video_response(v) for v in videos]


@router.get("/{video_id}", response_model=schemas.VideoDetailResponse)
def get_video_detail(
    video_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    video = crud.get_video(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    _check_can_view(video, current_user, db)

    pose_rows = crud.get_pose_data_for_video(db, video_id)
    frame_metrics = _pose_rows_to_frame_metrics(pose_rows)
    summary = biomechanics.summarize(frame_metrics) if frame_metrics else None

    return schemas.VideoDetailResponse(
        video_id=video.video_id,
        athlete_id=video.athlete_id,
        file_name=video.file_name,
        upload_date=video.upload_date,
        status=video.status,
        error_message=video.error_message,
        has_annotated_video=bool(video.annotated_video_path),
        biomechanics_summary=summary,
    )


@router.get("/{video_id}/frames", response_model=list[schemas.FrameMetricsResponse])
def get_video_frames(
    video_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    video = crud.get_video(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    _check_can_view(video, current_user, db)

    pose_rows = crud.get_pose_data_for_video(db, video_id)
    return _pose_rows_to_frame_metrics(pose_rows)


@router.get("/{video_id}/annotated")
def get_annotated_video(
    video_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    video = crud.get_video(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    _check_can_view(video, current_user, db)

    if not video.annotated_video_path or not Path(video.annotated_video_path).exists():
        raise HTTPException(status_code=404, detail="No annotated video available for this upload")

    return FileResponse(video.annotated_video_path, media_type="video/mp4")


@router.delete("/{video_id}")
def delete_video(
    video_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Only the athlete who owns the video (or an admin) can delete it --
    coaches/physios/sports_scientists can VIEW any athlete's videos
    (see _check_can_view) but that's not the same as being allowed to
    delete someone else's data.
    """
    video = crud.get_video(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    profile = crud.get_athlete_by_user_id(db, current_user.id)
    is_owner = profile is not None and profile.athlete_id == video.athlete_id
    if not (is_owner or current_user.role == "admin"):
        raise HTTPException(status_code=403, detail="Not authorized to delete this video")

    for path_str in (video.video_path, video.annotated_video_path):
        if path_str:
            Path(path_str).unlink(missing_ok=True)

    crud.delete_video(db, video_id)
    return {"message": "Video deleted successfully"}

