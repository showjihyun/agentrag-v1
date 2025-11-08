"""Tool Registry for managing available tools in Agent Builder."""

import logging
import importlib
from typing import Dict, List, Optional, Type, Any
from sqlalchemy.orm import Session
from langchain.tools import BaseTool

from backend.db.models.agent_builder import Tool

logger = logging.getLogger(__name__)


class DatabaseQueryTool(BaseTool):
    """Tool for executing database queries."""
    
    name: str = "database_query"
    description: str = "Execute SQL queries on connected databases"
    
    def _run(self, query: str, database: str = "default") -> str:
        """Execute database query."""
        # Implementation will be added when database connections are configured
        raise NotImplementedError("Database query tool not yet implemented")
    
    async def _arun(self, query: str, database: str = "default") -> str:
        """Execute database query asynchronously."""
        raise NotImplementedError("Database query tool not yet implemented")


class FileOperationTool(BaseTool):
    """Tool for file operations."""
    
    name: str = "file_operation"
    description: str = "Read, write, and manipulate files"
    
    def _run(self, operation: str, path: str, content: str = None) -> str:
        """Execute file operation."""
        import aiofiles
        import os
        
        if operation == "read":
            if not os.path.exists(path):
                return f"Error: File not found: {path}"
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        elif operation == "write":
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content or "")
            return f"Successfully wrote to {path}"
        elif operation == "list":
            if not os.path.exists(path):
                return f"Error: Directory not found: {path}"
            files = os.listdir(path)
            return "\n".join(files)
        else:
            return f"Error: Unknown operation: {operation}"
    
    async def _arun(self, operation: str, path: str, content: str = None) -> str:
        """Execute file operation asynchronously."""
        import aiofiles
        import os
        
        if operation == "read":
            if not os.path.exists(path):
                return f"Error: File not found: {path}"
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                return await f.read()
        elif operation == "write":
            async with aiofiles.open(path, 'w', encoding='utf-8') as f:
                await f.write(content or "")
            return f"Successfully wrote to {path}"
        elif operation == "list":
            if not os.path.exists(path):
                return f"Error: Directory not found: {path}"
            files = os.listdir(path)
            return "\n".join(files)
        else:
            return f"Error: Unknown operation: {operation}"


class HTTPAPICallTool(BaseTool):
    """Tool for making HTTP API calls."""
    
    name: str = "http_api_call"
    description: str = "Make HTTP requests to external APIs"
    
    def _run(
        self,
        method: str,
        url: str,
        headers: Dict[str, str] = None,
        body: Dict[str, Any] = None
    ) -> str:
        """Execute HTTP API call."""
        import httpx
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    json=body
                )
                response.raise_for_status()
                return response.text
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _arun(
        self,
        method: str,
        url: str,
        headers: Dict[str, str] = None,
        body: Dict[str, Any] = None
    ) -> str:
        """Execute HTTP API call asynchronously."""
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    json=body
                )
                response.raise_for_status()
                return response.text
        except Exception as e:
            return f"Error: {str(e)}"


class VectorSearchTool(BaseTool):
    """Tool for vector search operations integrated with VectorSearchAgent."""
    
    name: str = "vector_search"
    description: str = "Search documents using semantic similarity from the vector database"
    
    def __init__(self, vector_search_agent=None):
        """Initialize with VectorSearchAgent."""
        super().__init__()
        self.vector_search_agent = vector_search_agent
    
    def _run(
        self,
        query: str,
        top_k: int = 10,
        knowledgebase_ids: List[str] = None
    ) -> str:
        """Execute vector search."""
        if not self.vector_search_agent:
            return "Error: Vector search agent not configured"
        
        try:
            # Use existing VectorSearchAgent's search functionality
            # Note: This is a synchronous wrapper, actual implementation uses async
            import asyncio
            loop = asyncio.get_event_loop()
            results = loop.run_until_complete(
                self._arun(query, top_k, knowledgebase_ids)
            )
            return results
        except Exception as e:
            logger.error(f"Vector search tool error: {e}")
            return f"Error executing vector search: {str(e)}"
    
    async def _arun(
        self,
        query: str,
        top_k: int = 10,
        knowledgebase_ids: List[str] = None
    ) -> str:
        """Execute vector search asynchronously using VectorSearchAgent."""
        if not self.vector_search_agent:
            return "Error: Vector search agent not configured"
        
        try:
            # Generate session ID for this search
            import uuid
            session_id = f"tool_{uuid.uuid4().hex[:8]}"
            
            # Collect results from VectorSearchAgent stream
            results = []
            async for chunk in self.vector_search_agent.process_query(
                query=query,
                session_id=session_id,
                top_k=top_k
            ):
                if chunk.get("type") == "final":
                    # Extract final response
                    data = chunk.get("data", {})
                    response = data.get("response", "")
                    sources = data.get("sources", [])
                    
                    # Format results
                    result_text = f"Response: {response}\n\nSources:\n"
                    for i, source in enumerate(sources[:5], 1):
                        result_text += f"{i}. {source.get('title', 'Unknown')}\n"
                    
                    return result_text
            
            return "No results found"
            
        except Exception as e:
            logger.error(f"Vector search tool async error: {e}")
            return f"Error executing vector search: {str(e)}"


