"""
Plugin Configuration API Endpoints
플러그인 설정 관리를 위한 API 엔드포인트
"""
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import logging
import json
from datetime import datetime

from backend.core.dependencies import get_current_user
from backend.models.user import User
from backend.services.plugins.agents.enhanced_agent_plugin_manager import EnhancedAgentPluginManager
from backend.services.plugins.plugin_integration_service import get_plugin_integration_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/plugins", tags=["Plugin Configuration"])


# Request/Response Models
class PluginConfigField(BaseModel):
    """플러그인 설정 필드"""
    name: str
    type: str = Field(..., regex=r'^(text|number|boolean|select|multiselect|textarea|password|url|email)$')
    label: str
    description: Optional[str] = None
    required: bool = False
    defaultValue: Any = None
    placeholder: Optional[str] = None
    validation: Optional[Dict[str, Any]] = None
    options: Optional[List[Dict[str, Any]]] = None
    group: Optional[str] = None
    dependsOn: Optional[Dict[str, Any]] = None
    sensitive: bool = False


class PluginConfigSchema(BaseModel):
    """플러그인 설정 스키마"""
    title: str
    description: Optional[str] = None
    version: str
    fields: List[PluginConfigField]
    presets: Optional[List[Dict[str, Any]]] = None


class PluginConfigValues(BaseModel):
    """플러그인 설정 값"""
    values: Dict[str, Any]


class PluginConfigValidationRequest(BaseModel):
    """플러그인 설정 검증 요청"""
    values: Dict[str, Any]


class PluginConfigValidationResponse(BaseModel):
    """플러그인 설정 검증 응답"""
    valid: bool
    errors: Dict[str, str] = {}


class PluginConfigHistory(BaseModel):
    """플러그인 설정 히스토리"""
    id: str
    timestamp: str
    values: Dict[str, Any]
    description: Optional[str] = None


# API Endpoints

@router.get("/{plugin_id}/config-schema")
async def get_plugin_config_schema(
    plugin_id: str,
    current_user: User = Depends(get_current_user)
) -> PluginConfigSchema:
    """플러그인 설정 스키마 조회"""
    try:
        integration_service = await get_plugin_integration_service()
        
        # 플러그인 정보 조회
        plugin_info = await integration_service.enhanced_agent_manager.get_plugin_info(plugin_id)
        if not plugin_info:
            raise HTTPException(status_code=404, detail="Plugin not found")
        
        # 설정 스키마 생성 (플러그인 타입에 따라)
        schema = await generate_config_schema(plugin_id, plugin_info)
        
        return schema
        
    except Exception as e:
        logger.error(f"Failed to get config schema for plugin {plugin_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get configuration schema")


