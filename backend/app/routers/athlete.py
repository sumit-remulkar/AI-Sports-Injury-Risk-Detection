from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(
    prefix="/athletes",
    tags=["Athletes"]
)


@router.post("/", response_model=schemas.AthleteResponse)
def create_athlete(
    athlete: schemas.AthleteCreate,
    db: Session = Depends(get_db)
):
    return crud.create_athlete(db, athlete)


@router.get("/", response_model=list[schemas.AthleteResponse])
def get_athletes(db: Session = Depends(get_db)):
    return crud.get_athletes(db)


@router.get("/{athlete_id}", response_model=schemas.AthleteResponse)
def get_athlete(
    athlete_id: int,
    db: Session = Depends(get_db)
):
    athlete = crud.get_athlete(db, athlete_id)

    if athlete is None:
        raise HTTPException(
            status_code=404,
            detail="Athlete not found"
        )

    return athlete


@router.put("/{athlete_id}", response_model=schemas.AthleteResponse)
def update_athlete(
    athlete_id: int,
    athlete: schemas.AthleteCreate,
    db: Session = Depends(get_db)
):
    updated = crud.update_athlete(
        db,
        athlete_id,
        athlete
    )

    if updated is None:
        raise HTTPException(
            status_code=404,
            detail="Athlete not found"
        )

    return updated


@router.delete("/{athlete_id}")
def delete_athlete(
    athlete_id: int,
    db: Session = Depends(get_db)
):
    deleted = crud.delete_athlete(db, athlete_id)

    if deleted is None:
        raise HTTPException(
            status_code=404,
            detail="Athlete not found"
        )

    return {"message": "Athlete deleted successfully"}