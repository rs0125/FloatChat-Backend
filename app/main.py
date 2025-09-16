# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # <-- 1. IMPORT THIS
from . import api, api_semantic

app = FastAPI(
    title="ARGO Float Data API",
    description="API for querying and visualizing ARGO float data via structured endpoints and natural language.",
    version="1.0.0"
)

# --- 2. ADD THIS MIDDLEWARE BLOCK ---

# Define the list of "origins" (websites) that are allowed to make requests.
# For a hackathon and local development, using "*" allows everyone.
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods (GET, POST, etc.)
    allow_headers=["*"], # Allow all headers
)

# ------------------------------------

# Include the routes defined in api.py
app.include_router(api.router, prefix="/api")
# Include semantic search routes
app.include_router(api_semantic.router)

@app.get("/")
def read_root():
    return {"message": "Welcome! Go to /docs for the API documentation."}