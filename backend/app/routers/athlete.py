from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas, models
from ..database import get_db
from ..auth import get_current_user, require_role

router = APIRouter(prefix="/athletes", tags=["Athletes"])


# ---------------------------------------------------------------------------
# Self-service: any logged-in athlete manages their own profile
# ---------------------------------------------------------------------------

@router.get("/me", response_model=schemas.AthleteResponse)
def get_my_profile(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = crud.get_athlete_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Athlete profile not found")
    return profile


@router.put("/me", response_model=schemas.AthleteResponse)
def update_my_profile(
    athlete: schemas.AthleteUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = crud.get_athlete_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Athlete profile not found")
    return crud.update_athlete(db, profile.athlete_id, athlete)


# ---------------------------------------------------------------------------
# Staff-only: coach / physio / sports scientist / admin viewing athletes
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[schemas.AthleteResponse])
def get_athletes(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_role("coach", "physiotherapist", "sports_scientist", "admin")
    ),
):
    return crud.get_athletes(db)


@router.get("/{athlete_id}", response_model=schemas.AthleteResponse)
def get_athlete(
    athlete_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_role("coach", "physiotherapist", "sports_scientist", "admin")
    ),
):
    athlete = crud.get_athlete(db, athlete_id)
    if athlete is None:
        raise HTTPException(status_code=404, detail="Athlete not found")
    return athlete


@router.delete("/{athlete_id}")
def delete_athlete(
    athlete_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("admin")),
):
    deleted = crud.delete_athlete(db, athlete_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Athlete not found")
    return {"message": "Athlete deleted successfully"}
