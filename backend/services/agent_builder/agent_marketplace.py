"""
Agent Marketplace

Provides marketplace features for agents:
- Public agent discovery
- Search and filtering
- Ratings and reviews
- Usage statistics
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    """Marketplace agent status."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PUBLISHED = "published"
    REJECTED = "rejected"
    ARCHIVED = "archived"


@dataclass
class AgentReview:
    """Agent review."""
    id: str
    agent_id: str
    user_id: str
    user_name: str
    rating: int  # 1-5
    title: str
    content: str
    created_at: str
    helpful_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MarketplaceAgent:
    """Agent listing in marketplace."""
    id: str
    agent_id: str
    name: str
    description: str
    short_description: str
    category: str
    tags: List[str]
    author_id: str
    author_name: str
    
    # Stats
    downloads: int = 0
    executions: int = 0
    avg_rating: float = 0.0
    review_count: int = 0
    
    # Status
    status: AgentStatus = AgentStatus.DRAFT
    published_at: Optional[str] = None
    
    # Pricing
    is_free: bool = True
    price: float = 0.0
    
    # Metadata
    version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


class AgentMarketplaceService:
    """
    Service for agent marketplace.
    
    Features:
    - Publish agents to marketplace
    - Search and discover agents
    - Ratings and reviews
    - Download/install agents
    """
    
    def __init__(self):
        self._listings: Dict[str, MarketplaceAgent] = {}
        self._reviews: Dict[str, List[AgentReview]] = {}
        self._user_downloads: Dict[str, List[str]] = {}  # user_id -> [agent_ids]
    
    # ========================================================================
    # Publishing
    # ========================================================================
    
    async def publish_agent(
        self,
        agent_id: str,
        name: str,
        description: str,
        short_description: str,
        category: str,
        tags: List[str],
        author_id: str,
        author_name: str,
        is_free: bool = True,
        price: float = 0.0,
    ) -> MarketplaceAgent:
        """Publish an agent to the marketplace."""
        listing = MarketplaceAgent(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            name=name,
            description=description,
            short_description=short_description[:200],
            category=category,
            tags=tags,
            author_id=author_id,
            author_name=author_name,
            status=AgentStatus.PENDING_REVIEW,
            is_free=is_free,
            price=price if not is_free else 0.0,
        )
        
        self._listings[listing.id] = listing
        logger.info(f"Agent {agent_id} submitted for marketplace review")
        return listing
    
    async def approve_listing(self, listing_id: str) -> bool:
        """Approve a marketplace listing."""
        listing = self._listings.get(listing_id)
        if not listing:
            return False
        
        listing.status = AgentStatus.PUBLISHED
        listing.published_at = datetime.utcnow().isoformat()
        logger.info(f"Listing {listing_id} approved")
        return True
    
    async def reject_listing(self, listing_id: str, reason: str) -> bool:
        """Reject a marketplace listing."""
        listing = self._listings.get(listing_id)
        if not listing:
            return False
        
        listing.status = AgentStatus.REJECTED
        logger.info(f"Listing {listing_id} rejected: {reason}")
        return True
    
    # ========================================================================
    # Discovery
    # ========================================================================
    
    async def search_agents(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_rating: Optional[float] = None,
        is_free: Optional[bool] = None,
        sort_by: str = "downloads",
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Search marketplace agents."""
        results = [
            l for l in self._listings.values()
            if l.status == AgentStatus.PUBLISHED
        ]
        
        # Apply filters
        if query:
            query_lower = query.lower()
            results = [
                l for l in results
                if query_lower in l.name.lower() or
                query_lower in l.description.lower() or
                any(query_lower in tag for tag in l.tags)
            ]
        
        if category:
            results = [l for l in results if l.category == category]
        
        if tags:
            results = [
                l for l in results
                if any(tag in l.tags for tag in tags)
            ]
        
        if min_rating is not None:
            results = [l for l in results if l.avg_rating >= min_rating]
        
        if is_free is not None:
            results = [l for l in results if l.is_free == is_free]
        
        # Sort
        sort_key = {
            "downloads": lambda x: x.downloads,
            "rating": lambda x: x.avg_rating,
            "newest": lambda x: x.published_at or "",
            "name": lambda x: x.name.lower(),
        }.get(sort_by, lambda x: x.downloads)
        
        results.sort(key=sort_key, reverse=sort_by != "name")
        
        total = len(results)
        results = results[offset:offset + limit]
        
        return {
            "agents": [l.to_dict() for l in results],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    
    async def get_featured_agents(self, limit: int = 10) -> List[MarketplaceAgent]:
        """Get featured/popular agents."""
        published = [
            l for l in self._listings.values()
            if l.status == AgentStatus.PUBLISHED
        ]
        
        # Sort by combination of downloads and rating
        published.sort(
            key=lambda x: x.downloads * 0.7 + x.avg_rating * 100 * 0.3,
            reverse=True
        )
        
        return published[:limit]
    
    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get all categories with counts."""
        categories = {}
        
        for listing in self._listings.values():
            if listing.status == AgentStatus.PUBLISHED:
                cat = listing.category
                if cat not in categories:
                    categories[cat] = {"name": cat, "count": 0}
                categories[cat]["count"] += 1
        
        return sorted(categories.values(), key=lambda x: x["count"], reverse=True)
    
    async def get_listing(self, listing_id: str) -> Optional[MarketplaceAgent]:
        """Get a specific listing."""
        return self._listings.get(listing_id)
    
    # ========================================================================
    # Reviews
    # ========================================================================
    
    async def add_review(
        self,
        listing_id: str,
        user_id: str,
        user_name: str,
        rating: int,
        title: str,
        content: str,
    ) -> AgentReview:
        """Add a review for an agent."""
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        
        review = AgentReview(
            id=str(uuid.uuid4()),
            agent_id=listing_id,
            user_id=user_id,
            user_name=user_name,
            rating=rating,
            title=title,
            content=content,
            created_at=datetime.utcnow().isoformat(),
        )
        
        if listing_id not in self._reviews:
            self._reviews[listing_id] = []
        
        self._reviews[listing_id].append(review)
        
        # Update average rating
        await self._update_rating(listing_id)
        
        logger.info(f"Review added for listing {listing_id}")
        return review
    
    async def get_reviews(
        self,
        listing_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get reviews for an agent."""
        reviews = self._reviews.get(listing_id, [])
        reviews.sort(key=lambda r: r.created_at, reverse=True)
        
        total = len(reviews)
        reviews = reviews[offset:offset + limit]
        
        return {
            "reviews": [r.to_dict() for r in reviews],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    
    async def _update_rating(self, listing_id: str):
        """Update average rating for a listing."""
        reviews = self._reviews.get(listing_id, [])
        listing = self._listings.get(listing_id)
        
        if listing and reviews:
            total_rating = sum(r.rating for r in reviews)
            listing.avg_rating = round(total_rating / len(reviews), 2)
            listing.review_count = len(reviews)
    
    # ========================================================================
    # Downloads
    # ========================================================================
    
    async def download_agent(
        self,
        listing_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Download/install an agent from marketplace."""
        listing = self._listings.get(listing_id)
        if not listing or listing.status != AgentStatus.PUBLISHED:
            raise ValueError("Agent not found or not available")
        
        # Track download
        listing.downloads += 1
        
        if user_id not in self._user_downloads:
            self._user_downloads[user_id] = []
        
        if listing_id not in self._user_downloads[user_id]:
            self._user_downloads[user_id].append(listing_id)
        
        logger.info(f"User {user_id} downloaded agent {listing_id}")
        
        return {
            "listing_id": listing_id,
            "agent_id": listing.agent_id,
            "name": listing.name,
            "version": listing.version,
            "message": "Agent downloaded successfully",
        }
    
    async def get_user_downloads(self, user_id: str) -> List[MarketplaceAgent]:
        """Get agents downloaded by a user."""
        listing_ids = self._user_downloads.get(user_id, [])
        return [
            self._listings[lid]
            for lid in listing_ids
            if lid in self._listings
        ]
    
    # ========================================================================
    # Stats
    # ========================================================================
    
    async def record_execution(self, listing_id: str):
        """Record an agent execution."""
        listing = self._listings.get(listing_id)
        if listing:
            listing.executions += 1
    
    async def get_marketplace_stats(self) -> Dict[str, Any]:
        """Get overall marketplace statistics."""
        published = [
            l for l in self._listings.values()
            if l.status == AgentStatus.PUBLISHED
        ]
        
        total_downloads = sum(l.downloads for l in published)
        total_executions = sum(l.executions for l in published)
        total_reviews = sum(len(self._reviews.get(l.id, [])) for l in published)
        
        return {
            "total_agents": len(published),
            "total_downloads": total_downloads,
            "total_executions": total_executions,
            "total_reviews": total_reviews,
            "categories": len(set(l.category for l in published)),
        }
