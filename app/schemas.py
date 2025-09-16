# argo-backend/app/schemas.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Schema for incoming natural language queries
class NLQuery(BaseModel):
    text: str

# --- Schemas for API Responses ---

class FloatMetadata(BaseModel):
    id: int
    lat: float
    lon: float
    last_updated: Optional[datetime] = None

    class Config:
        orm_mode = True # Helps Pydantic work with SQLAlchemy objects

class FloatData(BaseModel):
    timestamp: datetime
    temperature: Optional[float] = None
    salinity: Optional[float] = None

    class Config:
        orm_mode = True