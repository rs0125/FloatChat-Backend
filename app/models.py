# argo-backend/app/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime
from .database import Base

class Float(Base):
    __tablename__ = "floats"

    id = Column(Integer, primary_key=True, index=True)
    # TODO: Add more columns for float metadata
    # e.g., last_latitude = Column(Float), last_longitude = Column(Float), etc.

class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True, index=True)
    # TODO: Add columns for time-series data
    # e.g., float_id = Column(Integer, ForeignKey("floats.id")), temperature = Column(Float), etc.