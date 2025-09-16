# argo-backend/app/api.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from . import services, schemas
from .database import get_db

router = APIRouter()

@router.get("/floats", response_model=List[schemas.FloatMetadata], tags=["Floats"])
def get_all_floats(db: Session = Depends(get_db)):
    """
    Fetch metadata for all floats to display on the map.
    """
    return services.fetch_all_floats(db)

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