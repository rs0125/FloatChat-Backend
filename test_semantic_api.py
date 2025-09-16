"""
Example usage script for the semantic search API.
Run this after starting the FastAPI server to test the semantic search functionality.
"""
import requests
import json

# API base URL (adjust if needed)
BASE_URL = "http://localhost:8000/api/semantic"

def test_embed_metadata():
    """Test embedding metadata into vector database."""
    print("\n=== Testing Embed Metadata ===")
    
    sample_metadata = {
        "metadatas": [
            {
                "float_id": "5904471",
                "platform_number": "5904471",
                "region": "North Atlantic",
                "description": "Deep ocean profiling float for climate monitoring",
                "notes": "Deployed as part of global ocean observation network",
                "lat": 45.5,
                "lon": -30.2,
                "deploy_date": "2023-01-15"
            },
            {
                "float_id": "5904472",
                "platform_number": "5904472", 
                "region": "Pacific Ocean",
                "description": "Temperature and salinity profiling float",
                "notes": "Research project on ocean circulation patterns",
                "lat": 35.0,
                "lon": -140.0,
                "deploy_date": "2023-02-10"
            },
            {
                "float_id": "5904473",
                "platform_number": "5904473",
                "region": "Antarctic Ocean",
                "description": "Deep water mass tracking float",
                "notes": "Antarctic Bottom Water formation study",
                "lat": -65.0,
                "lon": 0.0,
                "deploy_date": "2023-03-05"
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/embed", json=sample_metadata)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

def test_semantic_search():
    """Test semantic search functionality."""
    print("\n=== Testing Semantic Search ===")
    
    queries = [
        "deep ocean floats for climate research",
        "Antarctic water mass studies", 
        "Pacific Ocean temperature monitoring",
        "ocean circulation research projects"
    ]
    
    for query in queries:
        print(f"\nQuery: '{query}'")
        
        search_request = {
            "query": query,
            "top_k": 3
        }
        
        try:
            response = requests.post(f"{BASE_URL}/search", json=search_request)
            print(f"Status: {response.status_code}")
            result = response.json()
            
            if result.get("status") == "success":
                print(f"Found {len(result['results'])} results:")
                for i, res in enumerate(result['results'], 1):
                    metadata = res['metadata']
                    score = res['similarity_score']
                    print(f"  {i}. Float {metadata.get('float_id')} (Score: {score:.3f})")
                    print(f"     Region: {metadata.get('region')}")
                    print(f"     Description: {metadata.get('description')}")
            else:
                print(f"Error: {result.get('message')}")
                
        except Exception as e:
            print(f"Error: {e}")

def test_rag_query():
    """Test hybrid RAG query functionality."""
    print("\n=== Testing RAG Query ===")
    
    queries = [
        "deep ocean floats for climate research",  # Should be semantic
        "floats with temperature above 20 degrees",  # Should be numeric
        "Antarctic research floats measuring salinity"  # Should be mixed
    ]
    
    for query in queries:
        print(f"\nQuery: '{query}'")
        
        rag_request = {
            "query": query,
            "top_k": 3
        }
        
        try:
            response = requests.post(f"{BASE_URL}/rag_query", json=rag_request)
            print(f"Status: {response.status_code}")
            result = response.json()
            
            if result.get("status") == "success":
                print(f"Query Type: {result.get('query_type')}")
                print(f"Source: {result.get('source')}")
                if result.get('message'):
                    print(f"Message: {result.get('message')}")
                print(f"Results: {len(result.get('results', []))}")
            else:
                print(f"Error: {result.get('message')}")
                
        except Exception as e:
            print(f"Error: {e}")

def test_vector_status():
    """Test vector database status."""
    print("\n=== Testing Vector Status ===")
    
    try:
        response = requests.get(f"{BASE_URL}/status")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Semantic Search API Test Script")
    print("Make sure your FastAPI server is running on localhost:8000")
    print("And that OPENAI_API_KEY environment variable is set")
    
    # Test vector status first
    test_vector_status()
    
    # Test embedding (this adds test data)
    test_embed_metadata()
    
    # Test semantic search
    test_semantic_search()
    
    # Test RAG query
    test_rag_query()
    
    # Check final status
    test_vector_status()