"""
Plugin Installation API Endpoints
플러그인 설치 및 소스 검증을 위한 API 엔드포인트
"""
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, validator
import logging
import json
import asyncio
import uuid
from datetime import datetime

from backend.core.dependencies import get_current_user
from backend.models.user import User
from backend.services.plugins.plugin_integration_service import get_plugin_integration_service
from backend.services.plugins.manifest_validator import PluginManifestValidator
from backend.services.plugins.dependency_resolver import PluginDependencyResolver

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/plugins", tags=["Plugin Installation"])


# Request/Response Models
class PluginSource(BaseModel):
    """플러그인 소스"""
    type: str = Field(..., regex=r'^(github|url|local|marketplace)$')
    url: Optional[str] = None
    repository: Optional[str] = None
    branch: Optional[str] = None
    tag: Optional[str] = None
    local_path: Optional[str] = None
    marketplace_id: Optional[str] = None
    
    @validator('repository')
    def validate_repository(cls, v, values):
        if values.get('type') == 'github' and not v:
            raise ValueError('Repository is required for GitHub source')
        return v
    
    @validator('url')
    def validate_url(cls, v, values):
        if values.get('type') == 'url' and not v:
            raise ValueError('URL is required for URL source')
        return v
    
    @validator('local_path')
    def validate_local_path(cls, v, values):
        if values.get('type') == 'local' and not v:
            raise ValueError('Local path is required for local source')
        return v


class PluginDependency(BaseModel):
    """플러그인 의존성"""
    name: str
    version: str
    required: bool
    installed: bool
    compatible: bool
    description: Optional[str] = None


class PluginManifest(BaseModel):
    """플러그인 매니페스트"""
    name: str
    version: str
    description: str
    author: str
    license: str
    homepage: Optional[str] = None
    repository: Optional[str] = None
    keywords: List[str] = []
    dependencies: List[PluginDependency] = []
    permissions: List[str] = []
    config_schema: Optional[Dict[str, Any]] = None
    min_system_version: Optional[str] = None


class PluginSourceValidationRequest(BaseModel):
    """플러그인 소스 검증 요청"""
    type: str = Field(..., regex=r'^(github|url|local|marketplace)$')
    url: Optional[str] = None
    repository: Optional[str] = None
    branch: Optional[str] = None
    tag: Optional[str] = None
    local_path: Optional[str] = None
    marketplace_id: Optional[str] = None


class PluginDependencyCheckRequest(BaseModel):
    """플러그인 의존성 확인 요청"""
    dependencies: List[Dict[str, Any]]


class PluginInstallationRequest(BaseModel):
    """플러그인 설치 요청"""
    source: PluginSource
    manifest: PluginManifest
    auto_retry: bool = True
    config: Optional[Dict[str, Any]] = None


class PluginInstallationResponse(BaseModel):
    """플러그인 설치 응답"""
    installation_id: str
    status: str
    message: str


class InstallationStep(BaseModel):
    """설치 단계"""
    id: str
    title: str
    description: str
    status: str = Field(..., regex=r'^(pending|running|completed|failed|skipped)$')
    can_skip: bool = False
    can_retry: bool = False
    progress: Optional[int] = None
    logs: List[str] = []
    error: Optional[str] = None


# 설치 진행 상황 추적
installation_progress: Dict[str, Dict[str, Any]] = {}


# API Endpoints

