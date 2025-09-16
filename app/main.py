# argo-backend/app/main.py

from fastapi import FastAPI
from . import api

app = FastAPI(
    title="ARGO Float Data API",
    description="API for querying and visualizing ARGO float data via structured endpoints and natural language.",
    version="1.0.0"
)

# Include the routes defined in api.py
app.include_router(api.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome! Go to /docs for the API documentation."}