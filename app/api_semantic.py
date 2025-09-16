"""
FastAPI routes for semantic search functionality with optimized query routing.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from . import schemas
from .database import get_db
from .services.semantic_service import (
    insert_metadata_batch,
    semantic_search,
    metadata_filter_search,
    get_vector_status
)
from .services.query_optimizer import query_optimizer
from .services.dual_storage import dual_storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/semantic", tags=["Semantic Search & Optimization"])

# === Legacy Embedding Endpoint (for backward compatibility) ===

@router.post("/embed", response_model=schemas.EmbedResponse)
def embed_metadata_batch_route(request: schemas.EmbedRequest):
    """
    Generate embeddings for a batch of float metadata and insert into vector database only.
    
    NOTE: For new implementations, use /ingest/batch instead as it stores data in both databases.
    
    Args:
        request: EmbedRequest containing list of metadata dictionaries
        
    Returns:
        EmbedResponse with insertion status and counts
    """
    try:
        result = insert_metadata_batch(request.metadatas)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        return schemas.EmbedResponse(**result)
        
    except Exception as e:
        logger.error(f"Embed route error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === Optimized Query Endpoints ===

@router.post("/query/optimized")
async def optimized_query_route(
    request: schemas.OptimizedQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Execute an optimized query using intelligent routing between SQL and Vector databases.
    
    This is the main query endpoint that automatically chooses the best approach based on:
    - Query type (numeric, semantic, mixed)
    - Historical performance
    - Current system load
    
    Args:
        query: Natural language query
        strategy: Query strategy ('sql_first', 'vector_first', 'concurrent', 'adaptive')
        
    Returns:
        Dictionary with optimized query results
        
    Strategies:
    - 'adaptive': Automatically chooses best strategy (recommended)
    - 'sql_first': Try SQL first, fallback to vector if it fails/times out
    - 'vector_first': Use vector search only
    - 'concurrent': Run both SQL and vector queries simultaneously
    """
    try:
        result = await query_optimizer.optimize_query(request.query, db, request.strategy)
        return result
        
    except Exception as e:
        logger.error(f"Optimized query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=schemas.SemanticSearchResponse)
def semantic_search_route(request: schemas.SemanticSearchRequest):
    """
    Perform semantic search on float metadata using vector similarity.
    
    Args:
        request: SemanticSearchRequest with query and top_k
        
    Returns:
        SemanticSearchResponse with ranked results
    """
    try:
        result = semantic_search(request.query, request.top_k)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        # Convert to Pydantic models
        search_results = []
        for res in result["results"]:
            search_results.append(schemas.SemanticSearchResult(**res))
        
        return schemas.SemanticSearchResponse(
            status=result["status"],
            query=result["query"],
            results=search_results,
            total_searched=result["total_searched"]
        )
        
    except Exception as e:
        logger.error(f"Semantic search route error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/filter")
def metadata_filter_search_route(
    where_filter: Dict[str, Any],
    limit: int = 10
):
    """
    Search using metadata filters only (no semantic similarity).
    
    Args:
        where_filter: Metadata filter conditions (e.g., {"region": "Atlantic"})
        limit: Maximum number of results
        
    Returns:
        Dictionary with filtered results
        
    Example request body:
    ```json
    {
        "where_filter": {"region": "North Atlantic", "float_id": "5904471"},
        "limit": 5
    }
    ```
    """
    try:
        result = metadata_filter_search(where_filter, limit)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        return result
        
    except Exception as e:
        logger.error(f"Metadata filter search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === Legacy RAG Endpoint ===

@router.post("/rag_query", response_model=schemas.RAGQueryResponse)
def rag_query_route(request: schemas.RAGQueryRequest):
    """
    Legacy hybrid RAG query endpoint.
    
    NOTE: For optimized queries, use /query/optimized instead.
    
    Args:
        request: RAGQueryRequest with query and top_k
        
    Returns:
        RAGQueryResponse with classified results
    """
    try:
        # Use simplified hybrid query from semantic_service
        from .services.semantic_service import hybrid_rag_query
        result = hybrid_rag_query(request.query, request.top_k)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        # Convert to Pydantic models
        search_results = []
        for res in result["results"]:
            search_results.append(schemas.SemanticSearchResult(**res))
        
        return schemas.RAGQueryResponse(
            status=result["status"],
            query=result["query"],
            query_type=result["query_type"],
            source=result.get("source"),
            results=search_results,
            message=result.get("message")
        )
        
    except Exception as e:
        logger.error(f"RAG query route error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === Status and Monitoring Endpoints ===

@router.get("/status", response_model=schemas.VectorStatusResponse)
def vector_status_route():
    """
    Get status and statistics about the vector database.
    
    Returns:
        VectorStatusResponse with database statistics
    """
    try:
        status = get_vector_status()
        return schemas.VectorStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"Vector status route error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/storage")
def storage_status_route():
    """
    Get comprehensive status of both SQL and Vector storage systems.
    
    Returns:
        Dictionary with storage statistics and sync status
    """
    try:
        return dual_storage.get_storage_stats()
        
    except Exception as e:
        logger.error(f"Storage status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/performance")
def performance_status_route():
    """
    Get query optimization performance statistics.
    
    Returns:
        Dictionary with performance metrics
    """
    try:
        return query_optimizer._get_performance_summary()
        
    except Exception as e:
        logger.error(f"Performance status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/ingestion")
def ingestion_status_route():
    """
    Get data ingestion pipeline statistics.
    
    NOTE: Data ingestion is now managed by external pipeline.
    This endpoint is kept for backward compatibility.
    
    Returns:
        Message indicating external management
    """
    return {
        "status": "external_management",
        "message": "Data ingestion is managed by external pipeline"
    }

# === Maintenance Endpoints ===

@router.post("/maintenance/sync")
async def sync_databases_route(db: Session = Depends(get_db)):
    """
    Synchronize data between SQL and Vector databases.
    
    Returns:
        Dictionary with synchronization results
    """
    try:
        result = await dual_storage.sync_databases(db)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        return result
        
    except Exception as e:
        logger.error(f"Database sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/maintenance/reset_stats")
def reset_performance_stats():
    """
    Reset query optimization performance statistics.
    
    Returns:
        Dictionary confirming reset
    """
    try:
        query_optimizer.reset_stats()
        
        return {"status": "success", "message": "Query performance statistics reset"}
        
    except Exception as e:
        logger.error(f"Stats reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))