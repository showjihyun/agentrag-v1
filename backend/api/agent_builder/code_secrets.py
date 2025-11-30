"""
Code Secrets Management API endpoints.
Phase 4: 시크릿 관리
"""
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.db.database import get_db

router = APIRouter(prefix="/api/workflow", tags=["code-secrets"])


# ============== In-Memory Storage (Demo) ==============
# 실제 구현에서는 암호화된 DB 저장 필요
user_secrets: Dict[str, List[Dict[str, Any]]] = {}


# ============== Request/Response Models ==============

class SecretCreate(BaseModel):
    """시크릿 생성 요청."""
    name: str = Field(..., pattern=r'^[A-Z][A-Z0-9_]*$')
    value: str
    type: str = Field(default="string")  # string, password, api_key, json
    environment: str = Field(default="all")  # dev, staging, prod, all


class SecretResponse(BaseModel):
    """시크릿 응답."""
    id: str
    name: str
    type: str
    environment: str
    maskedValue: str
    lastUsed: Optional[str] = None
    createdAt: str


class SecretsListResponse(BaseModel):
    """시크릿 목록 응답."""
    secrets: List[SecretResponse] = Field(default_factory=list)


# ============== Helper Functions ==============

def mask_value(value: str, secret_type: str) -> str:
    """값 마스킹."""
    if secret_type == "password":
        return "********"
    elif len(value) <= 4:
        return "****"
    else:
        return f"****{value[-4:]}"


def get_user_secrets(user_id: str) -> List[Dict[str, Any]]:
    """사용자 시크릿 조회."""
    return user_secrets.get(user_id, [])


def save_user_secret(user_id: str, secret: Dict[str, Any]):
    """사용자 시크릿 저장."""
    if user_id not in user_secrets:
        user_secrets[user_id] = []
    user_secrets[user_id].append(secret)


# ============== API Endpoints ==============

@router.get("/secrets", response_model=SecretsListResponse)
async def list_secrets(
    current_user: User = Depends(get_current_user),
) -> SecretsListResponse:
    """사용자 시크릿 목록 조회."""
    secrets = get_user_secrets(str(current_user.id))
    
    return SecretsListResponse(
        secrets=[
            SecretResponse(
                id=s["id"],
                name=s["name"],
                type=s["type"],
                environment=s["environment"],
                maskedValue=mask_value(s["value"], s["type"]),
                lastUsed=s.get("last_used"),
                createdAt=s["created_at"],
            )
            for s in secrets
        ]
    )


@router.post("/secrets", response_model=SecretResponse)
async def create_secret(
    request: SecretCreate,
    current_user: User = Depends(get_current_user),
) -> SecretResponse:
    """시크릿 생성."""
    user_id = str(current_user.id)
    
    # 중복 체크
    existing = get_user_secrets(user_id)
    if any(s["name"] == request.name for s in existing):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Secret '{request.name}' already exists"
        )
    
    secret_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    secret = {
        "id": secret_id,
        "name": request.name,
        "value": request.value,  # 실제로는 암호화 필요
        "type": request.type,
        "environment": request.environment,
        "created_at": now,
    }
    
    save_user_secret(user_id, secret)
    
    return SecretResponse(
        id=secret_id,
        name=request.name,
        type=request.type,
        environment=request.environment,
        maskedValue=mask_value(request.value, request.type),
        createdAt=now,
    )


@router.delete("/secrets/{secret_id}")
async def delete_secret(
    secret_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """시크릿 삭제."""
    user_id = str(current_user.id)
    
    if user_id in user_secrets:
        user_secrets[user_id] = [
            s for s in user_secrets[user_id] if s["id"] != secret_id
        ]
    
    return {"message": "Secret deleted successfully"}


@router.get("/secrets/{secret_name}/value")
async def get_secret_value(
    secret_name: str,
    environment: str = "all",
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    시크릿 값 조회 (코드 실행 시 사용).
    실제 값을 반환하므로 보안 주의 필요.
    """
    user_id = str(current_user.id)
    secrets = get_user_secrets(user_id)
    
    for secret in secrets:
        if secret["name"] == secret_name:
            if secret["environment"] in (environment, "all"):
                # 마지막 사용 시간 업데이트
                secret["last_used"] = datetime.utcnow().isoformat()
                return {"value": secret["value"]}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Secret '{secret_name}' not found"
    )
