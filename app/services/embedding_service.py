"""
OpenAI embedding service for generating vector embeddings from text.
"""
import os
from openai import OpenAI
from typing import List, Dict, Any
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Configure OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY environment variable not set")

# Initialize OpenAI client with new API
client = OpenAI(api_key=OPENAI_API_KEY)

# Embedding model configuration
EMBEDDING_MODEL = "text-embedding-ada-002"
EMBEDDING_DIMENSION = 1536

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts using OpenAI's embedding API.
    
    Args:
        texts: List of strings to embed
        
    Returns:
        List of embedding vectors (each is a list of floats)
        
    Raises:
        Exception: If API call fails after retries
    """
    if not texts:
        return []
    
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key not configured")
    
    try:
        response = client.embeddings.create(
            input=texts,
            model=EMBEDDING_MODEL
        )
        
        embeddings = [item.embedding for item in response.data]
        logger.info(f"Generated embeddings for {len(texts)} texts")
        return embeddings
        
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        raise

def format_float_metadata_for_embedding(metadata: Dict[str, Any]) -> str:
    """
    Format float metadata into a text string suitable for embedding.
    
    Args:
        metadata: Dictionary containing float metadata
        
    Returns:
        Formatted text string
    """
    # Extract key fields for embedding
    float_id = metadata.get('float_id', '')
    platform_number = metadata.get('platform_number', '')
    region = metadata.get('region', '')
    notes = metadata.get('notes', '')
    description = metadata.get('description', '')
    
    # Combine into descriptive text
    text_parts = []
    
    if float_id:
        text_parts.append(f"Float ID: {float_id}")
    if platform_number:
        text_parts.append(f"Platform: {platform_number}")
    if region:
        text_parts.append(f"Region: {region}")
    if description:
        text_parts.append(f"Description: {description}")
    if notes:
        text_parts.append(f"Notes: {notes}")
    
    # Add location information if available
    lat = metadata.get('lat')
    lon = metadata.get('lon')
    if lat is not None and lon is not None:
        text_parts.append(f"Location: {lat:.2f}°N, {lon:.2f}°E")
    
    # Add deployment date if available
    deploy_date = metadata.get('deploy_date')
    if deploy_date:
        text_parts.append(f"Deployed: {deploy_date}")
    
    return " ".join(text_parts)

def embed_float_metadata_batch(metadata_list: List[Dict[str, Any]]) -> List[List[float]]:
    """
    Generate embeddings for a batch of float metadata.
    
    Args:
        metadata_list: List of metadata dictionaries
        
    Returns:
        List of embedding vectors
    """
    # Format metadata into text strings
    texts = [format_float_metadata_for_embedding(metadata) for metadata in metadata_list]
    
    # Generate embeddings
    embeddings = get_embeddings(texts)
    
    return embeddings