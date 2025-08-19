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
    {"name": "Town Hall", "latitude": -33.8732, "longitude": 151.2066, "type": "pedestrian"},
    {"name": "Circular Quay", "latitude": -33.8610, "longitude": 151.2108, "type": "pedestrian"},
    {"name": "Darling Harbour", "latitude": -33.8728, "longitude": 151.1992, "type": "pedestrian"},
    {"name": "Ultimo Harris St", "latitude": -33.8792, "longitude": 151.1975, "type": "pedestrian"},
    {"name": "Anzac Bridge East", "latitude": -33.8695, "longitude": 151.1885, "type": "traffic"},
    # Added extra named CBD & inner suburb sites
    {"name": "Barangaroo", "latitude": -33.8616, "longitude": 151.2019, "type": "pedestrian"},
    {"name": "Wynyard Station", "latitude": -33.8650, "longitude": 151.2065, "type": "pedestrian"},
    {"name": "Hyde Park North", "latitude": -33.8690, "longitude": 151.2127, "type": "pedestrian"},
    {"name": "Hyde Park South", "latitude": -33.8745, "longitude": 151.2114, "type": "pedestrian"},
    {"name": "Oxford St & Crown St", "latitude": -33.8794, "longitude": 151.2152, "type": "pedestrian"},
    {"name": "Surry Hills Crown & Cleveland", "latitude": -33.8870, "longitude": 151.2104, "type": "pedestrian"},
    {"name": "Broadway & Harris St", "latitude": -33.8823, "longitude": 151.1979, "type": "traffic"},
    {"name": "Kings Cross Station", "latitude": -33.8740, "longitude": 151.2253, "type": "pedestrian"},
    {"name": "Glebe Point Rd & St Johns Rd", "latitude": -33.8799, "longitude": 151.1826, "type": "pedestrian"},
    {"name": "Redfern Station", "latitude": -33.8923, "longitude": 151.2048, "type": "pedestrian"},
    {"name": "Parramatta Rd & City Rd", "latitude": -33.8887, "longitude": 151.1895, "type": "traffic"},
    {"name": "Eastern Distributor Entry", "latitude": -33.8711, "longitude": 151.2205, "type": "traffic"},
    {"name": "Western Distributor Ramp", "latitude": -33.8679, "longitude": 151.1946, "type": "traffic"},
    # Additional expansion set
    {"name": "Sydney Opera House", "latitude": -33.8568, "longitude": 151.2153, "type": "pedestrian"},
    {"name": "Royal Botanic Gardens Gate", "latitude": -33.8643, "longitude": 151.2165, "type": "pedestrian"},
    {"name": "The Rocks Argyle St", "latitude": -33.8582, "longitude": 151.2077, "type": "pedestrian"},
    {"name": "Observatory Hill", "latitude": -33.8596, "longitude": 151.2036, "type": "pedestrian"},
    {"name": "Pyrmont Bridge East", "latitude": -33.8690, "longitude": 151.1987, "type": "pedestrian"},
    {"name": "Pyrmont Bridge West", "latitude": -33.8691, "longitude": 151.1962, "type": "pedestrian"},
    {"name": "Fish Market", "latitude": -33.8680, "longitude": 151.1874, "type": "pedestrian"},
    {"name": "Walsh Bay", "latitude": -33.8557, "longitude": 151.2076, "type": "pedestrian"},
    {"name": "Powerhouse Museum", "latitude": -33.8784, "longitude": 151.1980, "type": "pedestrian"},
    {"name": "QVB", "latitude": -33.8715, "longitude": 151.2068, "type": "pedestrian"},
    {"name": "Museum Station", "latitude": -33.8731, "longitude": 151.2088, "type": "pedestrian"},
    {"name": "St James Station", "latitude": -33.8696, "longitude": 151.2111, "type": "pedestrian"},
    {"name": "Haymarket Light Rail", "latitude": -33.8807, "longitude": 151.2058, "type": "pedestrian"},
    {"name": "UTS Tower", "latitude": -33.8830, "longitude": 151.1997, "type": "pedestrian"},
    {"name": "USYD Gate City Rd", "latitude": -33.8883, "longitude": 151.1891, "type": "pedestrian"},
    {"name": "Chippendale Central Park", "latitude": -33.8849, "longitude": 151.2007, "type": "pedestrian"},
    {"name": "Moore Park", "latitude": -33.8924, "longitude": 151.2240, "type": "pedestrian"},
    {"name": "SCG", "latitude": -33.8910, "longitude": 151.2248, "type": "pedestrian"},
    {"name": "Star Casino", "latitude": -33.8680, "longitude": 151.1950, "type": "pedestrian"},
    {"name": "Walsh Bay Wharf 4/5", "latitude": -33.8551, "longitude": 151.2071, "type": "pedestrian"},
    {"name": "Cahill Expressway South", "latitude": -33.8607, "longitude": 151.2130, "type": "traffic"},
    {"name": "Cross City Tunnel East", "latitude": -33.8722, "longitude": 151.2194, "type": "traffic"},
    {"name": "Cross City Tunnel West", "latitude": -33.8738, "longitude": 151.1978, "type": "traffic"},
    {"name": "Harbour Tunnel South", "latitude": -33.8469, "longitude": 151.2129, "type": "traffic"},
    {"name": "M1 Gore Hill Entry", "latitude": -33.8219, "longitude": 151.1815, "type": "traffic"},
    {"name": "Western Distributor West", "latitude": -33.8700, "longitude": 151.1840, "type": "traffic"},
    {"name": "City West Link", "latitude": -33.8767, "longitude": 151.1599, "type": "traffic"},
    {"name": "Harbour Bridge North", "latitude": -33.8485, "longitude": 151.2107, "type": "traffic"},
    {"name": "Milsons Point Station", "latitude": -33.8467, "longitude": 151.2113, "type": "pedestrian"},
    {"name": "North Sydney Station", "latitude": -33.8390, "longitude": 151.2074, "type": "pedestrian"},
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