class WebSearchTool(BaseTool):
    """Tool for web search operations integrated with WebSearchAgent."""
    
    name: str = "web_search"
    description: str = "Search the web using DuckDuckGo and combine with RAG results"
    
    def __init__(self, web_search_agent=None):
        """Initialize with WebSearchAgent."""
        super().__init__()
        self.web_search_agent = web_search_agent
    
    def _run(self, query: str, max_results: int = 5) -> str:
        """Execute web search."""
        if not self.web_search_agent:
            return "Error: Web search agent not configured"
        
        try:
            # Use existing WebSearchAgent's search functionality
            import asyncio
            loop = asyncio.get_event_loop()
            results = loop.run_until_complete(
                self._arun(query, max_results)
            )
            return results
        except Exception as e:
            logger.error(f"Web search tool error: {e}")
            return f"Error executing web search: {str(e)}"
    
    async def _arun(self, query: str, max_results: int = 5) -> str:
        """Execute web search asynchronously using WebSearchAgent."""
        if not self.web_search_agent:
            return "Error: Web search agent not configured"
        
        try:
            # Generate session ID for this search
            import uuid
            session_id = f"tool_{uuid.uuid4().hex[:8]}"
            
            # Collect results from WebSearchAgent stream
            results = []
            async for chunk in self.web_search_agent.process_query(
                query=query,
                session_id=session_id,
                top_k=10,
                web_results=max_results
            ):
                if chunk.get("type") == "final":
                    # Extract final response
                    data = chunk.get("data", {})
                    response = data.get("response", "")
                    sources = data.get("sources", [])
                    web_count = data.get("web_count", 0)
                    
                    # Format results
                    result_text = f"Response: {response}\n\nWeb Sources ({web_count}):\n"
                    for i, source in enumerate(sources, 1):
                        if source.get("type") == "web":
                            result_text += f"{i}. {source.get('title', 'Unknown')}\n"
                            result_text += f"   URL: {source.get('url', '')}\n"
                    
                    return result_text
            
            return "No results found"
            
        except Exception as e:
            logger.error(f"Web search tool async error: {e}")
            return f"Error executing web search: {str(e)}"


class LocalDataTool(BaseTool):
    """Tool for local data access integrated with LocalDataAgent."""
    
    name: str = "local_data"
    description: str = "Access local files and databases using the local data agent"
    
    def __init__(self, local_data_agent=None):
        """Initialize with LocalDataAgent."""
        super().__init__()
        self.local_data_agent = local_data_agent
    
    def _run(self, operation: str, path: str = None, query: str = None) -> str:
        """Execute local data operation."""
        if not self.local_data_agent:
            return "Error: Local data agent not configured"
        
        try:
            # Use existing LocalDataAgent's functionality
            import asyncio
            loop = asyncio.get_event_loop()
            results = loop.run_until_complete(
                self._arun(operation, path, query)
            )
            return results
        except Exception as e:
            logger.error(f"Local data tool error: {e}")
            return f"Error executing local data operation: {str(e)}"
    
    async def _arun(self, operation: str, path: str = None, query: str = None) -> str:
        """Execute local data operation asynchronously using LocalDataAgent."""
        if not self.local_data_agent:
            return "Error: Local data agent not configured"
        
        try:
            # Generate session ID for this operation
            import uuid
            session_id = f"tool_{uuid.uuid4().hex[:8]}"
            
            # Build query for LocalDataAgent
            if operation == "read_file" and path:
                agent_query = f"Read the file at {path}"
            elif operation == "query_database" and query:
                agent_query = f"Execute database query: {query}"
            else:
                return f"Error: Invalid operation '{operation}' or missing parameters"
            
            # Collect results from LocalDataAgent stream
            async for chunk in self.local_data_agent.process_query(
                query=agent_query,
                session_id=session_id
            ):
                if chunk.get("type") == "final":
                    # Extract final response
                    data = chunk.get("data", {})
                    response = data.get("response", "")
                    return f"Result: {response}"
            
            return "No results found"
            
        except Exception as e:
            logger.error(f"Local data tool async error: {e}")
            return f"Error executing local data operation: {str(e)}"


