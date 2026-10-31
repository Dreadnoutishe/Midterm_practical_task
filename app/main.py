from decimal import Decimal
from typing import Annotated, Literal
from fastapi import Depends, FastAPI, HTTPException, Path, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from .database import get_db
from .models import HuntLog, WantedCriminal
from .schemas import CriminalOut, HuntCreate, HuntOut, HuntPatch

app = FastAPI(title="Space Bounty Hunters API", version="1.0.0")
DB = Annotated[Session, Depends(get_db)]
PositiveID = Annotated[int, Path(gt=0)]
Reward = Annotated[Decimal | None, Query(ge=0, max_digits=14, decimal_places=2)]

def require(db, model, record_id):
    record = db.get(model, record_id)
    if record is None:
        raise HTTPException(404, f"{model.__name__} not found")
    return record

@app.get("/api/criminals/", response_model=list[CriminalOut], tags=["Criminals"])
def list_criminals(db: DB, min_reward: Reward = None, max_reward: Reward = None,
                   armed: bool | None = None, has_crew: bool | None = None,
                   escape_master: bool | None = None,
                   sort: Literal["reward", "-reward"] | None = None):
    if min_reward is not None and max_reward is not None and min_reward > max_reward:
        raise HTTPException(422, "min_reward must be less than or equal to max_reward")
    query = select(WantedCriminal)
    if min_reward is not None:
        query = query.where(WantedCriminal.reward >= min_reward)
    if max_reward is not None:
        query = query.where(WantedCriminal.reward <= max_reward)
    for key, value in (("armed", armed), ("has_crew", has_crew), ("escape_master", escape_master)):
        if value is not None:
            query = query.where(getattr(WantedCriminal, key) == value)
    if sort is not None:
        query = query.order_by(WantedCriminal.reward.desc() if sort == "-reward" else WantedCriminal.reward.asc())
    return db.scalars(query.order_by(WantedCriminal.id)).all()

@app.get("/api/criminals/{id}/", response_model=CriminalOut, tags=["Criminals"])
def get_criminal(id: PositiveID, db: DB):
    return require(db, WantedCriminal, id)

@app.get("/api/hunts/", response_model=list[HuntOut], tags=["Hunts"])
def list_hunts(db: DB, criminal_id: Annotated[int | None, Query(gt=0)] = None):
    query = select(HuntLog)
    if criminal_id is not None:
        query = query.where(HuntLog.criminal_id == criminal_id)
    return db.scalars(query.order_by(HuntLog.id)).all()

@app.get("/api/hunts/{id}/", response_model=HuntOut, tags=["Hunts"])
def get_hunt(id: PositiveID, db: DB):
    return require(db, HuntLog, id)

@app.post("/api/hunts/", response_model=HuntOut, status_code=status.HTTP_201_CREATED, tags=["Hunts"])
def create_hunt(body: HuntCreate, db: DB):
    require(db, WantedCriminal, body.criminal_id)
    hunt = HuntLog(**body.model_dump())
    db.add(hunt)
    db.commit()
    db.refresh(hunt)
    return hunt

@app.patch("/api/hunts/{id}/", response_model=HuntOut, tags=["Hunts"])
def patch_hunt(id: PositiveID, body: HuntPatch, db: DB):
    hunt = require(db, HuntLog, id)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(hunt, key, value)
    db.commit()
    db.refresh(hunt)
    return hunt

@app.delete("/api/hunts/{id}/", status_code=status.HTTP_204_NO_CONTENT, tags=["Hunts"])
def delete_hunt(id: PositiveID, db: DB):
    hunt = require(db, HuntLog, id)
    db.delete(hunt)
    db.commit()
    return Response(status_code=204)
