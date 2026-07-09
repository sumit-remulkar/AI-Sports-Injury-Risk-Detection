from pydantic import BaseModel


class AthleteBase(BaseModel):
    full_name: str
    age: int
    gender: str
    sport: str
    position: str


class AthleteCreate(AthleteBase):
    pass


class AthleteUpdate(AthleteBase):
    pass


class AthleteResponse(AthleteBase):
    id: int

    class Config:
        from_attributes = True