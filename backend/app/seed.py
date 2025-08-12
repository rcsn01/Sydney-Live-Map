from __future__ import annotations
from datetime import datetime, timedelta, timezone
import random
from sqlalchemy.orm import Session
from . import models

SEED_LOCATIONS = [
    {"name": "George St & Martin Pl", "latitude": -33.8675, "longitude": 151.2070, "type": "pedestrian"},
    {"name": "Pitt St Mall", "latitude": -33.8707, "longitude": 151.2079, "type": "pedestrian"},
    {"name": "Harbour Bridge South", "latitude": -33.8523, "longitude": 151.2108, "type": "traffic"},
    {"name": "Central Station", "latitude": -33.8830, "longitude": 151.2068, "type": "pedestrian"},
]


def seed_data(session: Session, hours: int = 24):
    if session.query(models.Location).count() > 0:
        return

    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

    for loc in SEED_LOCATIONS:
        location = models.Location(**loc)
        session.add(location)
        session.flush()  # assign id

        for h in range(hours, 0, -1):
            ts = now - timedelta(hours=h)
            # Base patterns: pedestrian peak around 12-18h, traffic morning/afternoon peaks
            hour = ts.hour
            ped_base = 200 + 800 * gaussian_peak(hour, 13, 5)
            traffic_base = 300 + 1200 * (gaussian_peak(hour, 8, 2) + gaussian_peak(hour, 17, 2))
            if location.type == 'traffic':
                ped = int(ped_base * 0.3 + random.uniform(-20, 20))
                traffic = int(traffic_base * 1.0 + random.uniform(-50, 50))
            else:
                ped = int(ped_base * 1.0 + random.uniform(-50, 50))
                traffic = int(traffic_base * 0.5 + random.uniform(-40, 40))
            metric = models.Metric(
                location_id=location.id,
                timestamp=ts,
                pedestrian_count=max(ped, 0),
                traffic_count=max(traffic, 0),
            )
            session.add(metric)
    session.commit()


def gaussian_peak(x: int, mean: float, sigma: float) -> float:
    from math import exp
    return exp(-((x - mean) ** 2) / (2 * sigma ** 2))
