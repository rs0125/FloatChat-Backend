"""
Semantic search service that combines vector database and embedding operations.
Updated to use ChromaDB and optimized query routing.
"""
import numpy as np
from typing import List, Dict, Any, Tuple
import logging
import re

from .vector_db import chroma_db
from .embedding_service import get_embeddings, embed_float_metadata_batch

logger = logging.getLogger(__name__)

def insert_metadata_batch(metadatas: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Insert a batch of float metadata into the vector database.
    
    Args:
        metadatas: List of metadata dictionaries
        
    Returns:
        Dictionary with insertion status and count
    """
    try:
        # Generate embeddings for the metadata batch
        embeddings = embed_float_metadata_batch(metadatas)
        
        # Insert into ChromaDB
        ids = chroma_db.add_vectors(embeddings, metadatas)
        
        logger.info(f"Successfully inserted {len(metadatas)} metadata entries")
        return {
            "status": "success", 
            "count": len(metadatas),
            "total_vectors": chroma_db.count(),
            "generated_ids": ids
        }
        
    except Exception as e:
        logger.error(f"Failed to insert metadata batch: {e}")
        return {"status": "error", "message": str(e)}

def semantic_search(query: str, top_k: int = 5, metadata_filter: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Perform semantic search on float metadata.
    
    Args:
        query: Natural language search query
        top_k: Number of top results to return
        metadata_filter: Optional metadata filter for ChromaDB
        
    Returns:
        Dictionary with search results
    """
    try:
        # Generate embedding for the query
        query_embeddings = get_embeddings([query])
        if not query_embeddings:
            return {"status": "error", "message": "Failed to generate query embedding"}
        
        # Search in ChromaDB
        results = chroma_db.search(
            query_embedding=query_embeddings[0], 
            top_k=top_k,
            where=metadata_filter
        )
        
        # Format results
        formatted_results = []
        for distance, metadata, document in results:
            result = {
                "metadata": metadata,
                "document": document,
                "similarity_score": float(1 / (1 + distance)),  # Convert distance to similarity
                "distance": distance
            }
            formatted_results.append(result)
        
        logger.info(f"Semantic search returned {len(formatted_results)} results for query: '{query}'")
        return {
            "status": "success",
            "query": query,
            "results": formatted_results,
            "total_searched": chroma_db.count()
        }
        
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        return {"status": "error", "message": str(e)}

def metadata_filter_search(where_filter: Dict[str, Any], limit: int = 10) -> Dict[str, Any]:
    """
    Search using metadata filters only (no semantic similarity).
    
    Args:
        where_filter: Metadata filter conditions
        limit: Maximum number of results
        
    Returns:
        Dictionary with filtered results
    """
    try:
        results = chroma_db.search_by_metadata(where_filter, limit)
        
        return {
            "status": "success",
            "results": results,
            "filter": where_filter,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Metadata filter search failed: {e}")
        return {"status": "error", "message": str(e)}

def classify_query_type(query: str) -> str:
    """
    Classify a query as numeric/spatial, semantic, or mixed.
    
    Args:
        query: User query text
        
    Returns:
        One of: "numeric", "semantic", "mixed"
    """
    query_lower = query.lower()
    
    # Numeric/spatial indicators
    numeric_patterns = [
        r'\b\d+\.?\d*\s*(degrees?|°)\b',  # Coordinates
        r'\b(latitude|longitude|lat|lon|depth|temperature|temp|salinity|pressure)\b',
        r'\b(greater|less|more|higher|lower|above|below|between|range)\s+than\b',
        r'\b\d+\.?\d*\s*(m|meters?|km|kilometers?|°c|celsius|psu)\b',
        r'\b(north|south|east|west|equator|arctic|antarctic)\b',
        r'\b(recent|last|latest|current|today|yesterday|month|year)\b'
    ]
    
    # Semantic indicators
    semantic_patterns = [
        r'\b(describe|description|about|characteristics|features|type|kind)\b',
        r'\b(similar|like|related|comparable)\b',
        r'\b(research|study|experiment|project|program)\b',
        r'\b(mission|deployment|purpose|objective)\b'
    ]
    
    numeric_matches = sum(1 for pattern in numeric_patterns if re.search(pattern, query_lower))
    semantic_matches = sum(1 for pattern in semantic_patterns if re.search(pattern, query_lower))
    
    if numeric_matches > 0 and semantic_matches > 0:
        return "mixed"
    elif numeric_matches > 0:
        return "numeric"
    elif semantic_matches > 0:
        return "semantic"
    else:
        # Default to semantic for ambiguous queries
        return "semantic"

def hybrid_rag_query(query: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Perform hybrid RAG query that routes to appropriate search method.
    NOTE: This is a simplified version. Use query_optimizer for advanced routing.
    
    Args:
        query: User query
        top_k: Number of results to return
        
    Returns:
        Dictionary with hybrid search results
    """
    try:
        query_type = classify_query_type(query)
        
        result = {
            "status": "success",
            "query": query,
            "query_type": query_type,
            "results": []
        }
        
        if query_type == "numeric":
            # Route to SQL/Supabase (placeholder - use query_optimizer for full implementation)
            result["message"] = "Query classified as numeric/spatial - use query_optimizer for full SQL integration"
            result["source"] = "sql_placeholder"
            
        elif query_type == "semantic":
            # Route to vector search
            semantic_result = semantic_search(query, top_k)
            if semantic_result["status"] == "success":
                result["results"] = semantic_result["results"]
                result["source"] = "vector"
            else:
                result["status"] = "error"
                result["message"] = semantic_result["message"]
                
        else:  # mixed
            # Combine both approaches
            semantic_result = semantic_search(query, top_k // 2)
            if semantic_result["status"] == "success":
                result["results"].extend(semantic_result["results"])
            
            result["message"] = "Query classified as mixed - use query_optimizer for full hybrid implementation"
            result["source"] = "hybrid_placeholder"
        
        return result
        
    except Exception as e:
        logger.error(f"Hybrid RAG query failed: {e}")
        return {"status": "error", "message": str(e)}

def get_vector_status() -> Dict[str, Any]:
    """
    Get status information about the vector database.
    
    Returns:
        Dictionary with vector database statistics
    """
    try:
        collection_info = chroma_db.get_collection_info()
        return {
            "total_vectors": chroma_db.count(),
            "collection_info": collection_info,
            "embedding_model": "text-embedding-ada-002",
            "vector_db_type": "ChromaDB"
        }
    except Exception as e:
        logger.error(f"Failed to get vector status: {e}")
        return {
            "total_vectors": 0,
            "embedding_model": "text-embedding-ada-002", 
            "vector_db_type": "ChromaDB",
            "error": str(e)
        }