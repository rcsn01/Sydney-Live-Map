from __future__ import annotations
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
import os

from .database import Base, engine, get_db
from . import models, schemas, crud, seed

API_PREFIX = os.getenv("API_PREFIX", "/api")
SEED_ON_START = os.getenv("SEED_ON_START", "1") == "1"

app = FastAPI(title="Sydney Live Map API", openapi_url=f"{API_PREFIX}/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    if SEED_ON_START:
        with next(get_db()) as session:
            seed.seed_data(session)

@app.get(f"{API_PREFIX}/health")
def health():
    return {"status": "ok"}

@app.get(f"{API_PREFIX}/locations", response_model=list[schemas.LocationWithIntensity])
def list_locations(at: datetime | None = None, db: Session = Depends(get_db)):
    pairs = crud.latest_intensity_for_locations(db, at)
    return [schemas.LocationWithIntensity(**schemas.LocationBase.model_validate(loc).model_dump(), intensity=intensity) for loc, intensity in pairs]

@app.get(f"{API_PREFIX}/locations/{{location_id}}", response_model=schemas.LocationBase)
def get_location(location_id: int, db: Session = Depends(get_db)):
    loc = crud.get_location(db, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    return loc

@app.get(f"{API_PREFIX}/locations/{{location_id}}/metrics", response_model=list[schemas.MetricPoint])
def location_metrics(location_id: int, hours: int = 24, db: Session = Depends(get_db)):
    loc = crud.get_location(db, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    metrics = crud.get_metrics_for_location(db, location_id, since)
    return metrics


@app.get(f"{API_PREFIX}/metrics")
def metrics_by_type(type: str, hours: int = 24, db: Session = Depends(get_db)):
    """Return aggregated metrics (sum of counts) per timestamp for all locations matching the given type."""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    rows = crud.get_metrics_for_type(db, type, since)
    return rows


@app.get(f"{API_PREFIX}/location-types", response_model=list[str])
def location_types(db: Session = Depends(get_db)):
    """Return all distinct values of the `type` column from the locations table."""
    types = crud.get_location_types(db)
    return types
