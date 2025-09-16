# ARGO Float Data API - Enhanced with Dual Storage & Intelligent Query Optimization

## Overview

This enhanced version of the ARGO Float Data API features a sophisticated dual-storage architecture with intelligent query optimization. The system automatically manages data across both SQL (Supabase) and Vector (ChromaDB) databases, providing optimal performance for different types of queries.

## 🚀 Key Features

### Dual Storage Architecture
- **Simultaneous Storage**: Data is automatically stored in both SQL and Vector databases
- **Consistency Management**: Ensures data synchronization across both systems
- **Automatic Fallback**: Graceful degradation when one system is unavailable

### Intelligent Query Optimization
- **Adaptive Routing**: Automatically chooses the best database based on query type
- **Performance Monitoring**: Tracks response times and success rates
- **Multiple Strategies**: SQL-first, Vector-first, Concurrent, and Adaptive approaches

### Advanced Vector Search
- **ChromaDB Integration**: More robust than FAISS with built-in persistence
- **Metadata Filtering**: Combine semantic and traditional filtering
- **Scalable Architecture**: Handles large datasets efficiently

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Application                       │
├─────────────────────────────────────────────────────────────┤
│                    API Endpoints                           │
│  • /api/semantic/query/optimized (main query endpoint)     │
│  • /api/semantic/ingest/batch (data ingestion)            │
│  • /api/semantic/search (vector search)                   │
│  • /api/semantic/status/* (monitoring)                    │
├─────────────────────────────────────────────────────────────┤
│                  Service Layer                             │
│  ┌─────────────────┐ ┌─────────────────┐ ┌──────────────┐  │
│  │ Query Optimizer │ │ Dual Storage    │ │ Ingestion    │  │
│  │ - Adaptive      │ │ - SQL + Vector  │ │ Pipeline     │  │
│  │ - Performance   │ │ - Sync Management│ │ - Batch      │  │
│  │ - Fallback      │ │ - Consistency   │ │ - Validation │  │
│  └─────────────────┘ └─────────────────┘ └──────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                  Storage Layer                             │
│  ┌─────────────────┐                    ┌─────────────────┐ │
│  │ SQL Database    │                    │ Vector Database │ │
│  │ (Supabase)      │ ←──── Sync ────→   │ (ChromaDB)      │ │
│  │ - Structured    │                    │ - Embeddings    │ │
│  │ - Numeric       │                    │ - Semantic      │ │
│  │ - Spatial       │                    │ - Similarity    │ │
│  └─────────────────┘                    └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL database (Supabase)
- OpenAI API key
- Required packages (see requirements.txt)

## 🛠️ Installation

1. **Clone and Install Dependencies**
```bash
git clone <repository-url>
cd FloatChat-Backend
pip install -r requirements.txt
```

2. **Environment Configuration**
```bash
# Set required environment variables
export OPENAI_API_KEY="your_openai_api_key_here"
export DATABASE_URL="your_supabase_connection_string"
```

3. **Start the Application**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📊 Data Ingestion

### Batch Ingestion (Recommended)
```python
import requests

# Ingest data into both databases simultaneously
data = {
    "data": [
        {
            "float_id": "5904471",
            "platform_number": "5904471",
            "region": "North Atlantic",
            "description": "Deep ocean profiling float",
            "notes": "Climate monitoring research",
            "lat": 45.5,
            "lon": -30.2,
            "deploy_date": "2023-01-15",
            "profiles": [
                {
                    "profile_id": "prof_001",
                    "profile_time": "2023-01-16T10:00:00",
                    "variable_name": "TEMP",
                    "variable_value": 15.5,
                    "depth": 10.0
                }
            ]
        }
    ]
}

response = requests.post(
    "http://localhost:8000/api/semantic/ingest/batch",
    json=data
)
```

### File Ingestion
```python
# Ingest from CSV, JSON, or Parquet files
response = requests.post(
    "http://localhost:8000/api/semantic/ingest/file",
    params={
        "file_path": "/path/to/your/data.csv",
        "file_format": "csv"
    }
)
```

## 🔍 Querying Data

### Optimized Query (Recommended)
```python
# The main query endpoint with intelligent routing
response = requests.post(
    "http://localhost:8000/api/semantic/query/optimized",
    params={
        "query": "deep ocean floats measuring temperature in the Atlantic",
        "strategy": "adaptive"  # or 'sql_first', 'vector_first', 'concurrent'
    }
)
```

### Query Strategies

1. **Adaptive (Default)**: Automatically chooses the best approach
2. **SQL First**: Try SQL query first, fallback to vector search
3. **Vector First**: Use semantic search only
4. **Concurrent**: Run both simultaneously and combine results

### Semantic Search Only
```python
# Vector search with natural language
response = requests.post(
    "http://localhost:8000/api/semantic/search",
    json={
        "query": "climate research floats in polar regions",
        "top_k": 10
    }
)
```

### Metadata Filtering
```python
# Filter by specific metadata
response = requests.post(
    "http://localhost:8000/api/semantic/search/filter",
    json={
        "where_filter": {"region": "North Atlantic", "platform_number": "5904471"},
        "limit": 5
    }
)
```

## 📈 Monitoring & Status

### System Status
```python
# Check vector database status
requests.get("http://localhost:8000/api/semantic/status")

# Check both storage systems
requests.get("http://localhost:8000/api/semantic/status/storage")

# Check query performance
requests.get("http://localhost:8000/api/semantic/status/performance")

# Check ingestion statistics
requests.get("http://localhost:8000/api/semantic/status/ingestion")
```

### Maintenance
```python
# Synchronize databases
requests.post("http://localhost:8000/api/semantic/maintenance/sync")

# Reset performance statistics
requests.post("http://localhost:8000/api/semantic/maintenance/reset_stats")
```

## 🔧 Configuration

### Query Optimizer Settings
```python
# In services/query_optimizer.py
QueryOptimizer(
    sql_timeout=10.0,      # SQL query timeout in seconds
    vector_timeout=5.0     # Vector query timeout in seconds
)
```

### Ingestion Pipeline Settings
```python
# In services/ingestion_pipeline.py
DataIngestionPipeline(
    batch_size=100         # Records per batch
)
```

## 📊 API Endpoints

### Core Endpoints
- `POST /api/semantic/query/optimized` - Main optimized query endpoint
- `POST /api/semantic/ingest/batch` - Batch data ingestion
- `POST /api/semantic/ingest/file` - File-based ingestion

### Search Endpoints
- `POST /api/semantic/search` - Semantic vector search
- `POST /api/semantic/search/filter` - Metadata filtering
- `POST /api/semantic/embed` - Legacy embedding endpoint

### Status Endpoints
- `GET /api/semantic/status` - Vector database status
- `GET /api/semantic/status/storage` - Dual storage status
- `GET /api/semantic/status/performance` - Query performance metrics
- `GET /api/semantic/status/ingestion` - Ingestion statistics

### Maintenance Endpoints
- `POST /api/semantic/maintenance/sync` - Synchronize databases
- `POST /api/semantic/maintenance/reset_stats` - Reset statistics

## 🎯 Query Classification

The system automatically classifies queries into three types:

### Numeric/Spatial Queries
- Coordinates, measurements, ranges
- Example: "floats with temperature above 20°C"
- Routed to: SQL database

### Semantic Queries
- Descriptions, research purposes
- Example: "climate research floats"
- Routed to: Vector database

### Mixed Queries
- Combination of both
- Example: "Antarctic research floats measuring salinity"
- Routed to: Both databases (concurrent or sequential)

## 🚀 Performance Features

### Automatic Optimization
- Learns from query patterns
- Adapts to system performance
- Intelligent caching strategies

### Concurrent Processing
- Parallel SQL and vector queries
- Result merging and ranking
- Timeout management

### Error Recovery
- Graceful fallback mechanisms
- Automatic retry logic
- System health monitoring

## 🔒 Best Practices

1. **Use Batch Ingestion**: Always use `/ingest/batch` for new data
2. **Prefer Optimized Queries**: Use `/query/optimized` as your main endpoint
3. **Monitor Performance**: Check status endpoints regularly
4. **Sync Databases**: Run sync operations during maintenance windows
5. **Set Appropriate Timeouts**: Configure based on your data size

## 🐛 Troubleshooting

### Common Issues

1. **Slow Queries**: Check performance status and adjust timeouts
2. **Sync Issues**: Run manual sync and check logs
3. **Memory Issues**: Reduce batch sizes in ingestion pipeline
4. **OpenAI Rate Limits**: Implement exponential backoff

### Logs and Debugging
```python
import logging
logging.basicConfig(level=logging.INFO)
# Check application logs for detailed error information
```

## 🔮 Future Enhancements

- Real-time data streaming
- Advanced caching layers
- Multi-tenant support
- GraphQL interface
- Distributed vector storage

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.