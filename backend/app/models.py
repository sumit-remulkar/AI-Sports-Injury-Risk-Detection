import uuid

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Text,
    JSON,
    TIMESTAMP,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    """
    Core account table. Every person who logs in (athlete, coach,
    physiotherapist, sports scientist, admin) has exactly one row here.
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="athlete")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    athlete_profile = relationship(
        "AthleteProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class AthleteProfile(Base):
    """
    Athlete-specific data. One-to-one with User (only created when
    role == 'athlete'). Kept separate from User so coaches/admins
    don't carry unused athlete columns.
    """
    __tablename__ = "athlete_profiles"

    athlete_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)

    age = Column(Integer)
    gender = Column(String)
    sport = Column(String)
    position = Column(String)
    height = Column(Float)
    weight = Column(Float)
    injury_history = Column(Text)
    training_load = Column(String)

    user = relationship("User", back_populates="athlete_profile")
    videos = relationship("UploadedVideo", back_populates="athlete", cascade="all, delete-orphan")
    predictions = relationship("InjuryPrediction", back_populates="athlete", cascade="all, delete-orphan")


class UploadedVideo(Base):
    __tablename__ = "uploaded_videos"

    video_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    athlete_id = Column(UUID(as_uuid=True), ForeignKey("athlete_profiles.athlete_id"), nullable=False)
    file_name = Column(String)
    upload_date = Column(TIMESTAMP(timezone=True), server_default=func.now())
    video_path = Column(Text)

    athlete = relationship("AthleteProfile", back_populates="videos")
    pose_frames = relationship("PoseData", back_populates="video", cascade="all, delete-orphan")


class PoseData(Base):
    __tablename__ = "pose_data"

    pose_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("uploaded_videos.video_id"), nullable=False)
    frame_number = Column(Integer)
    joint_coordinates = Column(JSON)
    joint_angles = Column(JSON)

    video = relationship("UploadedVideo", back_populates="pose_frames")


class InjuryPrediction(Base):
    __tablename__ = "injury_predictions"

    prediction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    athlete_id = Column(UUID(as_uuid=True), ForeignKey("athlete_profiles.athlete_id"), nullable=False)
    injury_type = Column(String)
    risk_score = Column(Float)
    risk_level = Column(String)
    prediction_date = Column(TIMESTAMP(timezone=True), server_default=func.now())

    athlete = relationship("AthleteProfile", back_populates="predictions")
    recommendations = relationship("Recommendation", back_populates="prediction", cascade="all, delete-orphan")


class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("injury_predictions.prediction_id"), nullable=False)
    posture_correction = Column(Text)
    exercise_plan = Column(Text)
    recovery_plan = Column(Text)

    prediction = relationship("InjuryPrediction", back_populates="recommendations")


class Report(Base):
    __tablename__ = "reports"

    report_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    athlete_id = Column(UUID(as_uuid=True), ForeignKey("athlete_profiles.athlete_id"), nullable=False)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("injury_predictions.prediction_id"))
    report_file = Column(Text)
    generated_date = Column(TIMESTAMP(timezone=True), server_default=func.now())
