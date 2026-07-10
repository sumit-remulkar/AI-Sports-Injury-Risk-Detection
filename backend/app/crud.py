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

    # exclude_unset=True -> only fields the client actually sent get
    # overwritten. This is what makes AthleteUpdate a real PATCH-style update.
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