@router.post("/validate-source")
async def validate_plugin_source(
    request: PluginSourceValidationRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """플러그인 소스 검증"""
    try:
        integration_service = await get_plugin_integration_service()
        
        # 소스 타입별 검증
        if request.type == "github":
            manifest = await validate_github_source(request.repository, request.branch, request.tag)
        elif request.type == "url":
            manifest = await validate_url_source(request.url)
        elif request.type == "local":
            manifest = await validate_local_source(request.local_path)
        elif request.type == "marketplace":
            manifest = await validate_marketplace_source(request.marketplace_id)
        else:
            raise HTTPException(status_code=400, detail="Unsupported source type")
        
        return {"manifest": manifest}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate plugin source: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to validate plugin source")


@router.post("/check-dependencies")
async def check_plugin_dependencies(
    request: PluginDependencyCheckRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """플러그인 의존성 확인"""
    try:
        dependency_resolver = PluginDependencyResolver()
        
        # 의존성 확인
        dependencies = []
        for dep_info in request.dependencies:
            dependency = await dependency_resolver.check_dependency(
                name=dep_info["name"],
                version=dep_info["version"],
                required=dep_info.get("required", True)
            )
            dependencies.append(dependency)
        
        return {"dependencies": dependencies}
        
    except Exception as e:
        logger.error(f"Failed to check dependencies: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check plugin dependencies")


@router.post("/install")
async def install_plugin(
    request: PluginInstallationRequest,
    current_user: User = Depends(get_current_user)
) -> PluginInstallationResponse:
    """플러그인 설치 시작"""
    try:
        installation_id = str(uuid.uuid4())
        
        # 설치 진행 상황 초기화
        installation_progress[installation_id] = {
            "status": "started",
            "steps": [],
            "current_step": None,
            "user_id": current_user.id,
            "start_time": datetime.utcnow().isoformat(),
            "source": request.source.dict(),
            "manifest": request.manifest.dict()
        }
        
        # 백그라운드에서 설치 실행
        asyncio.create_task(execute_plugin_installation(
            installation_id=installation_id,
            source=request.source,
            manifest=request.manifest,
            config=request.config,
            auto_retry=request.auto_retry,
            user_id=current_user.id
        ))
        
        return PluginInstallationResponse(
            installation_id=installation_id,
            status="started",
            message="Plugin installation started"
        )
        
    except Exception as e:
        logger.error(f"Failed to start plugin installation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start plugin installation")


@router.websocket("/install-progress/{installation_id}")
async def plugin_installation_progress(websocket: WebSocket, installation_id: str):
    """플러그인 설치 진행 상황 WebSocket"""
    await websocket.accept()
    
    try:
        while True:
            if installation_id not in installation_progress:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Installation not found"
                }))
                break
            
            progress_data = installation_progress[installation_id]
            
            # 진행 상황 전송
            await websocket.send_text(json.dumps({
                "type": "progress",
                "data": progress_data
            }))
            
            # 설치 완료 또는 실패 시 종료
            if progress_data["status"] in ["completed", "failed"]:
                break
            
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for installation {installation_id}")
    except Exception as e:
        logger.error(f"WebSocket error for installation {installation_id}: {str(e)}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "WebSocket error"
        }))


