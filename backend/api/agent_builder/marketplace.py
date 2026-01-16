"""
Marketplace API

Provides endpoints for browsing, installing, and managing
marketplace items (agents, workflows, templates, tools).
All data is stored in the database.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import logging

from backend.db.database import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.db.models.flows import (
    MarketplaceItem,
    Agentflow,
    Chatflow,
    FlowTemplate,
)
from backend.db.models.marketplace import MarketplaceReview

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/marketplace", tags=["Marketplace"])


# ============ Pydantic Models ============

class MarketplaceItemResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    item_type: str
    category: Optional[str]
    author_id: str
    author_name: Optional[str] = None
    rating: float
    rating_count: int
    install_count: int
    price: str
    is_featured: bool
    is_official: bool
    tags: List[str]
    preview_image: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MarketplaceItemDetailResponse(MarketplaceItemResponse):
    long_description: Optional[str] = None
    version: str = "1.0.0"
    changelog: List[str] = []
    requirements: List[str] = []
    screenshots: List[str] = []
    reviews: List[dict] = []
    configuration: dict = {}


class CreateMarketplaceItemRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    item_type: str = Field(..., pattern="^(agentflow|chatflow|workflow|tool|template)$")
    reference_id: str
    reference_type: str
    category: Optional[str] = None
    tags: List[str] = []
    preview_image: Optional[str] = None
    price: str = "free"


class CreateReviewRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


# ============ Helper Functions ============

def marketplace_item_to_response(item: MarketplaceItem, author_name: str = None) -> dict:
    """Convert MarketplaceItem to response dict."""
    return {
        "id": str(item.id),
        "name": item.name,
        "description": item.description,
        "item_type": item.item_type,
        "category": item.category,
        "author_id": str(item.author_id),
        "author_name": author_name,
        "rating": item.rating or 0.0,
        "rating_count": item.rating_count or 0,
        "install_count": item.install_count or 0,
        "price": item.price or "free",
        "is_featured": item.is_featured or False,
        "is_official": item.is_official or False,
        "tags": item.tags or [],
        "preview_image": item.preview_image,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


# ============ Endpoints ============

@router.get("/items", response_model=List[MarketplaceItemResponse])
async def get_marketplace_items(
    category: Optional[str] = Query(None),
    item_type: Optional[str] = Query(None),
    sort_by: str = Query("popular", pattern="^(popular|recent|rating|downloads)$"),
    search: Optional[str] = Query(None),
    featured_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get marketplace items with filtering and sorting."""
    try:
        query = db.query(MarketplaceItem).filter(MarketplaceItem.is_published == True)
        
        # Filter by category
        if category and category != "all":
            query = query.filter(MarketplaceItem.category == category)
        
        # Filter by item type
        if item_type and item_type != "all":
            query = query.filter(MarketplaceItem.item_type == item_type)
        
        # Filter by featured
        if featured_only:
            query = query.filter(MarketplaceItem.is_featured == True)
        
        # Search
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    MarketplaceItem.name.ilike(search_pattern),
                    MarketplaceItem.description.ilike(search_pattern),
                )
            )
        
        # Sort
        if sort_by == "popular":
            query = query.order_by(MarketplaceItem.install_count.desc())
        elif sort_by == "recent":
            query = query.order_by(MarketplaceItem.created_at.desc())
        elif sort_by == "rating":
            query = query.order_by(MarketplaceItem.rating.desc())
        elif sort_by == "downloads":
            query = query.order_by(MarketplaceItem.install_count.desc())
        
        # Pagination
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        
        # Get author names
        author_ids = list(set(item.author_id for item in items))
        authors = db.query(User).filter(User.id.in_(author_ids)).all()
        author_map = {str(a.id): a.username or a.email for a in authors}
        
        return [
            MarketplaceItemResponse(**marketplace_item_to_response(
                item, 
                author_map.get(str(item.author_id))
            ))
            for item in items
        ]
        
    except Exception as e:
        logger.error(f"Failed to get marketplace items: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/items/{item_id}", response_model=MarketplaceItemDetailResponse)
