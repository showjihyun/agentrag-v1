"""Custom Tools API endpoints."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime
import httpx

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
from backend.db.models.custom_tools import CustomTool, CustomToolUsage

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/custom-tools",
    tags=["custom-tools"],
)


# Pydantic Models
class CustomToolCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category: str = Field(default="custom")
    icon: str = Field(default="🔧")
    method: str = Field(default="GET")
    url: str = Field(..., min_length=1)
    headers: dict = Field(default_factory=dict)
    query_params: dict = Field(default_factory=dict)
    body_template: dict = Field(default_factory=dict)
    parameters: list = Field(default_factory=list)
    outputs: list = Field(default_factory=list)
    requires_auth: bool = False
    auth_type: Optional[str] = None
    auth_config: dict = Field(default_factory=dict)
    test_data: dict = Field(default_factory=dict)


class CustomToolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    icon: Optional[str] = None
    method: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[dict] = None
    query_params: Optional[dict] = None
    body_template: Optional[dict] = None
    parameters: Optional[list] = None
    outputs: Optional[list] = None
    requires_auth: Optional[bool] = None
    auth_type: Optional[str] = None
    auth_config: Optional[dict] = None
    test_data: Optional[dict] = None
    is_public: Optional[bool] = None
    is_marketplace: Optional[bool] = None


class CustomToolTest(BaseModel):
    parameters: dict = Field(..., description="Test parameters")


@router.get("")
async def list_custom_tools(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    is_public: Optional[bool] = Query(None),
    is_marketplace: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List custom tools."""
    try:
        query = db.query(CustomTool)
        
        # Filter by user's tools or public tools
        if is_public is not None:
            query = query.filter(CustomTool.is_public == is_public)
        else:
            query = query.filter(
                (CustomTool.user_id == current_user.id) | (CustomTool.is_public == True)
            )
        
        if category:
            query = query.filter(CustomTool.category == category)
        
        if is_marketplace is not None:
            query = query.filter(CustomTool.is_marketplace == is_marketplace)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (CustomTool.name.ilike(search_term)) |
                (CustomTool.description.ilike(search_term))
            )
        
        tools = query.order_by(CustomTool.created_at.desc()).all()
        
        return {
            "tools": [
                {
                    "id": str(tool.id),
                    "name": tool.name,
                    "description": tool.description,
                    "category": tool.category,
                    "icon": tool.icon,
                    "requires_auth": tool.requires_auth,
                    "is_public": tool.is_public,
                    "is_marketplace": tool.is_marketplace,
                    "usage_count": tool.usage_count,
                    "created_at": tool.created_at.isoformat(),
                    "is_owner": tool.user_id == current_user.id,
                }
                for tool in tools
            ],
            "total": len(tools)
        }
    except Exception as e:
        logger.error(f"Failed to list custom tools: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list custom tools"
        )


@router.post("")
async def create_custom_tool(
    data: CustomToolCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new custom tool."""
    try:
        tool = CustomTool(
            user_id=current_user.id,
            name=data.name,
            description=data.description,
            category=data.category,
            icon=data.icon,
            method=data.method,
            url=data.url,
            headers=data.headers,
            query_params=data.query_params,
            body_template=data.body_template,
            parameters=data.parameters,
            outputs=data.outputs,
            requires_auth=data.requires_auth,
            auth_type=data.auth_type,
            auth_config=data.auth_config,
            test_data=data.test_data,
        )
        
        db.add(tool)
        db.commit()
        db.refresh(tool)
        
        logger.info(f"Created custom tool {tool.id} by user {current_user.id}")
        
        return {
            "id": str(tool.id),
            "name": tool.name,
            "description": tool.description,
            "category": tool.category,
            "created_at": tool.created_at.isoformat(),
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create custom tool: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create custom tool"
        )


@router.get("/{tool_id}")
async def get_custom_tool(
    tool_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get custom tool details."""
    try:
        tool = db.query(CustomTool).filter(CustomTool.id == tool_id).first()
        
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tool not found"
            )
        
        # Check access
        if not tool.is_public and str(tool.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return {
            "id": str(tool.id),
            "user_id": str(tool.user_id),
            "name": tool.name,
            "description": tool.description,
            "category": tool.category,
            "icon": tool.icon,
            "method": tool.method,
            "url": tool.url,
            "headers": tool.headers,
            "query_params": tool.query_params,
            "body_template": tool.body_template,
            "parameters": tool.parameters,
            "outputs": tool.outputs,
            "requires_auth": tool.requires_auth,
            "auth_type": tool.auth_type,
            "auth_config": tool.auth_config,
            "is_public": tool.is_public,
            "is_marketplace": tool.is_marketplace,
            "test_data": tool.test_data,
            "last_test_result": tool.last_test_result,
            "last_test_at": tool.last_test_at.isoformat() if tool.last_test_at else None,
            "usage_count": tool.usage_count,
            "created_at": tool.created_at.isoformat(),
            "updated_at": tool.updated_at.isoformat(),
            "is_owner": tool.user_id == current_user.id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get custom tool: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get custom tool"
        )


@router.put("/{tool_id}")
async def update_custom_tool(
    tool_id: str,
    data: CustomToolUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update custom tool."""
    try:
        tool = db.query(CustomTool).filter(CustomTool.id == tool_id).first()
        
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tool not found"
            )
        
        if str(tool.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owner can update tool"
            )
        
        # Update fields
        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(tool, key, value)
        
        tool.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(tool)
        
        logger.info(f"Updated custom tool {tool_id}")
        
        return {"id": str(tool.id), "updated_at": tool.updated_at.isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update custom tool: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update custom tool"
        )


@router.delete("/{tool_id}")
async def delete_custom_tool(
    tool_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete custom tool."""
    try:
        tool = db.query(CustomTool).filter(CustomTool.id == tool_id).first()
        
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tool not found"
            )
        
        if str(tool.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owner can delete tool"
            )
        
        db.delete(tool)
        db.commit()
        
        logger.info(f"Deleted custom tool {tool_id}")
        
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete custom tool: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete custom tool"
        )


