from sqlalchemy.orm import Session
from . import models, schemas


def create_athlete(db: Session, athlete: schemas.AthleteCreate):
    db_athlete = models.Athlete(**athlete.model_dump())
    db.add(db_athlete)
    db.commit()
    db.refresh(db_athlete)
    return db_athlete


def get_athletes(db: Session):
    return db.query(models.Athlete).all()


def get_athlete(db: Session, athlete_id: int):
    return db.query(models.Athlete).filter(
        models.Athlete.id == athlete_id
    ).first()


def update_athlete(db: Session, athlete_id: int, athlete: schemas.AthleteUpdate):
    db_athlete = get_athlete(db, athlete_id)

    if not db_athlete:
        return None

    for key, value in athlete.model_dump().items():
        setattr(db_athlete, key, value)

    db.commit()
    db.refresh(db_athlete)

    return db_athlete


def delete_athlete(db: Session, athlete_id: int):
    db_athlete = get_athlete(db, athlete_id)

    if not db_athlete:
        return None

    db.delete(db_athlete)
    db.commit()

    return db_athlete