"""Database query tool executor."""

from typing import Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from ..base_executor import BaseToolExecutor, ToolExecutionResult


class DatabaseQueryExecutor(BaseToolExecutor):
    """Executor for database query tool."""
    
    def __init__(self):
        super().__init__("database_query", "Database Query")
        self.category = "data"
        
        # Define parameter schema
        self.params_schema = {
            "query": {
                "type": "code",
                "description": "SQL query to execute",
                "required": True,
                "placeholder": "SELECT * FROM users WHERE id = ?"
            },
            "parameters": {
                "type": "array",
                "description": "Query parameters (for parameterized queries)",
                "required": False,
                "default": [],
                "placeholder": '["value1", "value2"]'
            },
            "database_url": {
                "type": "password",
                "description": "Database connection URL",
                "required": True,
                "placeholder": "postgresql://user:pass@localhost/dbname"
            },
            "timeout": {
                "type": "number",
                "description": "Query timeout in seconds",
                "required": False,
                "default": 30,
                "min": 1,
                "max": 300
            }
        }
    
    async def execute(
        self,
        params: Dict[str, Any],
        credentials: Optional[Dict[str, str]] = None
    ) -> ToolExecutionResult:
        """Execute database query."""
        
        self.validate_params(params, ["connection_string", "query"])
        
        connection_string = params.get("connection_string")
        query_str = params.get("query")
        query_params = params.get("params", {})
        
        try:
            engine = create_engine(connection_string)
            
            with engine.connect() as conn:
                result = conn.execute(text(query_str), query_params)
                
                # Fetch results if SELECT query
                if query_str.strip().upper().startswith("SELECT"):
                    rows = result.fetchall()
                    columns = result.keys()
                    
                    data = [
                        dict(zip(columns, row))
                        for row in rows
                    ]
                    
                    return ToolExecutionResult(
                        success=True,
                        output={
                            "rows": data,
                            "count": len(data),
                            "columns": list(columns)
                        }
                    )
                else:
                    # For INSERT/UPDATE/DELETE
                    conn.commit()
                    return ToolExecutionResult(
                        success=True,
                        output={
                            "affected_rows": result.rowcount
                        }
                    )
                    
        except SQLAlchemyError as e:
            return ToolExecutionResult(
                success=False,
                output=None,
                error=f"Database error: {str(e)}"
            )
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                output=None,
                error=f"Execution failed: {str(e)}"
            )
