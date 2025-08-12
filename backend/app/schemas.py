from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel

class LocationBase(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    type: str

    class Config:
        from_attributes = True

class LocationWithIntensity(LocationBase):
    intensity: float

class MetricPoint(BaseModel):
    timestamp: datetime
    pedestrian_count: int
    traffic_count: int

    class Config:
        from_attributes = True

class LocationDetail(LocationBase):
    metrics: list[MetricPoint]
