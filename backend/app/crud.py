from sqlalchemy.orm import Session

from . import models, schemas
from .auth import hash_password


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    db_user = models.User(
        full_name=user.full_name,
        email=user.email,
        password_hash=hash_password(user.password),
        role=user.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Athletes get an empty profile row automatically so /athletes/me
    # always has something to fetch/update.
    if db_user.role == "athlete":
        db.add(models.AthleteProfile(user_id=db_user.id))
        db.commit()

    return db_user


# ---------------------------------------------------------------------------
# Athlete Profile
# ---------------------------------------------------------------------------

def get_athlete_by_user_id(db: Session, user_id):
    return db.query(models.AthleteProfile).filter(
        models.AthleteProfile.user_id == user_id
    ).first()


def get_athlete(db: Session, athlete_id):
    return db.query(models.AthleteProfile).filter(
        models.AthleteProfile.athlete_id == athlete_id
    ).first()


def get_athletes(db: Session):
    return db.query(models.AthleteProfile).all()


def update_athlete(db: Session, athlete_id, athlete: schemas.AthleteUpdate):
    db_athlete = get_athlete(db, athlete_id)
    if not db_athlete:
        return None

    for key, value in athlete.model_dump(exclude_unset=True).items():
        setattr(db_athlete, key, value)

    db.commit()
    db.refresh(db_athlete)
    return db_athlete


def delete_athlete(db: Session, athlete_id):
    db_athlete = get_athlete(db, athlete_id)
    if not db_athlete:
        return None
    db.delete(db_athlete)
    db.commit()
    return db_athlete


# ---------------------------------------------------------------------------
# Video / Pose Data (Milestone 2)
# ---------------------------------------------------------------------------

def create_video(db: Session, video_id, athlete_id, file_name: str, video_path: str) -> models.UploadedVideo:
    video = models.UploadedVideo(
        video_id=video_id,
        athlete_id=athlete_id,
        file_name=file_name,
        video_path=video_path,
        status="uploaded",
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


def update_video_status(db: Session, video_id, status: str, error_message: str | None = None):
    video = get_video(db, video_id)
    if not video:
        return None
    video.status = status
    video.error_message = error_message
    db.commit()
    db.refresh(video)
    return video


def get_video(db: Session, video_id):
    return db.query(models.UploadedVideo).filter(
        models.UploadedVideo.video_id == video_id
    ).first()


def get_videos_for_athlete(db: Session, athlete_id):
    return (
        db.query(models.UploadedVideo)
        .filter(models.UploadedVideo.athlete_id == athlete_id)
        .order_by(models.UploadedVideo.upload_date.desc())
        .all()
    )


def add_pose_data(db: Session, video_id, frame_number: int, joint_coordinates: dict, joint_angles: dict):
    pose = models.PoseData(
        video_id=video_id,
        frame_number=frame_number,
        joint_coordinates=joint_coordinates,
        joint_angles=joint_angles,
    )
    db.add(pose)
    db.commit()
    return pose


def get_pose_data_for_video(db: Session, video_id):
    return (
        db.query(models.PoseData)
        .filter(models.PoseData.video_id == video_id)
        .order_by(models.PoseData.frame_number)
        .all()
    )


def delete_video(db: Session, video_id):
    video = get_video(db, video_id)
    if not video:
        return None
    db.delete(video)  # cascades to pose_data rows via the model relationship
    db.commit()
    return video