async def get_marketplace_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get detailed information about a marketplace item."""
    try:
        item_uuid = uuid.UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid item ID format")
    
    try:
        item = db.query(MarketplaceItem).filter(
            MarketplaceItem.id == item_uuid,
            MarketplaceItem.is_published == True
        ).first()
        
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Get author
        author = db.query(User).filter(User.id == item.author_id).first()
        author_name = author.username or author.email if author else "Unknown"
        
        # Get reviews
        reviews = db.query(MarketplaceReview).filter(
            MarketplaceReview.item_id == item.id
        ).order_by(MarketplaceReview.created_at.desc()).limit(10).all()
        
        review_list = []
        for review in reviews:
            reviewer = db.query(User).filter(User.id == review.user_id).first()
            review_list.append({
                "user": reviewer.username or "Anonymous" if reviewer else "Anonymous",
                "rating": review.rating,
                "comment": review.comment,
                "date": review.created_at.strftime("%Y-%m-%d"),
            })
        
        # Get configuration from referenced item
        configuration = {}
        if item.reference_type == "agentflow":
            ref = db.query(Agentflow).filter(Agentflow.id == item.reference_id).first()
            if ref:
                configuration = {
                    "orchestration_type": ref.orchestration_type,
                    "supervisor_config": ref.supervisor_config,
                }
        elif item.reference_type == "chatflow":
            ref = db.query(Chatflow).filter(Chatflow.id == item.reference_id).first()
            if ref:
                configuration = {
                    "chat_config": ref.chat_config,
                    "memory_config": ref.memory_config,
                    "rag_config": ref.rag_config,
                }
        
        base_response = marketplace_item_to_response(item, author_name)
        
        return MarketplaceItemDetailResponse(
            **base_response,
            long_description=item.description,
            version="1.0.0",
            changelog=["v1.0.0: Initial release"],
            requirements=[],
            screenshots=[],
            reviews=review_list,
            configuration=configuration,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get marketplace item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/items")
async def create_marketplace_item(
    request: CreateMarketplaceItemRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Publish an item to the marketplace."""
    try:
        ref_uuid = uuid.UUID(request.reference_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid reference ID format")
    
    try:
        # Verify ownership of referenced item
        if request.reference_type == "agentflow":
            ref = db.query(Agentflow).filter(
                Agentflow.id == ref_uuid,
                Agentflow.user_id == current_user.id
            ).first()
        elif request.reference_type == "chatflow":
            ref = db.query(Chatflow).filter(
                Chatflow.id == ref_uuid,
                Chatflow.user_id == current_user.id
            ).first()
        else:
            ref = None
        
        if not ref:
            raise HTTPException(status_code=404, detail="Referenced item not found or access denied")
        
        # Create marketplace item
        item = MarketplaceItem(
            author_id=current_user.id,
            name=request.name,
            description=request.description,
            item_type=request.item_type,
            reference_id=ref_uuid,
            reference_type=request.reference_type,
            category=request.category,
            tags=request.tags,
            preview_image=request.preview_image,
            price=request.price,
            is_published=True,
        )
        
        db.add(item)
        db.commit()
        db.refresh(item)
        
        return {
            "success": True,
            "message": "Item published to marketplace",
            "item_id": str(item.id),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create marketplace item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/items/{item_id}/install")
async def install_marketplace_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Install a marketplace item."""
    try:
        item_uuid = uuid.UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid item ID format")
    
    try:
        item = db.query(MarketplaceItem).filter(
            MarketplaceItem.id == item_uuid,
            MarketplaceItem.is_published == True
        ).first()
        
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Clone the referenced item
        new_item_id = None
        
        if item.reference_type == "agentflow":
            original = db.query(Agentflow).filter(Agentflow.id == item.reference_id).first()
            if original:
                clone = Agentflow(
                    user_id=current_user.id,
                    name=f"{original.name}",
                    description=original.description,
                    orchestration_type=original.orchestration_type,
                    supervisor_config=original.supervisor_config,
                    graph_definition=original.graph_definition,
                    tags=original.tags,
                    is_public=False,
                    is_active=True,
                    version="1.0.0",
                )
                db.add(clone)
                db.flush()
                new_item_id = str(clone.id)
                
        elif item.reference_type == "chatflow":
            original = db.query(Chatflow).filter(Chatflow.id == item.reference_id).first()
            if original:
                clone = Chatflow(
                    user_id=current_user.id,
                    name=f"{original.name}",
                    description=original.description,
                    chat_config=original.chat_config,
                    memory_config=original.memory_config,
                    rag_config=original.rag_config,
                    graph_definition=original.graph_definition,
                    tags=original.tags,
                    is_public=False,
                    is_active=True,
                    version="1.0.0",
                )
                db.add(clone)
                db.flush()
                new_item_id = str(clone.id)
        
        # Update install count
        item.install_count = (item.install_count or 0) + 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Successfully installed {item.name}",
            "item_id": item_id,
            "new_item_id": new_item_id,
            "item_type": item.reference_type,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to install marketplace item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/items/{item_id}/reviews")
async def create_review(
    item_id: str,
    request: CreateReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update a review for a marketplace item."""
    try:
        item_uuid = uuid.UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid item ID format")
    
    try:
        item = db.query(MarketplaceItem).filter(MarketplaceItem.id == item_uuid).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Check for existing review
        existing = db.query(MarketplaceReview).filter(
            MarketplaceReview.item_id == item_uuid,
            MarketplaceReview.user_id == current_user.id
        ).first()
        
        if existing:
            # Update existing review
            old_rating = existing.rating
            existing.rating = request.rating
            existing.comment = request.comment
            existing.updated_at = datetime.utcnow()
            
            # Update item rating
            total_rating = (item.rating * item.rating_count) - old_rating + request.rating
            item.rating = total_rating / item.rating_count
        else:
            # Create new review
            review = MarketplaceReview(
                item_id=item_uuid,
                user_id=current_user.id,
                rating=request.rating,
                comment=request.comment,
            )
            db.add(review)
            
            # Update item rating
            total_rating = (item.rating or 0) * (item.rating_count or 0) + request.rating
            item.rating_count = (item.rating_count or 0) + 1
            item.rating = total_rating / item.rating_count
        
        db.commit()
        
        return {
            "success": True,
            "message": "Review submitted successfully",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/items/{item_id}")
async def delete_marketplace_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove an item from the marketplace."""
    try:
        item_uuid = uuid.UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid item ID format")
    
    try:
        item = db.query(MarketplaceItem).filter(
            MarketplaceItem.id == item_uuid,
            MarketplaceItem.author_id == current_user.id
        ).first()
        
        if not item:
            raise HTTPException(status_code=404, detail="Item not found or access denied")
        
        db.delete(item)
        db.commit()
        
        return {"success": True, "message": "Item removed from marketplace"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete marketplace item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_marketplace_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get available marketplace categories with counts."""
    try:
        # Get counts by item type
        type_counts = db.query(
            MarketplaceItem.item_type,
            func.count(MarketplaceItem.id).label("count")
        ).filter(
            MarketplaceItem.is_published == True
        ).group_by(MarketplaceItem.item_type).all()
        
        categories = [
            {"id": "agents", "name": "Agents", "count": 0},
            {"id": "workflows", "name": "Workflows", "count": 0},
            {"id": "templates", "name": "Templates", "count": 0},
            {"id": "tools", "name": "Tools", "count": 0},
            {"id": "agentflow", "name": "Agentflows", "count": 0},
            {"id": "chatflow", "name": "Chatflows", "count": 0},
        ]
        
        type_map = {tc.item_type: tc.count for tc in type_counts}
        for cat in categories:
            cat["count"] = type_map.get(cat["id"], 0)
        
        return {"categories": [c for c in categories if c["count"] > 0 or c["id"] in ["agentflow", "chatflow", "templates"]]}
        
    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/featured")
async def get_featured_items(
    limit: int = Query(6, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get featured marketplace items."""
    try:
        items = db.query(MarketplaceItem).filter(
            MarketplaceItem.is_published == True,
            MarketplaceItem.is_featured == True
        ).order_by(MarketplaceItem.install_count.desc()).limit(limit).all()
        
        # Get author names
        author_ids = list(set(item.author_id for item in items))
        authors = db.query(User).filter(User.id.in_(author_ids)).all()
        author_map = {str(a.id): a.username or a.email for a in authors}
        
        return {
            "items": [
                MarketplaceItemResponse(**marketplace_item_to_response(
                    item,
                    author_map.get(str(item.author_id))
                ))
                for item in items
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get featured items: {e}")
        raise HTTPException(status_code=500, detail=str(e))
