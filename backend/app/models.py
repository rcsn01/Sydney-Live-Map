from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="pedestrian")

    metrics: Mapped[list['Metric']] = relationship(back_populates="location", cascade="all, delete-orphan")

class Metric(Base):
    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey('locations.id', ondelete='CASCADE'), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    # Single unified count field (previously pedestrian_count + traffic_count)
    count: Mapped[int] = mapped_column(Integer, nullable=False)

    location: Mapped[Location] = relationship(back_populates="metrics")
