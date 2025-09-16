"""
Vector database service using ChromaDB for semantic search on ARGO float metadata.
"""
import chromadb
from chromadb.config import Settings
import numpy as np
import os
from typing import List, Tuple, Dict, Any, Optional
import logging
import uuid

logger = logging.getLogger(__name__)

class ChromaVectorDB:
    """ChromaDB-based vector database for storing and searching float metadata embeddings."""
    
    def __init__(self, persist_directory: str = "./chroma_db", collection_name: str = "argo_floats"):
        """
        Initialize ChromaDB vector database.
        
        Args:
            persist_directory: Directory to persist the database
            collection_name: Name of the collection to store embeddings
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection '{collection_name}' with {self.count()} vectors")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "ARGO float metadata embeddings"}
            )
            logger.info(f"Created new collection '{collection_name}'")
    
    def add_vectors(self, embeddings: List[List[float]], metadatas: List[Dict[str, Any]], 
                   documents: List[str] = None) -> List[str]:
        """
        Add vectors and corresponding metadata to the database.
        
        Args:
            embeddings: List of embedding vectors
            metadatas: List of metadata dictionaries for each vector
            documents: Optional list of source documents
            
        Returns:
            List of generated IDs for the added vectors
        """
        try:
            # Generate unique IDs for each vector
            ids = [str(uuid.uuid4()) for _ in range(len(embeddings))]
            
            # Prepare documents if not provided
            if documents is None:
                documents = [self._format_metadata_as_document(meta) for meta in metadatas]
            
            # Add to ChromaDB collection
            self.collection.add(
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents,
                ids=ids
            )
            
            logger.info(f"Added {len(ids)} vectors to collection. Total vectors: {self.count()}")
            return ids
            
        except Exception as e:
            logger.error(f"Failed to add vectors: {e}")
            raise
    
    def search(self, query_embedding: List[float], top_k: int = 5, 
               where: Dict[str, Any] = None) -> List[Tuple[float, Dict[str, Any], str]]:
        """
        Search for similar vectors in the database.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of top results to return
            where: Optional metadata filter
            
        Returns:
            List of tuples (distance, metadata, document) for top-k results
        """
        try:
            if self.count() == 0:
                return []
            
            # Perform similarity search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, self.count()),
                where=where,
                include=['metadatas', 'documents', 'distances']
            )
            
            # Format results
            formatted_results = []
            if results['distances'] and results['metadatas'] and results['documents']:
                for distance, metadata, document in zip(
                    results['distances'][0], 
                    results['metadatas'][0], 
                    results['documents'][0]
                ):
                    formatted_results.append((distance, metadata, document))
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def search_by_metadata(self, where: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search by metadata filters only.
        
        Args:
            where: Metadata filter conditions
            limit: Maximum number of results
            
        Returns:
            List of metadata dictionaries
        """
        try:
            results = self.collection.get(
                where=where,
                limit=limit,
                include=['metadatas']
            )
            
            return results['metadatas'] if results['metadatas'] else []
            
        except Exception as e:
            logger.error(f"Metadata search failed: {e}")
            return []
    
    def count(self) -> int:
        """Return number of vectors in the database."""
        try:
            return self.collection.count()
        except:
            return 0
    
    def clear(self) -> None:
        """Clear all vectors and metadata from the database."""
        try:
            # Delete and recreate collection
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "ARGO float metadata embeddings"}
            )
            logger.info("Vector database cleared")
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        try:
            return {
                "name": self.collection_name,
                "count": self.count(),
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {}
    
    def _format_metadata_as_document(self, metadata: Dict[str, Any]) -> str:
        """Format metadata dictionary as a document string."""
        parts = []
        for key, value in metadata.items():
            if value is not None:
                parts.append(f"{key}: {value}")
        return " | ".join(parts)


# Global ChromaDB instance
chroma_db = ChromaVectorDB()