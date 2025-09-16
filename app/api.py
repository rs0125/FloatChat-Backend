# app/api.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from . import services, schemas
from .database import get_db

router = APIRouter()

@router.get("/floats", response_model=List[schemas.FloatMetadata], tags=["Floats"])
def get_all_floats(region: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Fetch metadata for all floats. Can be filtered by region.
    Example: /api/floats?region=atlantic
    """
    floats = services.fetch_all_floats(db=db, region=region)
    return floats

@router.get("/float/{float_id}/data", response_model=List[schemas.FloatData], tags=["Floats"])
def get_float_data(float_id: int, db: Session = Depends(get_db)):
    """
    Fetch time-series data for a single, selected float.
    """
    data = services.fetch_float_timeseries(db, float_id)
    if not data:
        raise HTTPException(status_code=404, detail="Float data not found")
    return data

@router.post("/query", tags=["Query"])
def query_floats(query: schemas.NLQuery):
    """
    Send a natural language query to the LangChain service.
    """
    return services.handle_natural_language_query(query.text)