"""
Database Integration Service

Supports PostgreSQL, MySQL, MongoDB operations.
"""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class DatabaseType(str, Enum):
    """Supported database types."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    SQLITE = "sqlite"


class DatabaseService:
    """Service for database operations."""
    
    def __init__(
        self,
        db_type: str,
        connection_string: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize database service.
        
        Args:
            db_type: Database type (postgresql, mysql, mongodb, sqlite)
            connection_string: Full connection string (optional)
            host: Database host
            port: Database port
            database: Database name
            username: Username
            password: Password
        """
        self.db_type = db_type.lower()
        self.connection_string = connection_string
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        
        # Build connection string if not provided
        if not self.connection_string:
            self.connection_string = self._build_connection_string()
    
    def _build_connection_string(self) -> str:
        """Build connection string from components."""
        if self.db_type == DatabaseType.POSTGRESQL:
            port = self.port or 5432
            return f"postgresql://{self.username}:{self.password}@{self.host}:{port}/{self.database}"
        
        elif self.db_type == DatabaseType.MYSQL:
            port = self.port or 3306
            return f"mysql://{self.username}:{self.password}@{self.host}:{port}/{self.database}"
        
        elif self.db_type == DatabaseType.MONGODB:
            port = self.port or 27017
            if self.username and self.password:
                return f"mongodb://{self.username}:{self.password}@{self.host}:{port}/{self.database}"
            return f"mongodb://{self.host}:{port}/{self.database}"
        
        elif self.db_type == DatabaseType.SQLITE:
            return f"sqlite:///{self.database}"
        
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a SQL query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query result with rows and metadata
        """
        if self.db_type in [DatabaseType.POSTGRESQL, DatabaseType.MYSQL, DatabaseType.SQLITE]:
            return await self._execute_sql_query(query, params)
        elif self.db_type == DatabaseType.MONGODB:
            return await self._execute_mongo_query(query, params)
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    async def _execute_sql_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute SQL query (PostgreSQL, MySQL, SQLite)."""
        try:
            import asyncpg
            from sqlalchemy.ext.asyncio import create_async_engine
            
            # Create async engine
            engine = create_async_engine(self.connection_string)
            
            async with engine.connect() as conn:
                # Execute query
                result = await conn.execute(query, params or {})
                
                # Fetch results
                if result.returns_rows:
                    rows = result.fetchall()
                    columns = result.keys()
                    
                    # Convert to list of dicts
                    data = [
                        {col: row[i] for i, col in enumerate(columns)}
                        for row in rows
                    ]
                    
                    return {
                        "success": True,
                        "operation": "query",
                        "rows": data,
                        "row_count": len(data),
                        "columns": list(columns),
                    }
                else:
                    # INSERT, UPDATE, DELETE
                    return {
                        "success": True,
                        "operation": "execute",
                        "affected_rows": result.rowcount,
                    }
            
        except Exception as e:
            logger.error(f"SQL query execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "query": query,
            }
    
    async def _execute_mongo_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute MongoDB query."""
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            import json
            
            # Parse query (should be JSON)
            query_dict = json.loads(query) if isinstance(query, str) else query
            
            # Connect to MongoDB
            client = AsyncIOMotorClient(self.connection_string)
            db = client[self.database]
            
            # Get collection and operation
            collection_name = query_dict.get("collection")
            operation = query_dict.get("operation", "find")
            filter_query = query_dict.get("filter", {})
            
            if not collection_name:
                raise ValueError("Collection name is required")
            
            collection = db[collection_name]
            
            # Execute operation
            if operation == "find":
                cursor = collection.find(filter_query)
                documents = await cursor.to_list(length=100)
                
                # Convert ObjectId to string
                for doc in documents:
                    if "_id" in doc:
                        doc["_id"] = str(doc["_id"])
                
                return {
                    "success": True,
                    "operation": "find",
                    "documents": documents,
                    "count": len(documents),
                }
            
            elif operation == "insert_one":
                document = query_dict.get("document", {})
                result = await collection.insert_one(document)
                
                return {
                    "success": True,
                    "operation": "insert_one",
                    "inserted_id": str(result.inserted_id),
                }
            
            elif operation == "update_one":
                update = query_dict.get("update", {})
                result = await collection.update_one(filter_query, update)
                
                return {
                    "success": True,
                    "operation": "update_one",
                    "matched_count": result.matched_count,
                    "modified_count": result.modified_count,
                }
            
            elif operation == "delete_one":
                result = await collection.delete_one(filter_query)
                
                return {
                    "success": True,
                    "operation": "delete_one",
                    "deleted_count": result.deleted_count,
                }
            
            else:
                raise ValueError(f"Unsupported operation: {operation}")
            
        except Exception as e:
            logger.error(f"MongoDB query execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "query": query,
            }
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test database connection.
        
        Returns:
            Connection test result
        """
        try:
            if self.db_type in [DatabaseType.POSTGRESQL, DatabaseType.MYSQL, DatabaseType.SQLITE]:
                from sqlalchemy.ext.asyncio import create_async_engine
                
                engine = create_async_engine(self.connection_string)
                async with engine.connect() as conn:
                    await conn.execute("SELECT 1")
                
                return {
                    "success": True,
                    "message": f"Successfully connected to {self.db_type}",
                }
            
            elif self.db_type == DatabaseType.MONGODB:
                from motor.motor_asyncio import AsyncIOMotorClient
                
                client = AsyncIOMotorClient(self.connection_string)
                await client.server_info()
                
                return {
                    "success": True,
                    "message": "Successfully connected to MongoDB",
                }
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def list_tables(self) -> Dict[str, Any]:
        """
        List all tables/collections.
        
        Returns:
            List of tables/collections
        """
        try:
            if self.db_type == DatabaseType.POSTGRESQL:
                query = """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """
                result = await self.execute_query(query)
                tables = [row["table_name"] for row in result.get("rows", [])]
                
                return {
                    "success": True,
                    "tables": tables,
                    "count": len(tables),
                }
            
            elif self.db_type == DatabaseType.MYSQL:
                query = "SHOW TABLES"
                result = await self.execute_query(query)
                tables = [list(row.values())[0] for row in result.get("rows", [])]
                
                return {
                    "success": True,
                    "tables": tables,
                    "count": len(tables),
                }
            
            elif self.db_type == DatabaseType.MONGODB:
                from motor.motor_asyncio import AsyncIOMotorClient
                
                client = AsyncIOMotorClient(self.connection_string)
                db = client[self.database]
                collections = await db.list_collection_names()
                
                return {
                    "success": True,
                    "collections": collections,
                    "count": len(collections),
                }
            
        except Exception as e:
            logger.error(f"Failed to list tables: {e}")
            return {
                "success": False,
                "error": str(e),
            }
