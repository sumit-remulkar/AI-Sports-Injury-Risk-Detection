from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


# ---------------------------------------------------------------------------
# Auth / User
# ---------------------------------------------------------------------------

VALID_ROLES = {"athlete", "coach", "physiotherapist", "sports_scientist", "admin"}


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: str = "athlete"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# Athlete Profile
# ---------------------------------------------------------------------------

class AthleteBase(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    sport: Optional[str] = None
    position: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    injury_history: Optional[str] = None
    training_load: Optional[str] = None


class AthleteCreate(AthleteBase):
    pass


class AthleteUpdate(AthleteBase):
    """All fields optional on purpose -- this is what makes PUT/PATCH a
    real partial update instead of forcing every field to be resent."""
    pass


class AthleteResponse(AthleteBase):
    athlete_id: UUID
    user_id: UUID

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Video / Pose / Biomechanics (Milestone 2)
# ---------------------------------------------------------------------------

class VideoResponse(BaseModel):
    video_id: UUID
    athlete_id: UUID
    file_name: str
    upload_date: datetime
    status: str
    error_message: Optional[str] = None
    has_annotated_video: bool = False

    class Config:
        from_attributes = True


class FrameMetricsResponse(BaseModel):
    frame_number: int
    left_knee_angle: Optional[float] = None
    right_knee_angle: Optional[float] = None
    left_elbow_angle: Optional[float] = None
    right_elbow_angle: Optional[float] = None
    left_hip_angle: Optional[float] = None
    right_hip_angle: Optional[float] = None
    trunk_lean_deg: Optional[float] = None
    knee_valgus_proxy: Optional[float] = None
    knee_symmetry_diff: Optional[float] = None


class BiomechanicsSummaryResponse(BaseModel):
    frames_analyzed: int
    frames_with_detection: int
    avg_left_knee_angle: Optional[float] = None
    avg_right_knee_angle: Optional[float] = None
    avg_trunk_lean_deg: Optional[float] = None
    left_knee_rom: Optional[float] = None
    right_knee_rom: Optional[float] = None
    knee_rom_asymmetry: Optional[float] = None
    peak_knee_valgus_proxy: Optional[float] = None


class VideoDetailResponse(VideoResponse):
    biomechanics_summary: Optional[BiomechanicsSummaryResponse] = None