@router.get("/{plugin_id}/config")
async def get_plugin_config(
    plugin_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """플러그인 현재 설정 조회"""
    try:
        integration_service = await get_plugin_integration_service()
        
        config = await integration_service.enhanced_agent_manager.get_plugin_config(plugin_id)
        if config is None:
            raise HTTPException(status_code=404, detail="Plugin configuration not found")
        
        return {"values": config}
        
    except Exception as e:
        logger.error(f"Failed to get config for plugin {plugin_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get plugin configuration")


@router.put("/{plugin_id}/config")
async def update_plugin_config(
    plugin_id: str,
    config_values: PluginConfigValues,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """플러그인 설정 업데이트"""
    try:
        integration_service = await get_plugin_integration_service()
        
        # 설정 검증
        validation_result = await validate_plugin_config(plugin_id, config_values.values)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400, 
                detail={"message": "Configuration validation failed", "errors": validation_result["errors"]}
            )
        
        # 설정 업데이트
        success = await integration_service.enhanced_agent_manager.update_plugin_config(
            plugin_id, 
            config_values.values,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update plugin configuration")
        
        # 백그라운드에서 설정 히스토리 저장
        background_tasks.add_task(
            save_config_history,
            plugin_id,
            config_values.values,
            current_user.id
        )
        
        return {"message": "Configuration updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update config for plugin {plugin_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update plugin configuration")


@router.post("/{plugin_id}/validate-config")
async def validate_plugin_config_endpoint(
    plugin_id: str,
    validation_request: PluginConfigValidationRequest,
    current_user: User = Depends(get_current_user)
) -> PluginConfigValidationResponse:
    """플러그인 설정 검증"""
    try:
        result = await validate_plugin_config(plugin_id, validation_request.values)
        return PluginConfigValidationResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to validate config for plugin {plugin_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to validate plugin configuration")


@router.get("/{plugin_id}/config-history")
async def get_plugin_config_history(
    plugin_id: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
) -> List[PluginConfigHistory]:
    """플러그인 설정 히스토리 조회"""
    try:
        integration_service = await get_plugin_integration_service()
        
        history = await integration_service.enhanced_agent_manager.get_config_history(
            plugin_id, 
            limit=limit
        )
        
        return [
            PluginConfigHistory(
                id=item["id"],
                timestamp=item["timestamp"],
                values=item["values"],
                description=item.get("description")
            )
            for item in history
        ]
        
    except Exception as e:
        logger.error(f"Failed to get config history for plugin {plugin_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get configuration history")


# Helper Functions

async def generate_config_schema(plugin_id: str, plugin_info: Dict[str, Any]) -> PluginConfigSchema:
    """플러그인 타입에 따른 설정 스키마 생성"""
    
    plugin_type = plugin_info.get("agent_type", "unknown")
    
    # 기본 스키마
    base_fields = [
        PluginConfigField(
            name="enabled",
            type="boolean",
            label="Enable Plugin",
            description="Enable or disable this plugin",
            required=False,
            defaultValue=True,
            group="General"
        ),
        PluginConfigField(
            name="timeout",
            type="number",
            label="Timeout (seconds)",
            description="Maximum execution time in seconds",
            required=False,
            defaultValue=30,
            validation={"min": 1, "max": 300},
            group="General"
        ),
        PluginConfigField(
            name="retry_count",
            type="number",
            label="Retry Count",
            description="Number of retries on failure",
            required=False,
            defaultValue=3,
            validation={"min": 0, "max": 10},
            group="General"
        )
    ]
    
    # 플러그인 타입별 특화 필드
    type_specific_fields = []
    
    if plugin_type == "vector_search":
        type_specific_fields = [
            PluginConfigField(
                name="collection_name",
                type="text",
                label="Collection Name",
                description="Milvus collection name",
                required=True,
                placeholder="documents",
                group="Vector Search"
            ),
            PluginConfigField(
                name="top_k",
                type="number",
                label="Top K Results",
                description="Number of top results to return",
                required=False,
                defaultValue=10,
                validation={"min": 1, "max": 100},
                group="Vector Search"
            ),
            PluginConfigField(
                name="similarity_threshold",
                type="number",
                label="Similarity Threshold",
                description="Minimum similarity score (0.0 - 1.0)",
                required=False,
                defaultValue=0.7,
                validation={"min": 0.0, "max": 1.0},
                group="Vector Search"
            )
        ]
    
    elif plugin_type == "web_search":
        type_specific_fields = [
            PluginConfigField(
                name="search_engine",
                type="select",
                label="Search Engine",
                description="Search engine to use",
                required=True,
                defaultValue="duckduckgo",
                options=[
                    {"label": "DuckDuckGo", "value": "duckduckgo"},
                    {"label": "Google", "value": "google"},
                    {"label": "Bing", "value": "bing"}
                ],
                group="Web Search"
            ),
            PluginConfigField(
                name="max_results",
                type="number",
                label="Max Results",
                description="Maximum number of search results",
                required=False,
                defaultValue=10,
                validation={"min": 1, "max": 50},
                group="Web Search"
            ),
            PluginConfigField(
                name="safe_search",
                type="boolean",
                label="Safe Search",
                description="Enable safe search filtering",
                required=False,
                defaultValue=True,
                group="Web Search"
            )
        ]
    
    elif plugin_type == "local_data":
        type_specific_fields = [
            PluginConfigField(
                name="data_path",
                type="text",
                label="Data Path",
                description="Path to local data directory",
                required=True,
                placeholder="/path/to/data",
                group="Local Data"
            ),
            PluginConfigField(
                name="file_extensions",
                type="multiselect",
                label="File Extensions",
                description="Supported file extensions",
                required=False,
                options=[
                    {"label": "PDF", "value": "pdf"},
                    {"label": "DOCX", "value": "docx"},
                    {"label": "TXT", "value": "txt"},
                    {"label": "MD", "value": "md"}
                ],
                group="Local Data"
            ),
            PluginConfigField(
                name="recursive_search",
                type="boolean",
                label="Recursive Search",
                description="Search subdirectories recursively",
                required=False,
                defaultValue=True,
                group="Local Data"
            )
        ]
    
    # 모든 필드 결합
    all_fields = base_fields + type_specific_fields
    
    # 프리셋 생성
    presets = []
    if plugin_type == "vector_search":
        presets = [
            {
                "name": "High Precision",
                "description": "High precision search with strict similarity threshold",
                "values": {
                    "top_k": 5,
                    "similarity_threshold": 0.85,
                    "timeout": 60
                }
            },
            {
                "name": "Broad Search",
                "description": "Broad search with lower similarity threshold",
                "values": {
                    "top_k": 20,
                    "similarity_threshold": 0.6,
                    "timeout": 30
                }
            }
        ]
    
    return PluginConfigSchema(
        title=plugin_info.get("agent_name", "Plugin Configuration"),
        description=plugin_info.get("description", "Configure plugin settings"),
        version=plugin_info.get("version", "1.0.0"),
        fields=all_fields,
        presets=presets
    )


async def validate_plugin_config(plugin_id: str, values: Dict[str, Any]) -> Dict[str, Any]:
    """플러그인 설정 검증"""
    errors = {}
    
    try:
        integration_service = await get_plugin_integration_service()
        
        # 플러그인 정보 조회
        plugin_info = await integration_service.enhanced_agent_manager.get_plugin_info(plugin_id)
        if not plugin_info:
            return {"valid": False, "errors": {"general": "Plugin not found"}}
        
        # 스키마 기반 검증
        schema = await generate_config_schema(plugin_id, plugin_info)
        
        for field in schema.fields:
            field_name = field.name
            field_value = values.get(field_name)
            
            # 필수 필드 검증
            if field.required and (field_value is None or field_value == ""):
                errors[field_name] = f"{field.label} is required"
                continue
            
            # 타입별 검증
            if field_value is not None:
                if field.type == "number":
                    try:
                        num_value = float(field_value)
                        if field.validation:
                            if "min" in field.validation and num_value < field.validation["min"]:
                                errors[field_name] = f"Value must be at least {field.validation['min']}"
                            if "max" in field.validation and num_value > field.validation["max"]:
                                errors[field_name] = f"Value must be at most {field.validation['max']}"
                    except (ValueError, TypeError):
                        errors[field_name] = "Invalid number format"
                
                elif field.type == "email":
                    import re
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    if not re.match(email_pattern, str(field_value)):
                        errors[field_name] = "Invalid email format"
                
                elif field.type == "url":
                    import re
                    url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
                    if not re.match(url_pattern, str(field_value)):
                        errors[field_name] = "Invalid URL format"
        
        # 플러그인별 커스텀 검증
        custom_errors = await validate_plugin_specific_config(plugin_id, plugin_info, values)
        errors.update(custom_errors)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Config validation error for plugin {plugin_id}: {str(e)}")
        return {
            "valid": False,
            "errors": {"general": "Validation failed due to internal error"}
        }


async def validate_plugin_specific_config(
    plugin_id: str, 
    plugin_info: Dict[str, Any], 
    values: Dict[str, Any]
) -> Dict[str, str]:
    """플러그인별 특화 검증"""
    errors = {}
    plugin_type = plugin_info.get("agent_type", "unknown")
    
    if plugin_type == "vector_search":
        # Milvus 컬렉션 존재 확인
        collection_name = values.get("collection_name")
        if collection_name:
            # TODO: Milvus 연결 확인 및 컬렉션 존재 여부 검증
            pass
    
    elif plugin_type == "local_data":
        # 데이터 경로 존재 확인
        import os
        data_path = values.get("data_path")
        if data_path and not os.path.exists(data_path):
            errors["data_path"] = "Data path does not exist"
    
    return errors


async def save_config_history(plugin_id: str, values: Dict[str, Any], user_id: str):
    """설정 히스토리 저장 (백그라운드 작업)"""
    try:
        integration_service = await get_plugin_integration_service()
        
        await integration_service.enhanced_agent_manager.save_config_history(
            plugin_id=plugin_id,
            values=values,
            user_id=user_id,
            description=f"Configuration updated by user {user_id}"
        )
        
    except Exception as e:
        logger.error(f"Failed to save config history for plugin {plugin_id}: {str(e)}")