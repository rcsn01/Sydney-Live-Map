from __future__ import annotations
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from . import models

def get_locations(session: Session):
    return session.scalars(select(models.Location)).all()


def get_location_types(session: Session) -> list[str]:
    """Return a list of distinct values in the Location.type column."""
    stmt = select(models.Location.type).distinct().order_by(models.Location.type)
    return [row[0] for row in session.execute(stmt).all()]

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
        intensity = compute_intensity(metric.count)
        results.append((loc, intensity))
    return results

def compute_intensity(count: int) -> float:
    # Simple heuristic: normalize against a rough maximum and clamp
    norm = min(count / 2000.0, 1.0)
    return round(norm, 3)


def get_metrics_for_type(session: Session, type_value: str, since: datetime):
    """Return aggregated metrics (sum of counts) per timestamp for all locations of a given type."""
    stmt = (
        select(models.Metric.timestamp, func.sum(models.Metric.count).label('count'))
        .join(models.Location, models.Metric.location_id == models.Location.id)
        .where(models.Location.type == type_value, models.Metric.timestamp >= since)
        .group_by(models.Metric.timestamp)
        .order_by(models.Metric.timestamp.asc())
    )
    rows = session.execute(stmt).all()
    # rows are tuples (timestamp, count)
    return [ {'timestamp': r[0], 'count': int(r[1] or 0)} for r in rows ]
