# app/api.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from . import services, schemas
from .database import get_db

router = APIRouter()

@router.get("/floats", response_model=List[schemas.FloatMetadata], tags=["Floats"])
def get_all_floats(db: Session = Depends(get_db)):
    """
    Fetch all floats and their latest known position for the map.
    """
    # <-- CHANGED: No longer takes a 'region' parameter.
    floats = services.fetch_all_floats(db=db)
    return floats

@router.get("/float/{float_id}/profiles", response_model=List[schemas.ProfileData], tags=["Floats"])
# <-- CHANGED: Path is now /profiles, float_id is a string, and accepts an optional 'variable' filter.
def get_float_profiles(float_id: str, variable: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Fetch time-series profile data for a single float.
    Can be filtered by variable_name (e.g., 'TEMP' or 'PSAL').
    Example: /api/float/some_id/profiles?variable=TEMP
    """
    # <-- CHANGED: Calls the new service function.
    profiles = services.fetch_float_profiles(db, float_id=float_id, variable=variable)
    if not profiles:
        raise HTTPException(status_code=404, detail="Profile data not found for this float")
    return profiles

@router.post("/query", tags=["Query"])
def query_floats(query: schemas.NLQuery):
    """
    Send a natural language query to the LangChain service. (Unchanged)
    """
    return services.handle_natural_language_query(query.text)