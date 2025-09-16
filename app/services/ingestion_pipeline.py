"""
Data ingestion pipeline for ARGO float data that automatically populates both databases.
Handles batch processing, data validation, and error recovery.
"""
import asyncio
import pandas as pd
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timezone
import json
import os

from ..database import get_db
from .dual_storage import dual_storage
from .vector_db import chroma_db

logger = logging.getLogger(__name__)

class DataIngestionPipeline:
    """Pipeline for ingesting ARGO float data into both SQL and Vector databases."""
    
    def __init__(self, batch_size: int = 100):
        """
        Initialize data ingestion pipeline.
        
        Args:
            batch_size: Number of records to process in each batch
        """
        self.batch_size = batch_size
        self.ingestion_stats = {
            "total_processed": 0,
            "successful_ingestions": 0,
            "failed_ingestions": 0,
            "sql_failures": 0,
            "vector_failures": 0,
            "start_time": None,
            "end_time": None
        }
    
    async def ingest_from_file(self, file_path: str, file_format: str = "auto") -> Dict[str, Any]:
        """
        Ingest data from a file (CSV, JSON, or Parquet).
        
        Args:
            file_path: Path to the data file
            file_format: File format ('csv', 'json', 'parquet', or 'auto')
            
        Returns:
            Dictionary with ingestion results
        """
        try:
            self.ingestion_stats["start_time"] = datetime.now(timezone.utc)
            
            # Detect file format if auto
            if file_format == "auto":
                file_format = self._detect_file_format(file_path)
            
            # Load data from file
            data = self._load_data_from_file(file_path, file_format)
            
            # Process data in batches
            result = await self._process_data_batches(data)
            
            self.ingestion_stats["end_time"] = datetime.now(timezone.utc)
            result["ingestion_stats"] = self.ingestion_stats
            
            return result
            
        except Exception as e:
            logger.error(f"File ingestion failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def ingest_from_dict(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ingest data from a list of dictionaries.
        
        Args:
            data: List of float data dictionaries
            
        Returns:
            Dictionary with ingestion results
        """
        try:
            self.ingestion_stats["start_time"] = datetime.now(timezone.utc)
            
            # Process data in batches
            result = await self._process_data_batches(data)
            
            self.ingestion_stats["end_time"] = datetime.now(timezone.utc)
            result["ingestion_stats"] = self.ingestion_stats
            
            return result
            
        except Exception as e:
            logger.error(f"Dictionary ingestion failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def ingest_realtime_data(self, data_stream: Any) -> Dict[str, Any]:
        """
        Ingest data from a real-time stream (placeholder for future implementation).
        
        Args:
            data_stream: Real-time data stream source
            
        Returns:
            Dictionary with ingestion results
        """
        # Placeholder for real-time ingestion
        return {
            "status": "not_implemented",
            "message": "Real-time ingestion not yet implemented"
        }
    
    async def _process_data_batches(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process data in batches for efficient ingestion."""
        total_records = len(data)
        self.ingestion_stats["total_processed"] = total_records
        
        successful_batches = 0
        failed_batches = 0
        
        # Process data in batches
        for i in range(0, total_records, self.batch_size):
            batch = data[i:i + self.batch_size]
            
            try:
                # Validate and normalize batch data
                normalized_batch = self._validate_and_normalize_batch(batch)
                
                # Get database session
                db = next(get_db())
                
                # Ingest batch into both databases
                batch_result = await dual_storage.ingest_float_data(normalized_batch, db)
                
                if batch_result["status"] in ["success", "partial"]:
                    successful_batches += 1
                    self.ingestion_stats["successful_ingestions"] += len(normalized_batch)
                else:
                    failed_batches += 1
                    self.ingestion_stats["failed_ingestions"] += len(normalized_batch)
                
                logger.info(f"Processed batch {i//self.batch_size + 1}/{(total_records-1)//self.batch_size + 1}")
                
            except Exception as e:
                failed_batches += 1
                self.ingestion_stats["failed_ingestions"] += len(batch)
                logger.error(f"Batch processing failed: {e}")
            
            finally:
                db.close()
        
        return {
            "status": "success" if failed_batches == 0 else "partial",
            "total_records": total_records,
            "successful_batches": successful_batches,
            "failed_batches": failed_batches,
            "batch_size": self.batch_size
        }
    
    def _validate_and_normalize_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and normalize a batch of float data."""
        normalized_batch = []
        
        for record in batch:
            try:
                normalized_record = self._normalize_float_record(record)
                if self._validate_float_record(normalized_record):
                    normalized_batch.append(normalized_record)
                else:
                    logger.warning(f"Invalid record skipped: {record.get('float_id', 'unknown')}")
            except Exception as e:
                logger.error(f"Record normalization failed: {e}")
        
        return normalized_batch
    
    def _normalize_float_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a single float record to standard format."""
        normalized = {
            "float_id": str(record.get("float_id", "")),
            "platform_number": str(record.get("platform_number", "")),
            "deploy_date": self._parse_date(record.get("deploy_date")),
            "region": str(record.get("region", "")),
            "description": str(record.get("description", "")),
            "notes": str(record.get("notes", "")),
            "lat": self._parse_float(record.get("lat")),
            "lon": self._parse_float(record.get("lon")),
            "properties": record.get("properties", {}),
            "profiles": record.get("profiles", [])
        }
        
        return normalized
    
    def _validate_float_record(self, record: Dict[str, Any]) -> bool:
        """Validate a float record."""
        # Required fields
        if not record.get("float_id"):
            return False
        
        # Validate coordinates if present
        lat = record.get("lat")
        lon = record.get("lon")
        if lat is not None and (lat < -90 or lat > 90):
            return False
        if lon is not None and (lon < -180 or lon > 180):
            return False
        
        return True
    
    def _parse_date(self, date_value: Any) -> Optional[datetime]:
        """Parse various date formats to datetime object."""
        if date_value is None:
            return None
        
        if isinstance(date_value, datetime):
            return date_value
        
        if isinstance(date_value, str):
            # Try common date formats
            formats = [
                "%Y-%m-%d",
                "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d",
                "%d/%m/%Y",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_value, fmt)
                except ValueError:
                    continue
        
        return None
    
    def _parse_float(self, value: Any) -> Optional[float]:
        """Parse various number formats to float."""
        if value is None or value == "":
            return None
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _detect_file_format(self, file_path: str) -> str:
        """Detect file format from extension."""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == ".csv":
            return "csv"
        elif ext == ".json":
            return "json"
        elif ext == ".parquet":
            return "parquet"
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def _load_data_from_file(self, file_path: str, file_format: str) -> List[Dict[str, Any]]:
        """Load data from file based on format."""
        try:
            if file_format == "csv":
                df = pd.read_csv(file_path)
                return df.to_dict('records')
            
            elif file_format == "json":
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else [data]
            
            elif file_format == "parquet":
                df = pd.read_parquet(file_path)
                return df.to_dict('records')
            
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
                
        except Exception as e:
            logger.error(f"Failed to load data from {file_path}: {e}")
            raise
    
    def get_ingestion_stats(self) -> Dict[str, Any]:
        """Get current ingestion statistics."""
        stats = self.ingestion_stats.copy()
        
        if stats["start_time"] and stats["end_time"]:
            duration = stats["end_time"] - stats["start_time"]
            stats["duration_seconds"] = duration.total_seconds()
            
            if stats["total_processed"] > 0:
                stats["records_per_second"] = stats["total_processed"] / duration.total_seconds()
        
        return stats
    
    def reset_stats(self):
        """Reset ingestion statistics."""
        self.ingestion_stats = {
            "total_processed": 0,
            "successful_ingestions": 0,
            "failed_ingestions": 0,
            "sql_failures": 0,
            "vector_failures": 0,
            "start_time": None,
            "end_time": None
        }


# Global ingestion pipeline instance
ingestion_pipeline = DataIngestionPipeline()