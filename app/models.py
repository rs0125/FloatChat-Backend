# app/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from .database import Base

# Renamed from Measurement to Profile to match the new schema
class Profile(Base):
    __tablename__ = "profiles"

    profile_id = Column(Text, primary_key=True, index=True)
    float_id = Column(Text, ForeignKey("floats.float_id"))
    profile_time = Column(DateTime(timezone=True))
    lat = Column(Float)
    lon = Column(Float)
    pressure = Column(Float)
    depth = Column(Float)
    variable_name = Column(Text)
    variable_value = Column(Float)
    level = Column(Integer)
    raw_profile = Column(JSONB)
    
    float = relationship("Float", back_populates="profiles")

class Float(Base):
    __tablename__ = "floats"

    float_id = Column(Text, primary_key=True, index=True)
    platform_number = Column(Text)
    deploy_date = Column(DateTime(timezone=True))
    properties = Column(JSONB)

    profiles = relationship("Profile", back_populates="float", cascade="all, delete-orphan")