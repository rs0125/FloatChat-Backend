# app/models.py

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base

# (The Measurement class stays the same)
class Measurement(Base):
    __tablename__ = "measurements"
    id = Column(Integer, primary_key=True, index=True)
    float_id = Column(Integer, ForeignKey("floats.id"))
    timestamp = Column("timestamp", DateTime(timezone=True))
    depth = Column(Float)
    temperature = Column(Float)
    salinity = Column(Float)
    float = relationship("Float", back_populates="measurements")

class Float(Base):
    __tablename__ = "floats"

    id = Column(Integer, primary_key=True, index=True)
    wmo_id = Column(Integer, unique=True)
    region = Column(Text)
    launch_date = Column(DateTime(timezone=True))
    
    # --- ADD THESE TWO LINES ---
    lat = Column(Float)
    lon = Column(Float)

    measurements = relationship("Measurement", back_populates="float", cascade="all, delete-orphan")