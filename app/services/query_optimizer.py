"""
Intelligent query optimization service that routes queries between SQL and Vector databases
based on performance, query type, and success probability.
"""
import asyncio
import time
from typing import Dict, Any, List, Tuple, Optional, Union
from sqlalchemy.orm import Session
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import re

from .. import langchain_services
from .semantic_service import semantic_search, classify_query_type, get_embeddings
from .vector_db import chroma_db

logger = logging.getLogger(__name__)

class QueryOptimizer:
    """Intelligent query router with performance monitoring and fallback logic."""
    
    def __init__(self, sql_timeout: float = 30.0, vector_timeout: float = 10.0):
        """
        Initialize query optimizer.
        
        Args:
            sql_timeout: Timeout for SQL queries in seconds
            vector_timeout: Timeout for vector queries in seconds
        """
        self.sql_timeout = sql_timeout
        self.vector_timeout = vector_timeout
        self.performance_stats = {
            "sql_queries": {"count": 0, "total_time": 0, "failures": 0},
            "vector_queries": {"count": 0, "total_time": 0, "failures": 0},
            "concurrent_queries": {"count": 0, "total_time": 0}
        }
        
    async def optimize_query(self, query: str, db: Session, 
                           strategy: str = "adaptive") -> Dict[str, Any]:
        """
        Execute optimized query using the best strategy.
        
        Args:
            query: User's natural language query
            db: Database session
            strategy: Query strategy ('sql_first', 'vector_first', 'concurrent', 'adaptive')
            
        Returns:
            Dictionary with query results and metadata
        """
        start_time = time.time()
        
        try:
            # Classify query type
            query_type = classify_query_type(query)
            
            # Choose strategy based on query type and historical performance
            if strategy == "adaptive":
                strategy = self._choose_adaptive_strategy(query_type)
            
            # Execute query based on strategy
            if strategy == "sql_first":
                result = await self._sql_first_strategy(query, db)
            elif strategy == "vector_first":
                result = await self._vector_first_strategy(query)
            elif strategy == "concurrent":
                result = await self._concurrent_strategy(query, db)
            else:
                result = await self._adaptive_strategy(query, db, query_type)
            
            # Add metadata
            total_time = time.time() - start_time
            result.update({
                "query_type": query_type,
                "strategy_used": strategy,
                "total_time": total_time,
                "optimizer_stats": self._get_performance_summary()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Query optimization failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "query": query,
                "strategy_used": strategy
            }
    
    async def _sql_first_strategy(self, query: str, db: Session) -> Dict[str, Any]:
        """Try SQL first, fallback to vector search if it fails or times out."""
        # Try SQL query first
        sql_result = await self._execute_sql_query(query, db)
        
        if sql_result["status"] == "success" and sql_result.get("results"):
            return {
                "status": "success",
                "source": "sql",
                "results": sql_result["results"],
                "fallback_used": False,
                "message": "SQL query successful"
            }
        
        # Fallback to vector search
        logger.info("SQL query failed or returned no results, falling back to vector search")
        vector_result = await self._execute_vector_query(query)
        
        return {
            "status": vector_result["status"],
            "source": "vector_fallback",
            "results": vector_result.get("results", []),
            "fallback_used": True,
            "sql_error": sql_result.get("message"),
            "message": "Used vector search as fallback"
        }
    
    async def _vector_first_strategy(self, query: str) -> Dict[str, Any]:
        """Try vector search first, with option for SQL fallback."""
        vector_result = await self._execute_vector_query(query)
        
        return {
            "status": vector_result["status"],
            "source": "vector",
            "results": vector_result.get("results", []),
            "fallback_used": False,
            "message": "Vector search completed"
        }
    
    async def _concurrent_strategy(self, query: str, db: Session) -> Dict[str, Any]:
        """Execute both SQL and vector queries concurrently and combine results."""
        start_time = time.time()
        
        # Execute both queries concurrently
        sql_task = asyncio.create_task(self._execute_sql_query(query, db))
        vector_task = asyncio.create_task(self._execute_vector_query(query))
        
        # Wait for both to complete
        sql_result, vector_result = await asyncio.gather(sql_task, vector_task, return_exceptions=True)
        
        # Handle exceptions
        if isinstance(sql_result, Exception):
            sql_result = {"status": "error", "message": str(sql_result)}
        if isinstance(vector_result, Exception):
            vector_result = {"status": "error", "message": str(vector_result)}
        
        # Combine results
        combined_results = []
        
        if sql_result.get("status") == "success":
            sql_items = sql_result.get("results", [])
            for item in sql_items:
                combined_results.append({
                    "source": "sql",
                    "data": item,
                    "score": 1.0  # SQL results get perfect score
                })
        
        if vector_result.get("status") == "success":
            vector_items = vector_result.get("results", [])
            for item in vector_items:
                combined_results.append({
                    "source": "vector",
                    "data": item.get("metadata", {}),
                    "score": item.get("similarity_score", 0.0)
                })
        
        # Update performance stats
        self.performance_stats["concurrent_queries"]["count"] += 1
        self.performance_stats["concurrent_queries"]["total_time"] += time.time() - start_time
        
        return {
            "status": "success" if combined_results else "no_results",
            "source": "concurrent",
            "results": combined_results,
            "sql_status": sql_result.get("status"),
            "vector_status": vector_result.get("status"),
            "message": f"Concurrent search returned {len(combined_results)} results"
        }
    
    async def _adaptive_strategy(self, query: str, db: Session, query_type: str) -> Dict[str, Any]:
        """Adaptive strategy based on query type and historical performance."""
        sql_avg_time = self._get_avg_response_time("sql")
        vector_avg_time = self._get_avg_response_time("vector")
        sql_success_rate = self._get_success_rate("sql")
        vector_success_rate = self._get_success_rate("vector")
        
        # Decision logic based on query type and performance
        if query_type == "numeric":
            # Numeric queries typically work better with SQL
            if sql_success_rate > 0.7:  # SQL has good success rate
                return await self._sql_first_strategy(query, db)
            else:
                return await self._concurrent_strategy(query, db)
                
        elif query_type == "semantic":
            # Semantic queries work better with vector search
            return await self._vector_first_strategy(query)
            
        else:  # mixed or unknown
            # For mixed queries, use concurrent if both systems are performing well
            if sql_success_rate > 0.5 and vector_success_rate > 0.5:
                return await self._concurrent_strategy(query, db)
            elif sql_avg_time < vector_avg_time:
                return await self._sql_first_strategy(query, db)
            else:
                return await self._vector_first_strategy(query)
    
    async def _execute_sql_query(self, query: str, db: Session) -> Dict[str, Any]:
        """Execute SQL query with timeout and performance tracking."""
        start_time = time.time()
        
        try:
            # Use ThreadPoolExecutor to run SQL query with timeout
            with ThreadPoolExecutor() as executor:
                future = executor.submit(langchain_services.handle_natural_language_query, query)
                try:
                    result = future.result(timeout=self.sql_timeout)
                    
                    # Update performance stats
                    self.performance_stats["sql_queries"]["count"] += 1
                    self.performance_stats["sql_queries"]["total_time"] += time.time() - start_time
                    
                    return {
                        "status": "success",
                        "results": [result],  # Wrap in list for consistency
                        "response_time": time.time() - start_time
                    }
                    
                except FutureTimeoutError:
                    self.performance_stats["sql_queries"]["failures"] += 1
                    return {
                        "status": "timeout", 
                        "message": f"SQL query timed out after {self.sql_timeout}s"
                    }
                    
        except Exception as e:
            self.performance_stats["sql_queries"]["failures"] += 1
            logger.error(f"SQL query failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _execute_vector_query(self, query: str) -> Dict[str, Any]:
        """Execute vector query with timeout and performance tracking."""
        start_time = time.time()
        
        try:
            # Vector search is typically fast, but add timeout for safety
            vector_result = await asyncio.wait_for(
                self._run_vector_search(query),
                timeout=self.vector_timeout
            )
            
            # Update performance stats
            self.performance_stats["vector_queries"]["count"] += 1
            self.performance_stats["vector_queries"]["total_time"] += time.time() - start_time
            
            return vector_result
            
        except asyncio.TimeoutError:
            self.performance_stats["vector_queries"]["failures"] += 1
            return {
                "status": "timeout",
                "message": f"Vector query timed out after {self.vector_timeout}s"
            }
        except Exception as e:
            self.performance_stats["vector_queries"]["failures"] += 1
            logger.error(f"Vector query failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _run_vector_search(self, query: str) -> Dict[str, Any]:
        """Run vector search in async context."""
        return semantic_search(query, top_k=10)
    
    def _choose_adaptive_strategy(self, query_type: str) -> str:
        """Choose the best strategy based on query type and performance history."""
        sql_success_rate = self._get_success_rate("sql")
        vector_success_rate = self._get_success_rate("vector")
        
        if query_type == "numeric" and sql_success_rate > 0.6:
            return "sql_first"
        elif query_type == "semantic":
            return "vector_first"
        elif sql_success_rate > 0.5 and vector_success_rate > 0.5:
            return "concurrent"
        else:
            return "sql_first"  # Default fallback
    
    def _get_avg_response_time(self, db_type: str) -> float:
        """Get average response time for a database type."""
        stats = self.performance_stats.get(f"{db_type}_queries", {})
        count = stats.get("count", 0)
        total_time = stats.get("total_time", 0)
        return total_time / count if count > 0 else 0.0
    
    def _get_success_rate(self, db_type: str) -> float:
        """Get success rate for a database type."""
        stats = self.performance_stats.get(f"{db_type}_queries", {})
        count = stats.get("count", 0)
        failures = stats.get("failures", 0)
        return (count - failures) / count if count > 0 else 0.0
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of performance statistics."""
        return {
            "sql": {
                "avg_response_time": self._get_avg_response_time("sql"),
                "success_rate": self._get_success_rate("sql"),
                "total_queries": self.performance_stats["sql_queries"]["count"]
            },
            "vector": {
                "avg_response_time": self._get_avg_response_time("vector"),
                "success_rate": self._get_success_rate("vector"),
                "total_queries": self.performance_stats["vector_queries"]["count"]
            },
            "concurrent": {
                "avg_response_time": self._get_avg_response_time("concurrent"),
                "total_queries": self.performance_stats["concurrent_queries"]["count"]
            }
        }
    
    def reset_stats(self):
        """Reset performance statistics."""
        self.performance_stats = {
            "sql_queries": {"count": 0, "total_time": 0, "failures": 0},
            "vector_queries": {"count": 0, "total_time": 0, "failures": 0},
            "concurrent_queries": {"count": 0, "total_time": 0}
        }


# Global query optimizer instance with increased timeouts
query_optimizer = QueryOptimizer(sql_timeout=30.0, vector_timeout=10.0)