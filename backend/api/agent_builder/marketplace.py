"""
Marketplace API

Provides endpoints for browsing, installing, and managing
marketplace items (agents, workflows, templates, tools).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from backend.core.dependencies import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/marketplace", tags=["Marketplace"])


# Models
class MarketplaceItem(BaseModel):
    id: str
    name: str
    description: str
    category: str  # agents, workflows, templates, tools
    author: str
    rating: float
    downloads: int
    price: float
    is_featured: bool
    tags: List[str]
    preview_image: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


class MarketplaceItemDetail(MarketplaceItem):
    long_description: str
    version: str
    changelog: List[str]
    requirements: List[str]
    screenshots: List[str]
    reviews: List[dict]
    configuration: dict


# Sample marketplace data
SAMPLE_ITEMS = [
    {
        "id": "item-1",
        "name": "Customer Support Agent",
        "description": "Pre-trained agent for customer support with FAQ handling",
        "category": "agents",
        "author": "AgenticRAG Team",
        "rating": 4.8,
        "downloads": 1250,
        "price": 0,
        "is_featured": True,
        "tags": ["customer-support", "faq", "chatbot"],
        "created_at": "2024-01-15T10:00:00Z"
    },
    {
        "id": "item-2",
        "name": "Data Analysis Workflow",
        "description": "Complete workflow for data analysis and visualization",
        "category": "workflows",
        "author": "DataPro",
        "rating": 4.6,
        "downloads": 890,
        "price": 29.99,
        "is_featured": True,
        "tags": ["data-analysis", "visualization", "reporting"],
        "created_at": "2024-02-01T14:30:00Z"
    },
    {
        "id": "item-3",
        "name": "Content Writer Template",
        "description": "Template for creating high-quality content",
        "category": "templates",
        "author": "ContentMaster",
        "rating": 4.9,
        "downloads": 2100,
        "price": 0,
        "is_featured": True,
        "tags": ["content", "writing", "seo"],
        "created_at": "2024-01-20T09:15:00Z"
    },
    {
        "id": "item-4",
        "name": "Code Review Agent",
        "description": "Automated code review with best practices",
        "category": "agents",
        "author": "DevTools Inc",
        "rating": 4.7,
        "downloads": 756,
        "price": 49.99,
        "is_featured": False,
        "tags": ["code-review", "development", "quality"],
        "created_at": "2024-02-10T11:20:00Z"
    },
    {
        "id": "item-5",
        "name": "Email Automation Workflow",
        "description": "Automate email responses and follow-ups",
        "category": "workflows",
        "author": "AutoMate",
        "rating": 4.5,
        "downloads": 634,
        "price": 19.99,
        "is_featured": False,
        "tags": ["email", "automation", "productivity"],
        "created_at": "2024-02-15T16:45:00Z"
    },
    {
        "id": "item-6",
        "name": "SQL Query Tool",
        "description": "Natural language to SQL query converter",
        "category": "tools",
        "author": "QueryMaster",
        "rating": 4.8,
        "downloads": 1450,
        "price": 0,
        "is_featured": False,
        "tags": ["sql", "database", "query"],
        "created_at": "2024-01-25T13:00:00Z"
    },
]


@router.get("/items", response_model=List[MarketplaceItem])
async def get_marketplace_items(
    category: Optional[str] = None,
    sort_by: str = Query("popular", pattern="^(popular|recent|rating|downloads)$"),
    search: Optional[str] = None,
    featured_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get marketplace items with filtering and sorting
    """
    try:
        items = SAMPLE_ITEMS.copy()
        
        # Filter by category
        if category and category != "all":
            items = [item for item in items if item["category"] == category]
        
        # Filter by featured
        if featured_only:
            items = [item for item in items if item["is_featured"]]
        
        # Search
        if search:
            search_lower = search.lower()
            items = [
                item for item in items
                if search_lower in item["name"].lower()
                or search_lower in item["description"].lower()
                or any(search_lower in tag.lower() for tag in item["tags"])
            ]
        
        # Sort
        if sort_by == "popular":
            items.sort(key=lambda x: x["downloads"], reverse=True)
        elif sort_by == "recent":
            items.sort(key=lambda x: x["created_at"], reverse=True)
        elif sort_by == "rating":
            items.sort(key=lambda x: x["rating"], reverse=True)
        elif sort_by == "downloads":
            items.sort(key=lambda x: x["downloads"], reverse=True)
        
        return [MarketplaceItem(**item) for item in items]
        
    except Exception as e:
        logger.error(f"Failed to get marketplace items: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/items/{item_id}", response_model=MarketplaceItemDetail)
async def get_marketplace_item(
    item_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a marketplace item
    """
    try:
        # Find item
        item = next((item for item in SAMPLE_ITEMS if item["id"] == item_id), None)
        
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Add detailed information
        detail = {
            **item,
            "long_description": f"Detailed description of {item['name']}. This is a comprehensive solution that provides...",
            "version": "1.2.0",
            "changelog": [
                "v1.2.0: Added new features and improvements",
                "v1.1.0: Bug fixes and performance enhancements",
                "v1.0.0: Initial release"
            ],
            "requirements": ["Python 3.10+", "FastAPI", "LangChain"],
            "screenshots": [],
            "reviews": [
                {
                    "user": "user1",
                    "rating": 5,
                    "comment": "Excellent tool, saved me hours of work!",
                    "date": "2024-02-20"
                },
                {
                    "user": "user2",
                    "rating": 4,
                    "comment": "Very useful, minor issues but overall great",
                    "date": "2024-02-18"
                }
            ],
            "configuration": {
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }
        
        return MarketplaceItemDetail(**detail)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get marketplace item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/items/{item_id}/install")
async def install_marketplace_item(
    item_id: str,
    db: Session = Depends(get_db)
):
    """
    Install a marketplace item
    """
    try:
        # Find item
        item = next((item for item in SAMPLE_ITEMS if item["id"] == item_id), None)
        
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # In production, this would:
        # 1. Download the item
        # 2. Validate it
        # 3. Install it to user's workspace
        # 4. Update download count
        
        return {
            "success": True,
            "message": f"Successfully installed {item['name']}",
            "item_id": item_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to install marketplace item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_marketplace_categories(
    db: Session = Depends(get_db)
):
    """
    Get available marketplace categories
    """
    return {
        "categories": [
            {"id": "agents", "name": "Agents", "count": 2},
            {"id": "workflows", "name": "Workflows", "count": 2},
            {"id": "templates", "name": "Templates", "count": 1},
            {"id": "tools", "name": "Tools", "count": 1},
        ]
    }


@router.get("/featured")
async def get_featured_items(
    limit: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db)
):
    """
    Get featured marketplace items
    """
    try:
        featured = [item for item in SAMPLE_ITEMS if item["is_featured"]]
        featured.sort(key=lambda x: x["downloads"], reverse=True)
        
        return {
            "items": [MarketplaceItem(**item) for item in featured[:limit]]
        }
        
    except Exception as e:
        logger.error(f"Failed to get featured items: {e}")
        raise HTTPException(status_code=500, detail=str(e))