@router.post("/{tool_id}/test")
async def test_custom_tool(
    tool_id: str,
    test_data: CustomToolTest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Test custom tool with sample data."""
    try:
        tool = db.query(CustomTool).filter(CustomTool.id == tool_id).first()
        
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tool not found"
            )
        
        # Check access
        if not tool.is_public and str(tool.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Execute tool
        start_time = datetime.utcnow()
        
        try:
            # Build request
            url = tool.url
            headers = tool.headers.copy()
            params = tool.query_params.copy()
            
            # Replace template variables
            for key, value in test_data.parameters.items():
                url = url.replace(f"{{{{{key}}}}}", str(value))
                
                # Replace in headers
                for h_key, h_value in headers.items():
                    if isinstance(h_value, str):
                        headers[h_key] = h_value.replace(f"{{{{{key}}}}}", str(value))
                
                # Replace in params
                for p_key, p_value in params.items():
                    if isinstance(p_value, str):
                        params[p_key] = p_value.replace(f"{{{{{key}}}}}", str(value))
            
            # Make request
            async with httpx.AsyncClient(timeout=30.0) as client:
                if tool.method == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif tool.method == "POST":
                    body = tool.body_template.copy()
                    for key, value in test_data.parameters.items():
                        # Simple template replacement in body
                        body = _replace_in_dict(body, key, value)
                    response = await client.post(url, headers=headers, params=params, json=body)
                elif tool.method == "PUT":
                    body = tool.body_template.copy()
                    for key, value in test_data.parameters.items():
                        body = _replace_in_dict(body, key, value)
                    response = await client.put(url, headers=headers, params=params, json=body)
                elif tool.method == "DELETE":
                    response = await client.delete(url, headers=headers, params=params)
                else:
                    raise ValueError(f"Unsupported method: {tool.method}")
            
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Parse response
            try:
                result_data = response.json()
            except:
                result_data = {"text": response.text}
            
            success = response.status_code < 400
            
            # Save test result
            tool.last_test_result = {
                "success": success,
                "status_code": response.status_code,
                "data": result_data,
                "duration_ms": duration_ms,
            }
            tool.last_test_at = datetime.utcnow()
            db.commit()
            
            # Log usage
            usage = CustomToolUsage(
                tool_id=tool.id,
                user_id=current_user.id,
                input_data=test_data.parameters,
                output_data=result_data,
                success=success,
                duration_ms=duration_ms,
            )
            db.add(usage)
            db.commit()
            
            return {
                "success": success,
                "status_code": response.status_code,
                "data": result_data,
                "duration_ms": duration_ms,
            }
            
        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Request timeout",
                "duration_ms": 30000,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "duration_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000),
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test custom tool: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test custom tool"
        )


@router.post("/{tool_id}/clone")
async def clone_custom_tool(
    tool_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Clone a custom tool."""
    try:
        original = db.query(CustomTool).filter(CustomTool.id == tool_id).first()
        
        if not original:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tool not found"
            )
        
        if not original.is_public and original.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot clone private tool"
            )
        
        # Create clone
        clone = CustomTool(
            user_id=current_user.id,
            name=f"{original.name} (Copy)",
            description=original.description,
            category=original.category,
            icon=original.icon,
            method=original.method,
            url=original.url,
            headers=original.headers,
            query_params=original.query_params,
            body_template=original.body_template,
            parameters=original.parameters,
            outputs=original.outputs,
            requires_auth=original.requires_auth,
            auth_type=original.auth_type,
            auth_config=original.auth_config,
            test_data=original.test_data,
            is_public=False,
        )
        
        db.add(clone)
        db.commit()
        db.refresh(clone)
        
        return {"id": str(clone.id), "name": clone.name}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to clone custom tool: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clone custom tool"
        )


