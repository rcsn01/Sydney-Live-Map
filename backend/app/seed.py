from __future__ import annotations
from datetime import datetime, timedelta, timezone
import random
import math
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


def seed_data(session: Session, hours: int = 24 * 7):
    """Seed synthetic data with higher variance across locations & temporal patterns.

    Variation techniques:
      * Per-location deterministic scaling (based on name hash & known hotspots list)
      * Distinct pedestrian vs traffic diurnal curves (+ added shoulder / late-night noise)
      * Weekend modulation (pedestrian leisure boost, traffic commuter drop)
      * Random hourly noise with location-specific volatility
      * Occasional spike events (rare surges) for major hubs
    """
    if session.query(models.Location).count() > 0:
        return

    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

    for loc in SEED_LOCATIONS:
        location = models.Location(**loc)
        session.add(location)
        session.flush()  # assign id

        ped_mult, traffic_mult, volatility = location_scalers(location.name, location.type)

        for h in range(hours, 0, -1):
            ts = now - timedelta(hours=h)
            hour = ts.hour
            weekday = ts.weekday()  # 0=Mon .. 6=Sun

            # Diurnal base curves (0..1)
            ped_curve = (
                0.10
                + 0.55 * gaussian_peak(hour, 13, 3.5)  # lunch
                + 0.40 * gaussian_peak(hour, 18, 3.0)  # after work / evening
                + 0.18 * gaussian_peak(hour, 8, 2.5)   # morning ramp
                + 0.08 * gaussian_peak(hour, 22, 2.0)  # late evening leisure
            )
            traffic_curve = (
                0.12
                + 0.80 * gaussian_peak(hour, 8, 1.8)   # AM peak
                + 0.70 * gaussian_peak(hour, 17, 2.0)  # PM peak
                + 0.20 * gaussian_peak(hour, 12, 3.5)  # mid-day commercial
            )

            # Base absolute scales (these will be modulated):
            base_ped = 120 + 1300 * min(ped_curve, 1.0)
            base_traffic = 200 + 2000 * min(traffic_curve, 1.0)

            # Apply per-location deterministic multipliers
            ped_val = base_ped * ped_mult
            traffic_val = base_traffic * traffic_mult

            # Weekend adjustments: more leisure pedestrians, less commuter traffic
            if weekday >= 5:  # Sat / Sun
                ped_val *= 1.15 if 10 <= hour <= 20 else 0.9
                traffic_val *= 0.7 if 7 <= hour <= 10 or 16 <= hour <= 19 else 0.85

            # Late night quiet hours damping
            if hour < 5:
                ped_val *= 0.4
                traffic_val *= 0.55

            # Location volatility (controlled randomness)
            noise_scale_ped = ped_val * 0.08 * volatility
            noise_scale_traffic = traffic_val * 0.06 * volatility
            ped_val += random.gauss(0, noise_scale_ped)
            traffic_val += random.gauss(0, noise_scale_traffic)

            # Rare surge events for key hubs (simulate event / crowd) ~1% chance per hour
            if is_major_hub(location.name) and random.random() < 0.01:
                surge_factor = random.uniform(1.4, 2.2)
                ped_val *= surge_factor
                # traffic might modestly increase but not as much
                traffic_val *= 1 + (surge_factor - 1) * 0.35

            ped = int(max(ped_val, 0))
            traffic = int(max(traffic_val, 0))

            metric = models.Metric(
                location_id=location.id,
                timestamp=ts,
                pedestrian_count=ped,
                traffic_count=traffic,
            )
            session.add(metric)
    session.commit()


def location_scalers(name: str, loc_type: str) -> tuple[float, float, float]:
    """Return (ped_scale, traffic_scale, volatility) for a location.
    Deterministic via hashing for reproducibility.
    """
    base_hotspots = {
        'Central Station': (1.8, 0.9, 1.2),
        'Town Hall': (1.6, 0.8, 1.15),
        'Wynyard Station': (1.55, 0.85, 1.1),
        'Circular Quay': (1.5, 0.75, 1.05),
        'Sydney Opera House': (1.7, 0.5, 1.25),
        'Harbour Bridge South': (0.7, 1.5, 1.0),
        'Harbour Bridge North': (0.65, 1.45, 0.95),
        'Anzac Bridge East': (0.4, 1.6, 0.9),
        'Western Distributor Ramp': (0.35, 1.55, 0.9),
    }
    if name in base_hotspots:
        return base_hotspots[name]

    # Hash-based pseudo random but stable factors
    h = pseudo_hash(name)
    # Ped scale range differs by type
    if loc_type == 'pedestrian':
        ped_scale = 0.6 + (h % 37) / 37 * 1.0   # 0.6 .. 1.6
        traffic_scale = 0.3 + (h // 37 % 29) / 29 * 0.6  # 0.3 .. 0.9
    else:
        ped_scale = 0.3 + (h % 41) / 41 * 0.6   # 0.3 .. 0.9
        traffic_scale = 0.7 + (h // 41 % 31) / 31 * 1.0  # 0.7 .. 1.7
    volatility = 0.9 + ((h // 100) % 23) / 23 * 0.5  # 0.9 .. 1.4
    return ped_scale, traffic_scale, volatility


def is_major_hub(name: str) -> bool:
    keywords = [
        'Station', 'Opera House', 'Town Hall', 'Central', 'Wynyard', 'Harbour Bridge',
        'Anzac', 'SCG', 'Casino', 'USYD', 'UTS'
    ]
    lowered = name.lower()
    return any(k.lower() in lowered for k in keywords)


def pseudo_hash(s: str) -> int:
    # Simple deterministic hash (avoid importing hashlib for lightweight seeding)
    h = 0
    for ch in s:
        h = (h * 131 + ord(ch)) & 0xFFFFFFFF
    return h


def gaussian_peak(x: int, mean: float, sigma: float) -> float:
    from math import exp
    return exp(-((x - mean) ** 2) / (2 * sigma ** 2))
