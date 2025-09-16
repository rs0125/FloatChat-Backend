# app/schemas.py

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Any, List, Dict

# Schema for incoming natural language queries (unchanged)
class NLQuery(BaseModel):
    text: str

# --- Schemas for Semantic Search ---

# Schema for embedding requests
class EmbedRequest(BaseModel):
    metadatas: List[Dict[str, Any]]

class EmbedResponse(BaseModel):
    status: str
    count: Optional[int] = None
    total_vectors: Optional[int] = None
    message: Optional[str] = None

# Schema for semantic search requests
class SemanticSearchRequest(BaseModel):
    query: str
    top_k: int = 5

class SemanticSearchResult(BaseModel):
    metadata: Dict[str, Any]
    similarity_score: float
    distance: float

class SemanticSearchResponse(BaseModel):
    status: str
    query: Optional[str] = None
    results: List[SemanticSearchResult] = []
    total_searched: Optional[int] = None
    message: Optional[str] = None

# Schema for optimized query requests
class OptimizedQueryRequest(BaseModel):
    query: str
    strategy: str = "adaptive"

# Schema for RAG query requests
class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 5

class RAGQueryResponse(BaseModel):
    status: str
    query: str
    query_type: str  # "numeric", "semantic", or "mixed"
    source: Optional[str] = None  # "sql", "vector", or "hybrid"
    results: List[SemanticSearchResult] = []
    message: Optional[str] = None

# Schema for vector status (updated for ChromaDB)
class VectorStatusResponse(BaseModel):
    total_vectors: int
    collection_info: Optional[Dict[str, Any]] = None
    embedding_model: str
    vector_db_type: str
    error: Optional[str] = None

# Schema for optimized query requests
class OptimizedQueryRequest(BaseModel):
    query: str
    strategy: str = "adaptive"  # 'sql_first', 'vector_first', 'concurrent', 'adaptive'

class OptimizedQueryResponse(BaseModel):
    status: str
    query: str
    query_type: str
    strategy_used: str
    source: Optional[str] = None
    results: List[Dict[str, Any]] = []
    fallback_used: Optional[bool] = None
    total_time: Optional[float] = None
    sql_error: Optional[str] = None
    message: Optional[str] = None
    optimizer_stats: Optional[Dict[str, Any]] = None

# Schema for data ingestion
class DataIngestionRequest(BaseModel):
    data: List[Dict[str, Any]]

class DataIngestionResponse(BaseModel):
    status: str
    total_records: Optional[int] = None
    successful_batches: Optional[int] = None
    failed_batches: Optional[int] = None
    sql_results: Optional[List[Dict[str, Any]]] = None
    vector_results: Optional[List[Dict[str, Any]]] = None
    message: Optional[str] = None
    ingestion_stats: Optional[Dict[str, Any]] = None

# Schema for storage status
class StorageStatusResponse(BaseModel):
    sql_database: Dict[str, Any]
    vector_database: Dict[str, Any]
    sync_status: str

# Schema for metadata filter search
class MetadataFilterRequest(BaseModel):
    where_filter: Dict[str, Any]
    limit: int = 10

class MetadataFilterResponse(BaseModel):
    status: str
    results: List[Dict[str, Any]] = []
    filter: Dict[str, Any]
    count: int

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