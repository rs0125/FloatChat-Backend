# app/schemas.py

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Any

# Schema for incoming natural language queries (unchanged)
class NLQuery(BaseModel):
    text: str

# --- Schemas for API Responses ---

# Represents a float and its LATEST known position for the map
class FloatMetadata(BaseModel):
    float_id: str
    platform_number: Optional[str] = None
    lat: Optional[float] = None # Will be populated from the latest profile
    lon: Optional[float] = None # Will be populated from the latest profile
    
    # Updated for Pydantic V2
    model_config = ConfigDict(from_attributes=True)

# Represents a single data point from a profile
class ProfileData(BaseModel):
    profile_id: str
    profile_time: datetime
    variable_name: str
    variable_value: float
    depth: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)