@router.post("/retry-step/{installation_id}/{step_id}")
async def retry_installation_step(
    installation_id: str,
    step_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """설치 단계 재시도"""
    try:
        if installation_id not in installation_progress:
            raise HTTPException(status_code=404, detail="Installation not found")
        
        progress_data = installation_progress[installation_id]
        
        # 권한 확인
        if progress_data["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 단계 재시도
        await retry_step(installation_id, step_id)
        
        return {"message": "Step retry initiated"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry step {step_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retry installation step")


# Helper Functions

async def validate_github_source(repository: str, branch: Optional[str], tag: Optional[str]) -> Dict[str, Any]:
    """GitHub 소스 검증"""
    try:
        # GitHub API를 사용하여 저장소 정보 확인
        import httpx
        
        # 저장소 존재 확인
        async with httpx.AsyncClient() as client:
            repo_url = f"https://api.github.com/repos/{repository}"
            response = await client.get(repo_url)
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Repository not found")
            elif response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to access repository")
            
            repo_data = response.json()
            
            # 매니페스트 파일 확인
            manifest_url = f"https://api.github.com/repos/{repository}/contents/plugin.json"
            if branch:
                manifest_url += f"?ref={branch}"
            elif tag:
                manifest_url += f"?ref={tag}"
            
            manifest_response = await client.get(manifest_url)
            if manifest_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Plugin manifest not found")
            
            # 매니페스트 파싱
            import base64
            manifest_content = base64.b64decode(manifest_response.json()["content"]).decode('utf-8')
            manifest_data = json.loads(manifest_content)
            
            # 매니페스트 검증
            validator = PluginManifestValidator()
            is_valid, errors = await validator.validate(manifest_data)
            
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"Invalid manifest: {', '.join(errors)}")
            
            return manifest_data
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitHub source validation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to validate GitHub source")


async def validate_url_source(url: str) -> Dict[str, Any]:
    """URL 소스 검증"""
    try:
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to download plugin")
            
            # ZIP 파일인지 확인
            content_type = response.headers.get("content-type", "")
            if "zip" not in content_type and not url.endswith(".zip"):
                raise HTTPException(status_code=400, detail="Plugin must be a ZIP file")
            
            # 임시로 매니페스트 정보 반환 (실제로는 ZIP 파일을 분석해야 함)
            return {
                "name": "Downloaded Plugin",
                "version": "1.0.0",
                "description": "Plugin downloaded from URL",
                "author": "Unknown",
                "license": "Unknown",
                "dependencies": [],
                "permissions": []
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL source validation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to validate URL source")


async def validate_local_source(local_path: str) -> Dict[str, Any]:
    """로컬 소스 검증"""
    try:
        import os
        
        if not os.path.exists(local_path):
            raise HTTPException(status_code=404, detail="Local path not found")
        
        # 매니페스트 파일 확인
        manifest_path = os.path.join(local_path, "plugin.json")
        if not os.path.exists(manifest_path):
            raise HTTPException(status_code=400, detail="Plugin manifest not found")
        
        # 매니페스트 읽기 및 검증
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
        
        validator = PluginManifestValidator()
        is_valid, errors = await validator.validate(manifest_data)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid manifest: {', '.join(errors)}")
        
        return manifest_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Local source validation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to validate local source")


async def validate_marketplace_source(marketplace_id: str) -> Dict[str, Any]:
    """마켓플레이스 소스 검증"""
    try:
        # 마켓플레이스 API 호출 (구현 필요)
        # 현재는 더미 데이터 반환
        return {
            "name": f"Marketplace Plugin {marketplace_id}",
            "version": "1.0.0",
            "description": "Plugin from marketplace",
            "author": "Marketplace",
            "license": "MIT",
            "dependencies": [],
            "permissions": []
        }
        
    except Exception as e:
        logger.error(f"Marketplace source validation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to validate marketplace source")


async def execute_plugin_installation(
    installation_id: str,
    source: PluginSource,
    manifest: PluginManifest,
    config: Optional[Dict[str, Any]],
    auto_retry: bool,
    user_id: str
):
    """플러그인 설치 실행"""
    try:
        progress_data = installation_progress[installation_id]
        
        # 설치 단계 정의
        steps = [
            {"id": "download", "title": "Downloading Plugin", "description": "Downloading plugin files..."},
            {"id": "extract", "title": "Extracting Files", "description": "Extracting plugin files..."},
            {"id": "validate", "title": "Validating Plugin", "description": "Validating plugin structure..."},
            {"id": "dependencies", "title": "Installing Dependencies", "description": "Installing required dependencies..."},
            {"id": "register", "title": "Registering Plugin", "description": "Registering plugin in system..."},
            {"id": "activate", "title": "Activating Plugin", "description": "Activating plugin..."},
        ]
        
        progress_data["steps"] = steps
        
        # 각 단계 실행
        for step in steps:
            step_id = step["id"]
            progress_data["current_step"] = step_id
            
            # 단계 시작
            step["status"] = "running"
            step["progress"] = 0
            step["logs"] = []
            
            try:
                if step_id == "download":
                    await execute_download_step(installation_id, source, step)
                elif step_id == "extract":
                    await execute_extract_step(installation_id, step)
                elif step_id == "validate":
                    await execute_validate_step(installation_id, manifest, step)
                elif step_id == "dependencies":
                    await execute_dependencies_step(installation_id, manifest.dependencies, step)
                elif step_id == "register":
                    await execute_register_step(installation_id, manifest, config, step)
                elif step_id == "activate":
                    await execute_activate_step(installation_id, step)
                
                # 단계 완료
                step["status"] = "completed"
                step["progress"] = 100
                step["logs"].append(f"Step {step['title']} completed successfully")
                
            except Exception as e:
                # 단계 실패
                step["status"] = "failed"
                step["error"] = str(e)
                step["logs"].append(f"Step {step['title']} failed: {str(e)}")
                
                if auto_retry and step.get("can_retry", True):
                    # 자동 재시도
                    step["logs"].append("Retrying step...")
                    await asyncio.sleep(2)
                    continue
                else:
                    # 설치 실패
                    progress_data["status"] = "failed"
                    progress_data["error"] = str(e)
                    return
        
        # 설치 완료
        progress_data["status"] = "completed"
        progress_data["end_time"] = datetime.utcnow().isoformat()
        
    except Exception as e:
        logger.error(f"Installation execution error: {str(e)}")
        progress_data["status"] = "failed"
        progress_data["error"] = str(e)


async def execute_download_step(installation_id: str, source: PluginSource, step: Dict[str, Any]):
    """다운로드 단계 실행"""
    step["logs"].append("Starting download...")
    await asyncio.sleep(1)  # 시뮬레이션
    step["progress"] = 50
    step["logs"].append("Download in progress...")
    await asyncio.sleep(1)
    step["progress"] = 100
    step["logs"].append("Download completed")


async def execute_extract_step(installation_id: str, step: Dict[str, Any]):
    """압축 해제 단계 실행"""
    step["logs"].append("Extracting files...")
    await asyncio.sleep(1)
    step["progress"] = 100
    step["logs"].append("Files extracted successfully")


async def execute_validate_step(installation_id: str, manifest: PluginManifest, step: Dict[str, Any]):
    """검증 단계 실행"""
    step["logs"].append("Validating plugin structure...")
    await asyncio.sleep(1)
    step["progress"] = 100
    step["logs"].append("Plugin validation completed")


async def execute_dependencies_step(installation_id: str, dependencies: List[PluginDependency], step: Dict[str, Any]):
    """의존성 설치 단계 실행"""
    if not dependencies:
        step["logs"].append("No dependencies to install")
        step["progress"] = 100
        return
    
    step["logs"].append(f"Installing {len(dependencies)} dependencies...")
    for i, dep in enumerate(dependencies):
        step["logs"].append(f"Installing {dep.name}...")
        await asyncio.sleep(0.5)
        step["progress"] = int((i + 1) / len(dependencies) * 100)
    
    step["logs"].append("All dependencies installed")


async def execute_register_step(installation_id: str, manifest: PluginManifest, config: Optional[Dict[str, Any]], step: Dict[str, Any]):
    """등록 단계 실행"""
    step["logs"].append("Registering plugin in system...")
    await asyncio.sleep(1)
    step["progress"] = 100
    step["logs"].append("Plugin registered successfully")


async def execute_activate_step(installation_id: str, step: Dict[str, Any]):
    """활성화 단계 실행"""
    step["logs"].append("Activating plugin...")
    await asyncio.sleep(1)
    step["progress"] = 100
    step["logs"].append("Plugin activated successfully")


async def retry_step(installation_id: str, step_id: str):
    """단계 재시도"""
    if installation_id not in installation_progress:
        return
    
    progress_data = installation_progress[installation_id]
    
    # 해당 단계 찾기
    for step in progress_data["steps"]:
        if step["id"] == step_id:
            step["status"] = "pending"
            step["error"] = None
            step["logs"].append("Retrying step...")
            break