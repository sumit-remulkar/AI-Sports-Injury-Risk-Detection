from fastapi import FastAPI
from .database import engine
from . import models
from .routers import athlete

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Sports Injury Risk Detection API"
)
app.include_router(athlete.router)

@app.get("/")
def root():
    return {
        "message": "AI Sports Injury Risk Detection Backend Running"
    }