@router.get("/{tool_id}/usage")
async def get_tool_usage(
    tool_id: str,
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get tool usage history."""
    try:
        tool = db.query(CustomTool).filter(CustomTool.id == tool_id).first()
        
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tool not found"
            )
        
        if str(tool.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        usage = db.query(CustomToolUsage).filter(
            CustomToolUsage.tool_id == tool_id
        ).order_by(
            CustomToolUsage.executed_at.desc()
        ).limit(limit).all()
        
        return {
            "usage": [
                {
                    "id": str(u.id),
                    "input_data": u.input_data,
                    "output_data": u.output_data,
                    "success": u.success,
                    "error_message": u.error_message,
                    "duration_ms": u.duration_ms,
                    "executed_at": u.executed_at.isoformat(),
                }
                for u in usage
            ],
            "total": len(usage)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tool usage: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tool usage"
        )


# Marketplace endpoints
@router.get("/marketplace/featured")
async def get_featured_tools(
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get featured marketplace tools."""
    from sqlalchemy import func
    from backend.db.models.custom_tools import CustomToolRating
    
    try:
        # Get tools with ratings
        tools = db.query(
            CustomTool,
            func.avg(CustomToolRating.rating).label('avg_rating'),
            func.count(CustomToolRating.id).label('rating_count')
        ).outerjoin(
            CustomToolRating, CustomTool.id == CustomToolRating.tool_id
        ).filter(
            CustomTool.is_marketplace == True
        ).group_by(
            CustomTool.id
        ).order_by(
            func.coalesce(func.avg(CustomToolRating.rating), 0).desc(),
            CustomTool.usage_count.desc()
        ).limit(limit).all()
        
        return {
            "tools": [
                {
                    "id": str(tool.id),
                    "name": tool.name,
                    "description": tool.description,
                    "category": tool.category,
                    "icon": tool.icon,
                    "usage_count": tool.usage_count,
                    "avg_rating": float(avg_rating) if avg_rating else 0,
                    "rating_count": rating_count,
                    "created_at": tool.created_at.isoformat(),
                }
                for tool, avg_rating, rating_count in tools
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get featured tools: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get featured tools"
        )


@router.post("/{tool_id}/rate")
async def rate_tool(
    tool_id: str,
    rating: int = Query(..., ge=1, le=5),
    review: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rate a marketplace tool."""
    from backend.db.models.custom_tools import CustomToolRating
    
    try:
        tool = db.query(CustomTool).filter(CustomTool.id == tool_id).first()
        
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tool not found"
            )
        
        if not tool.is_marketplace:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only rate marketplace tools"
            )
        
        # Check if already rated
        existing = db.query(CustomToolRating).filter(
            CustomToolRating.tool_id == tool_id,
            CustomToolRating.user_id == current_user.id
        ).first()
        
        if existing:
            existing.rating = rating
            existing.review = review
            existing.updated_at = datetime.utcnow()
        else:
            new_rating = CustomToolRating(
                tool_id=tool.id,
                user_id=current_user.id,
                rating=rating,
                review=review
            )
            db.add(new_rating)
        
        db.commit()
        
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to rate tool: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rate tool"
        )


@router.get("/{tool_id}/ratings")
async def get_tool_ratings(
    tool_id: str,
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get tool ratings and reviews."""
    from backend.db.models.custom_tools import CustomToolRating
    from backend.db.models.user import User as UserModel
    
    try:
        ratings = db.query(CustomToolRating, UserModel).join(
            UserModel, CustomToolRating.user_id == UserModel.id
        ).filter(
            CustomToolRating.tool_id == tool_id
        ).order_by(
            CustomToolRating.created_at.desc()
        ).limit(limit).all()
        
        return {
            "ratings": [
                {
                    "id": str(rating.id),
                    "rating": rating.rating,
                    "review": rating.review,
                    "user": {
                        "id": str(user.id),
                        "username": user.username,
                    },
                    "created_at": rating.created_at.isoformat(),
                }
                for rating, user in ratings
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get tool ratings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tool ratings"
        )


def _replace_in_dict(data: dict, key: str, value) -> dict:
    """Recursively replace template variables in dict."""
    result = {}
    for k, v in data.items():
        if isinstance(v, str):
            result[k] = v.replace(f"{{{{{key}}}}}", str(value))
        elif isinstance(v, dict):
            result[k] = _replace_in_dict(v, key, value)
        elif isinstance(v, list):
            result[k] = [
                _replace_in_dict(item, key, value) if isinstance(item, dict)
                else item.replace(f"{{{{{key}}}}}", str(value)) if isinstance(item, str)
                else item
                for item in v
            ]
        else:
            result[k] = v
    return result
