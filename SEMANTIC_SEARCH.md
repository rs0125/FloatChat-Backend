# Semantic Search Extension

This document describes the semantic search functionality added to the ARGO Float Data API.

## Overview

The semantic search extension adds vector database capabilities using FAISS and OpenAI embeddings to enable natural language search over float metadata. This complements the existing SQL-based queries with semantic understanding.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │    │  Semantic        │    │  Vector DB      │
│   Routes        │───▶│  Service         │───▶│  (FAISS)        │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  Embedding       │
                       │  Service         │
                       │  (OpenAI API)    │
                       └──────────────────┘
```

## Components

### 1. Vector Database Service (`services/vector_db.py`)
- FAISS-based vector storage with L2 distance indexing
- Persistent storage to disk using pickle
- Batch insertion and similarity search capabilities

### 2. Embedding Service (`services/embedding_service.py`)
- OpenAI text-embedding-ada-002 integration
- Automatic retry logic with exponential backoff
- Float metadata formatting for optimal embeddings

### 3. Semantic Service (`services/semantic_service.py`)
- High-level orchestration of vector operations
- Query classification (numeric/spatial vs semantic vs mixed)
- Hybrid RAG query routing

## API Endpoints

### POST `/api/semantic/embed`
Generate embeddings for float metadata and store in vector database.

**Request:**
```json
{
  "metadatas": [
    {
      "float_id": "5904471",
      "platform_number": "5904471",
      "region": "North Atlantic", 
      "description": "Deep ocean profiling float",
      "notes": "Climate monitoring deployment",
      "lat": 45.5,
      "lon": -30.2,
      "deploy_date": "2023-01-15"
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "count": 1,
  "total_vectors": 42
}
```

### POST `/api/semantic/search`
Perform semantic search using natural language queries.

**Request:**
```json
{
  "query": "deep ocean floats for climate research",
  "top_k": 5
}
```

**Response:**
```json
{
  "status": "success",
  "query": "deep ocean floats for climate research",
  "results": [
    {
      "metadata": {
        "float_id": "5904471",
        "region": "North Atlantic",
        "description": "Deep ocean profiling float"
      },
      "similarity_score": 0.85,
      "distance": 0.176
    }
  ],
  "total_searched": 42
}
```

### POST `/api/semantic/rag_query`
Hybrid query that intelligently routes between semantic and SQL search.

**Query Classification:**
- **Numeric/Spatial:** Coordinates, measurements, ranges → SQL database
- **Semantic:** Descriptions, research purposes → Vector database  
- **Mixed:** Combines both approaches

**Request:**
```json
{
  "query": "floats measuring temperature above 20°C in research programs",
  "top_k": 10
}
```

**Response:**
```json
{
  "status": "success",
  "query": "floats measuring temperature above 20°C in research programs",
  "query_type": "mixed",
  "source": "hybrid",
  "results": [...],
  "message": "Query classified as mixed - combined semantic and SQL results"
}
```

### GET `/api/semantic/status`
Get vector database statistics.

**Response:**
```json
{
  "total_vectors": 42,
  "index_dimension": 1536,
  "embedding_model": "text-embedding-ada-002",
  "vector_db_type": "FAISS"
}
```

## Setup and Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### Dependencies
Added to `requirements.txt`:
- `faiss-cpu` - Vector database
- `numpy` - Numerical operations
- `tenacity` - Retry logic

### Testing
Run the test script to verify functionality:
```bash
python test_semantic_api.py
```

## Usage Examples

### 1. Initial Data Loading
```python
import requests

# Load float metadata into vector database
metadata_batch = [
    {
        "float_id": "5904471",
        "region": "North Atlantic",
        "description": "Deep ocean profiling float for climate monitoring"
    }
]

response = requests.post("http://localhost:8000/api/semantic/embed", 
                        json={"metadatas": metadata_batch})
```

### 2. Semantic Search
```python
# Search for floats related to climate research
search_request = {
    "query": "climate monitoring floats in deep ocean",
    "top_k": 5
}

response = requests.post("http://localhost:8000/api/semantic/search",
                        json=search_request)
results = response.json()["results"]
```

### 3. Hybrid RAG Query
```python
# Intelligent query routing
rag_request = {
    "query": "Antarctic floats measuring temperature below 2°C",
    "top_k": 10  
}

response = requests.post("http://localhost:8000/api/semantic/rag_query",
                        json=rag_request)
```

## Integration with Existing System

The semantic search functionality is designed to complement, not replace, the existing SQL-based queries:

1. **Supabase/PostgreSQL** continues to handle structured numeric queries
2. **Vector database** handles semantic/descriptive queries
3. **Hybrid routing** intelligently combines both approaches
4. **Existing API endpoints** remain unchanged

## Performance Considerations

- **Vector Index:** Stored persistently to disk, loaded on startup
- **Batch Operations:** Embedding generation optimized for batches
- **Query Classification:** Lightweight regex-based classification
- **Memory Usage:** FAISS index held in memory for fast search

## Future Enhancements

1. **Advanced Query Classification:** ML-based query intent detection
2. **Result Fusion:** Sophisticated ranking of hybrid results
3. **Incremental Updates:** Real-time vector updates as new floats deploy
4. **Advanced Retrieval:** Dense + sparse retrieval combinations