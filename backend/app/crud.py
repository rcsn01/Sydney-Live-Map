from __future__ import annotations
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from . import models

def get_locations(session: Session):
    return session.scalars(select(models.Location)).all()

def get_location(session: Session, location_id: int):
    return session.get(models.Location, location_id)

def get_metrics_for_location(session: Session, location_id: int, since: datetime):
    stmt = (
        select(models.Metric)
        .where(models.Metric.location_id == location_id, models.Metric.timestamp >= since)
        .order_by(models.Metric.timestamp.asc())
    )
    return session.scalars(stmt).all()

def latest_intensity_for_locations(session: Session, at: datetime | None = None):
    if at is None:
        at = datetime.now(timezone.utc)
    # Get the latest metric at or before 'at' per location
    subq = (
        select(
            models.Metric.location_id,
            func.max(models.Metric.timestamp).label('max_ts')
        )
        .where(models.Metric.timestamp <= at)
        .group_by(models.Metric.location_id)
        .subquery()
    )

    join_stmt = (
        select(models.Location, models.Metric)
        .join(subq, subq.c.location_id == models.Location.id)
        .join(models.Metric, (models.Metric.location_id == subq.c.location_id) & (models.Metric.timestamp == subq.c.max_ts))
    )

    rows = session.execute(join_stmt).all()

    results = []
    for loc, metric in rows:
        intensity = compute_intensity(metric.pedestrian_count, metric.traffic_count)
        results.append((loc, intensity))
    return results

def compute_intensity(ped_count: int, traffic_count: int) -> float:
    # Simple heuristic: normalized sum
    # Assume rough typical maxima for scaling
    ped_norm = min(ped_count / 1000.0, 1.0)
    traffic_norm = min(traffic_count / 2000.0, 1.0)
    return round((ped_norm * 0.6 + traffic_norm * 0.4), 3)
