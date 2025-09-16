"""
Dual storage service that manages data in both Supabase (SQL) and ChromaDB (Vector) simultaneously.
This service ensures data consistency across both storage systems.
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from ..database import get_db
from .. import models, services
from .vector_db import chroma_db
from .embedding_service import embed_float_metadata_batch

logger = logging.getLogger(__name__)

class DualStorageService:
    """Service for managing data across both SQL and Vector databases."""
    
    def __init__(self):
        self.vector_db = chroma_db
        
    async def ingest_float_data(self, float_data_batch: List[Dict[str, Any]], 
                               db: Session) -> Dict[str, Any]:
        """
        Ingest ARGO float data into both Supabase and ChromaDB simultaneously.
        
        Args:
            float_data_batch: List of float data dictionaries
            db: SQLAlchemy database session
            
        Returns:
            Dictionary with ingestion results
        """
        try:
            sql_results = []
            vector_results = []
            
            # Step 1: Prepare data for both databases
            float_metadata = []
            profile_data = []
            
            for float_item in float_data_batch:
                # Extract float metadata
                float_meta = {
                    "float_id": float_item.get("float_id"),
                    "platform_number": float_item.get("platform_number"),
                    "deploy_date": float_item.get("deploy_date"),
                    "region": float_item.get("region", ""),
                    "description": float_item.get("description", ""),
                    "notes": float_item.get("notes", ""),
                    "lat": float_item.get("lat"),
                    "lon": float_item.get("lon"),
                    "properties": float_item.get("properties", {})
                }
                float_metadata.append(float_meta)
                
                # Extract profile data if available
                if "profiles" in float_item:
                    for profile in float_item["profiles"]:
                        profile_data.append({
                            "float_id": float_item.get("float_id"),
                            "profile_id": profile.get("profile_id"),
                            "profile_time": profile.get("profile_time"),
                            "lat": profile.get("lat"),
                            "lon": profile.get("lon"),
                            "variable_name": profile.get("variable_name"),
                            "variable_value": profile.get("variable_value"),
                            "depth": profile.get("depth")
                        })
            
            # Step 2: Store in SQL database (Supabase)
            sql_success = await self._store_in_sql(float_metadata, profile_data, db)
            sql_results.append({"status": "success" if sql_success else "error", 
                              "count": len(float_metadata)})
            
            # Step 3: Store in Vector database (ChromaDB) 
            vector_success = await self._store_in_vector(float_metadata)
            vector_results.append({"status": "success" if vector_success else "error",
                                 "count": len(float_metadata)})
            
            return {
                "status": "success" if sql_success and vector_success else "partial",
                "sql_results": sql_results,
                "vector_results": vector_results,
                "total_floats": len(float_metadata),
                "total_profiles": len(profile_data)
            }
            
        except Exception as e:
            logger.error(f"Dual storage ingestion failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _store_in_sql(self, float_metadata: List[Dict[str, Any]], 
                           profile_data: List[Dict[str, Any]], db: Session) -> bool:
        """Store data in SQL database."""
        try:
            # Store float metadata
            for meta in float_metadata:
                # Check if float already exists
                existing_float = db.query(models.Float).filter(
                    models.Float.float_id == meta["float_id"]
                ).first()
                
                if not existing_float:
                    float_obj = models.Float(
                        float_id=meta["float_id"],
                        platform_number=meta["platform_number"],
                        deploy_date=meta.get("deploy_date"),
                        properties=meta.get("properties", {})
                    )
                    db.add(float_obj)
            
            # Store profile data
            for profile in profile_data:
                # Check if profile already exists
                existing_profile = db.query(models.Profile).filter(
                    models.Profile.profile_id == profile["profile_id"]
                ).first()
                
                if not existing_profile:
                    profile_obj = models.Profile(
                        profile_id=profile["profile_id"],
                        float_id=profile["float_id"],
                        profile_time=profile.get("profile_time"),
                        lat=profile.get("lat"),
                        lon=profile.get("lon"),
                        variable_name=profile.get("variable_name"),
                        variable_value=profile.get("variable_value"),
                        depth=profile.get("depth")
                    )
                    db.add(profile_obj)
            
            db.commit()
            logger.info(f"Successfully stored {len(float_metadata)} floats and {len(profile_data)} profiles in SQL")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"SQL storage failed: {e}")
            return False
    
    async def _store_in_vector(self, float_metadata: List[Dict[str, Any]]) -> bool:
        """Store data in vector database."""
        try:
            # Generate embeddings
            embeddings = embed_float_metadata_batch(float_metadata)
            
            # Store in ChromaDB
            ids = self.vector_db.add_vectors(embeddings, float_metadata)
            
            logger.info(f"Successfully stored {len(ids)} vectors in ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"Vector storage failed: {e}")
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get statistics from both storage systems."""
        try:
            # Get database session
            db = next(get_db())
            
            # SQL stats
            sql_stats = {
                "floats_count": db.query(models.Float).count(),
                "profiles_count": db.query(models.Profile).count()
            }
            
            # Vector stats
            vector_stats = self.vector_db.get_collection_info()
            
            return {
                "sql_database": sql_stats,
                "vector_database": vector_stats,
                "sync_status": "healthy" if sql_stats["floats_count"] == vector_stats["count"] else "out_of_sync"
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {"error": str(e)}
    
    async def sync_databases(self, db: Session) -> Dict[str, Any]:
        """Synchronize data between SQL and Vector databases."""
        try:
            # Get all floats from SQL that might not be in vector DB
            sql_floats = db.query(models.Float).all()
            
            # Check which floats are missing in vector DB
            missing_in_vector = []
            
            for float_obj in sql_floats:
                # Try to find in vector DB by metadata filter
                results = self.vector_db.search_by_metadata(
                    where={"float_id": float_obj.float_id},
                    limit=1
                )
                
                if not results:
                    # Float not found in vector DB, add it
                    float_meta = {
                        "float_id": float_obj.float_id,
                        "platform_number": float_obj.platform_number,
                        "deploy_date": str(float_obj.deploy_date) if float_obj.deploy_date else "",
                        "properties": float_obj.properties or {},
                        "region": "",  # Would need to be derived or stored separately
                        "description": "",
                        "notes": ""
                    }
                    missing_in_vector.append(float_meta)
            
            # Add missing floats to vector DB
            if missing_in_vector:
                success = await self._store_in_vector(missing_in_vector)
                return {
                    "status": "success" if success else "error",
                    "synced_count": len(missing_in_vector),
                    "message": f"Synced {len(missing_in_vector)} floats to vector database"
                }
            else:
                return {
                    "status": "success",
                    "synced_count": 0,
                    "message": "Databases are already in sync"
                }
                
        except Exception as e:
            logger.error(f"Database sync failed: {e}")
            return {"status": "error", "message": str(e)}


# Global dual storage service instance
dual_storage = DualStorageService()