"""Agent Builder API endpoints for tool configuration management."""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
from backend.core.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/tool-config",
    tags=["agent-builder-tool-config"],
)


class ToolConfigValidationRequest(BaseModel):
    """Request model for tool configuration validation."""
    
    tool_id: str = Field(..., description="Tool ID")
    configuration: Dict[str, Any] = Field(..., description="Tool configuration")


class ToolConfigValidationResponse(BaseModel):
    """Response model for tool configuration validation."""
    
    valid: bool = Field(..., description="Whether configuration is valid")
    errors: Dict[str, str] = Field(default_factory=dict, description="Validation errors by field")
    warnings: Dict[str, str] = Field(default_factory=dict, description="Validation warnings")


class ToolSchemaResponse(BaseModel):
    """Response model for tool schema."""
    
    tool_id: str
    name: str
    description: str
    params: Dict[str, Any]
    outputs: Dict[str, Any]
    examples: Optional[Dict[str, Any]] = None


@router.post("/validate")
async def validate_tool_config(
    request: ToolConfigValidationRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Validate tool configuration against tool schema.
    
    **Request Body:**
    - tool_id: Tool identifier
    - configuration: Tool configuration to validate
    
    **Returns:**
    - Validation result with errors and warnings
    
    **Errors:**
    - 401: Unauthorized
    - 404: Tool not found
    - 500: Internal server error
    """
    try:
        logger.info(f"Validating config for tool {request.tool_id}")
        
        # Get tool config
        tool_config = ToolRegistry.get_tool_config(request.tool_id)
        if not tool_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool {request.tool_id} not found"
            )
        
        errors = {}
        warnings = {}
        
        # Validate required parameters
        for param_name, param_config in tool_config.params.items():
            if param_config.required:
                if param_name not in request.configuration:
                    errors[param_name] = "This field is required"
                elif request.configuration[param_name] in [None, "", []]:
                    errors[param_name] = "This field cannot be empty"
        
        # Validate parameter types and constraints
        for param_name, value in request.configuration.items():
            if param_name.startswith("_"):
                # Skip internal fields
                continue
                
            if param_name not in tool_config.params:
                warnings[param_name] = "Unknown parameter"
                continue
            
            param_config = tool_config.params[param_name]
            
            # Type validation
            if value is not None:
                if param_config.type == "number":
                    try:
                        num_value = float(value)
                        if param_config.min is not None and num_value < param_config.min:
                            errors[param_name] = f"Must be at least {param_config.min}"
                        if param_config.max is not None and num_value > param_config.max:
                            errors[param_name] = f"Must be at most {param_config.max}"
                    except (ValueError, TypeError):
                        errors[param_name] = "Must be a valid number"
                
                elif param_config.type == "string":
                    if not isinstance(value, str):
                        errors[param_name] = "Must be a string"
                    elif param_config.enum and value not in param_config.enum:
                        errors[param_name] = f"Must be one of: {', '.join(param_config.enum)}"
                
                elif param_config.type == "boolean":
                    if not isinstance(value, bool):
                        errors[param_name] = "Must be a boolean"
                
                elif param_config.type == "array":
                    if not isinstance(value, list):
                        errors[param_name] = "Must be an array"
                
                elif param_config.type == "object":
                    if not isinstance(value, dict):
                        errors[param_name] = "Must be an object"
        
        return ToolConfigValidationResponse(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate tool config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate tool configuration"
        )


@router.get("/schema/{tool_id}")
async def get_tool_schema(
    tool_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed schema for a tool including examples.
    
    **Path Parameters:**
    - tool_id: Tool identifier
    
    **Returns:**
    - Tool schema with parameter definitions and examples
    
    **Errors:**
    - 401: Unauthorized
    - 404: Tool not found
    - 500: Internal server error
    """
    try:
        logger.info(f"Getting schema for tool {tool_id}")
        
        tool_config = ToolRegistry.get_tool_config(tool_id)
        if not tool_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool {tool_id} not found"
            )
        
        # Build parameter schema
        params_schema = {}
        for param_name, param_config in tool_config.params.items():
            params_schema[param_name] = {
                "type": param_config.type,
                "description": param_config.description,
                "required": param_config.required,
                "default": param_config.default,
                "enum": param_config.enum,
                "min": param_config.min,
                "max": param_config.max,
                "pattern": param_config.pattern,
            }
        
        # Build output schema
        outputs_schema = {}
        for output_name, output_config in tool_config.outputs.items():
            outputs_schema[output_name] = {
                "type": output_config.type,
                "description": output_config.description,
            }
        
        # Generate examples based on tool type
        examples = _generate_tool_examples(tool_id, tool_config)
        
        return ToolSchemaResponse(
            tool_id=tool_id,
            name=tool_config.name,
            description=tool_config.description,
            params=params_schema,
            outputs=outputs_schema,
            examples=examples
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tool schema: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tool schema"
        )


def _generate_tool_examples(tool_id: str, tool_config) -> Dict[str, Any]:
    """Generate example configurations for a tool."""
    
    examples = {}
    
    # Basic example with required fields only
    basic_example = {}
    for param_name, param_config in tool_config.params.items():
        if param_config.required:
            if param_config.default is not None:
                basic_example[param_name] = param_config.default
            elif param_config.type == "string":
                if param_config.enum:
                    basic_example[param_name] = param_config.enum[0]
                else:
                    basic_example[param_name] = f"example_{param_name}"
            elif param_config.type == "number":
                basic_example[param_name] = param_config.min or 0
            elif param_config.type == "boolean":
                basic_example[param_name] = False
            elif param_config.type == "array":
                basic_example[param_name] = []
            elif param_config.type == "object":
                basic_example[param_name] = {}
    
    examples["basic"] = basic_example
    
    # Advanced example with all fields
    advanced_example = {}
    for param_name, param_config in tool_config.params.items():
        if param_config.default is not None:
            advanced_example[param_name] = param_config.default
        elif param_config.type == "string":
            if param_config.enum:
                advanced_example[param_name] = param_config.enum[0]
            else:
                advanced_example[param_name] = f"example_{param_name}"
        elif param_config.type == "number":
            advanced_example[param_name] = param_config.default or (param_config.min or 0)
        elif param_config.type == "boolean":
            advanced_example[param_name] = True
        elif param_config.type == "array":
            advanced_example[param_name] = ["item1", "item2"]
        elif param_config.type == "object":
            advanced_example[param_name] = {"key": "value"}
    
    examples["advanced"] = advanced_example
    
    return examples