class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(
        self,
        db: Session,
        vector_search_agent=None,
        web_search_agent=None,
        local_data_agent=None
    ):
        """
        Initialize Tool Registry.
        
        Args:
            db: Database session
            vector_search_agent: VectorSearchAgent instance (optional)
            web_search_agent: WebSearchAgent instance (optional)
            local_data_agent: LocalDataAgent instance (optional)
        """
        self.db = db
        self._tool_cache: Dict[str, BaseTool] = {}
        self.vector_search_agent = vector_search_agent
        self.web_search_agent = web_search_agent
        self.local_data_agent = local_data_agent
        
        # Initialize built-in tools
        self._initialize_builtin_tools()
    
    def _initialize_builtin_tools(self):
        """Initialize built-in tools from existing agents."""
        logger.info("Initializing built-in tools...")
        
        # Vector Search Tool
        self._register_builtin_tool(
            tool_id="vector_search",
            name="Vector Search",
            description="Search documents using semantic similarity",
            category="search",
            tool_class=VectorSearchTool,
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "top_k": {
                        "type": "integer",
                        "default": 10,
                        "description": "Number of results"
                    },
                    "knowledgebase_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Knowledgebase IDs to search"
                    }
                },
                "required": ["query"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "results": {
                        "type": "array",
                        "items": {"type": "object"}
                    }
                }
            },
            tool_instance=VectorSearchTool(self.vector_search_agent)
        )
        
        # Web Search Tool
        self._register_builtin_tool(
            tool_id="web_search",
            name="Web Search",
            description="Search the web using DuckDuckGo",
            category="search",
            tool_class=WebSearchTool,
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {
                        "type": "integer",
                        "default": 5,
                        "description": "Maximum results"
                    }
                },
                "required": ["query"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "results": {
                        "type": "array",
                        "items": {"type": "object"}
                    }
                }
            },
            tool_instance=WebSearchTool(self.web_search_agent)
        )
        
        # Local Data Tool
        self._register_builtin_tool(
            tool_id="local_data",
            name="Local Data Access",
            description="Access local files and databases",
            category="data",
            tool_class=LocalDataTool,
            input_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["read_file", "query_database"],
                        "description": "Operation type"
                    },
                    "path": {"type": "string", "description": "File path"},
                    "query": {"type": "string", "description": "Database query"}
                },
                "required": ["operation"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "string"}
                }
            },
            tool_instance=LocalDataTool(self.local_data_agent)
        )
        
        # Database Query Tool
        self._register_builtin_tool(
            tool_id="database_query",
            name="Database Query",
            description="Execute SQL queries on connected databases",
            category="database",
            tool_class=DatabaseQueryTool,
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL query"},
                    "database": {
                        "type": "string",
                        "default": "default",
                        "description": "Database name"
                    }
                },
                "required": ["query"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "rows": {
                        "type": "array",
                        "items": {"type": "object"}
                    }
                }
            }
        )
        
        # File Operation Tool
        self._register_builtin_tool(
            tool_id="file_operation",
            name="File Operation",
            description="Read, write, and manipulate files",
            category="file",
            tool_class=FileOperationTool,
            input_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["read", "write", "list"],
                        "description": "Operation type"
                    },
                    "path": {"type": "string", "description": "File path"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["operation", "path"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "string"}
                }
            }
        )
        
        # HTTP API Call Tool
        self._register_builtin_tool(
            tool_id="http_api_call",
            name="HTTP API Call",
            description="Make HTTP requests to external APIs",
            category="api",
            tool_class=HTTPAPICallTool,
            input_schema={
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "enum": ["GET", "POST", "PUT", "DELETE"],
                        "description": "HTTP method"
                    },
                    "url": {"type": "string", "description": "API URL"},
                    "headers": {
                        "type": "object",
                        "description": "HTTP headers"
                    },
                    "body": {
                        "type": "object",
                        "description": "Request body"
                    }
                },
                "required": ["method", "url"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "response": {"type": "string"}
                }
            }
        )
        
        logger.info(f"Initialized {len(self._tool_cache)} built-in tools")
    
    def _register_builtin_tool(
        self,
        tool_id: str,
        name: str,
        description: str,
        category: str,
        tool_class: Type[BaseTool],
        input_schema: dict,
        output_schema: dict = None,
        requires_auth: bool = False,
        tool_instance: BaseTool = None
    ):
        """Register a built-in tool."""
        # Check if tool already exists in database
        tool = self.db.query(Tool).filter(Tool.id == tool_id).first()
        
        if not tool:
            # Create tool record
            tool = Tool(
                id=tool_id,
                name=name,
                description=description,
                category=category,
                input_schema=input_schema,
                output_schema=output_schema,
                implementation_type="langchain",
                implementation_ref=f"{tool_class.__module__}.{tool_class.__name__}",
                requires_auth=requires_auth,
                is_builtin=True
            )
            self.db.add(tool)
            try:
                self.db.commit()
                logger.info(f"Registered built-in tool: {tool_id}")
            except Exception as e:
                self.db.rollback()
                logger.warning(f"Tool {tool_id} may already exist: {e}")
        
        # Cache tool instance
        if tool_instance:
            self._tool_cache[tool_id] = tool_instance
        else:
            self._tool_cache[tool_id] = tool_class()
    
    def register_tool(
        self,
        tool_id: str,
        name: str,
        description: str,
        category: str,
        tool_class: Type[BaseTool],
        input_schema: dict,
        output_schema: dict = None,
        requires_auth: bool = False
    ):
        """
        Register a new custom tool.
        
        Args:
            tool_id: Unique tool identifier
            name: Tool name
            description: Tool description
            category: Tool category
            tool_class: Tool class (must inherit from BaseTool)
            input_schema: JSON Schema for inputs
            output_schema: JSON Schema for outputs
            requires_auth: Whether tool requires authentication
        """
        # Create or update tool in database
        tool = self.db.query(Tool).filter(Tool.id == tool_id).first()
        
        if not tool:
            tool = Tool(
                id=tool_id,
                name=name,
                description=description,
                category=category,
                input_schema=input_schema,
                output_schema=output_schema,
                implementation_type="langchain",
                implementation_ref=f"{tool_class.__module__}.{tool_class.__name__}",
                requires_auth=requires_auth,
                is_builtin=False
            )
            self.db.add(tool)
        else:
            # Update existing tool
            tool.name = name
            tool.description = description
            tool.category = category
            tool.input_schema = input_schema
            tool.output_schema = output_schema
            tool.implementation_ref = f"{tool_class.__module__}.{tool_class.__name__}"
            tool.requires_auth = requires_auth
        
        self.db.commit()
        
        # Cache tool instance
        self._tool_cache[tool_id] = tool_class()
        
        logger.info(f"Registered custom tool: {tool_id}")
    
    def get_tool(self, tool_id: str) -> BaseTool:
        """
        Get tool instance by ID.
        
        Args:
            tool_id: Tool identifier
            
        Returns:
            BaseTool instance
            
        Raises:
            ValueError: If tool not found
        """
        # Check cache first
        if tool_id in self._tool_cache:
            return self._tool_cache[tool_id]
        
        # Load from database
        tool = self.db.query(Tool).filter(Tool.id == tool_id).first()
        if not tool:
            raise ValueError(f"Tool not found: {tool_id}")
        
        # Instantiate tool
        if tool.implementation_type == "langchain":
            try:
                module_name, class_name = tool.implementation_ref.rsplit(".", 1)
                module = importlib.import_module(module_name)
                tool_class = getattr(module, class_name)
                tool_instance = tool_class()
                
                # Cache instance
                self._tool_cache[tool_id] = tool_instance
                return tool_instance
            except Exception as e:
                logger.error(f"Failed to instantiate tool {tool_id}: {e}")
                raise ValueError(f"Failed to instantiate tool: {tool_id}")
        
        raise ValueError(f"Unsupported tool implementation type: {tool.implementation_type}")
    
    def list_tools(
        self,
        category: Optional[str] = None,
        builtin_only: bool = False
    ) -> List[Tool]:
        """
        List available tools.
        
        Args:
            category: Filter by category (optional)
            builtin_only: Only return built-in tools
            
        Returns:
            List of Tool models
        """
        query = self.db.query(Tool)
        
        if category:
            query = query.filter(Tool.category == category)
        
        if builtin_only:
            query = query.filter(Tool.is_builtin == True)
        
        return query.all()
    
    def validate_tool_input(self, tool_id: str, input_data: dict) -> bool:
        """
        Validate tool input against schema.
        
        Args:
            tool_id: Tool identifier
            input_data: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        tool = self.db.query(Tool).filter(Tool.id == tool_id).first()
        if not tool:
            return False
        
        # Basic validation - check required fields
        schema = tool.input_schema
        if "required" in schema:
            for field in schema["required"]:
                if field not in input_data:
                    logger.warning(f"Missing required field: {field}")
                    return False
        
        return True
