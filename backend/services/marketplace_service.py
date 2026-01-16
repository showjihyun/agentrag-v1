"""Service for marketplace operations including purchases and reviews."""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, and_, or_
from datetime import datetime
from decimal import Decimal
import uuid
import secrets

from backend.db.models.marketplace import (
    MarketplacePurchase,
    MarketplaceReview,
    MarketplaceRevenue,
    MarketplaceCategory,
    MarketplaceTag,
    MarketplaceItemTag,
)
from backend.db.models.flows import MarketplaceItem
from backend.db.models.user import User
from backend.exceptions import (
    ResourceNotFoundException as NotFoundException,
    ValidationException as BadRequestException,
    AuthorizationException as ForbiddenException,
)


class MarketplaceService:
    """Service for managing marketplace operations."""

    PLATFORM_FEE_PERCENTAGE = Decimal("0.30")  # 30% platform fee

    def __init__(self, db: Session):
        self.db = db

    # Item Management
    def get_marketplace_items(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        item_type: Optional[str] = None,
        is_featured: Optional[bool] = None,
        sort_by: str = "created_at",
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[List[MarketplaceItem], int]:
        """Get marketplace items with filters."""
        query = self.db.query(MarketplaceItem).filter(
            MarketplaceItem.is_published == True
        )

        # Apply filters
        if category:
            query = query.filter(MarketplaceItem.category == category)
        
        if item_type:
            query = query.filter(MarketplaceItem.item_type == item_type)
        
        if is_featured is not None:
            query = query.filter(MarketplaceItem.is_featured == is_featured)
        
        if search:
            query = query.filter(
                or_(
                    MarketplaceItem.name.ilike(f"%{search}%"),
                    MarketplaceItem.description.ilike(f"%{search}%"),
                )
            )

        # Tag filtering
        if tags:
            query = query.join(MarketplaceItemTag).join(MarketplaceTag).filter(
                MarketplaceTag.slug.in_(tags)
            )

        # Get total count
        total = query.count()

        # Apply sorting
        if sort_by == "popular":
            query = query.order_by(desc(MarketplaceItem.install_count))
        elif sort_by == "rating":
            query = query.order_by(desc(MarketplaceItem.rating))
        elif sort_by == "newest":
            query = query.order_by(desc(MarketplaceItem.created_at))
        else:
            query = query.order_by(desc(MarketplaceItem.created_at))

        # Apply pagination
        items = query.limit(limit).offset(offset).all()

        return items, total

    def get_marketplace_item(self, item_id: str) -> MarketplaceItem:
        """Get marketplace item by ID."""
        item = self.db.query(MarketplaceItem).filter(
            MarketplaceItem.id == uuid.UUID(item_id)
        ).first()
        if not item:
            raise NotFoundException("Marketplace item not found")
        return item

    # Purchase Management
    def create_purchase(
        self,
        item_id: str,
        buyer_id: str,
        payment_intent_id: str,
        amount: Decimal,
    ) -> MarketplacePurchase:
        """Create a purchase record."""
        item = self.get_marketplace_item(item_id)

        # Check if already purchased
        existing = self.db.query(MarketplacePurchase).filter(
            MarketplacePurchase.item_id == uuid.UUID(item_id),
            MarketplacePurchase.buyer_id == uuid.UUID(buyer_id),
            MarketplacePurchase.is_active == True,
        ).first()
        if existing:
            raise BadRequestException("Item already purchased")

        # Create purchase
        purchase = MarketplacePurchase(
            id=uuid.uuid4(),
            item_id=uuid.UUID(item_id),
            buyer_id=uuid.UUID(buyer_id),
            price_paid=amount,
            stripe_payment_intent_id=payment_intent_id,
            payment_status="completed",
            license_key=self._generate_license_key(),
        )
        self.db.add(purchase)

        # Update item stats
        item.install_count += 1

        # Create revenue record
        self._create_revenue_record(purchase, item)

        self.db.commit()
        self.db.refresh(purchase)

        return purchase

    def get_user_purchases(self, user_id: str) -> List[MarketplacePurchase]:
        """Get all purchases for a user."""
        purchases = (
            self.db.query(MarketplacePurchase)
            .filter(
                MarketplacePurchase.buyer_id == uuid.UUID(user_id),
                MarketplacePurchase.is_active == True,
            )
            .order_by(desc(MarketplacePurchase.created_at))
            .all()
        )
        return purchases

    def check_purchase(self, item_id: str, user_id: str) -> bool:
        """Check if user has purchased an item."""
        purchase = self.db.query(MarketplacePurchase).filter(
            MarketplacePurchase.item_id == uuid.UUID(item_id),
            MarketplacePurchase.buyer_id == uuid.UUID(user_id),
            MarketplacePurchase.is_active == True,
            MarketplacePurchase.payment_status == "completed",
        ).first()
        return purchase is not None

    def refund_purchase(
        self, purchase_id: str, user_id: str, reason: str
    ) -> MarketplacePurchase:
        """Refund a purchase."""
        purchase = self.db.query(MarketplacePurchase).filter(
            MarketplacePurchase.id == uuid.UUID(purchase_id),
            MarketplacePurchase.buyer_id == uuid.UUID(user_id),
        ).first()
        if not purchase:
            raise NotFoundException("Purchase not found")

        if purchase.payment_status == "refunded":
            raise BadRequestException("Purchase already refunded")

        purchase.payment_status = "refunded"
        purchase.is_active = False
        purchase.refunded_at = datetime.utcnow()
        purchase.refund_reason = reason

        # Update revenue record
        revenue = self.db.query(MarketplaceRevenue).filter(
            MarketplaceRevenue.purchase_id == purchase.id
        ).first()
        if revenue:
            revenue.payout_status = "cancelled"

        self.db.commit()
        self.db.refresh(purchase)

        return purchase

    # Review Management
    def create_review(
        self,
        item_id: str,
        user_id: str,
        rating: int,
        title: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> MarketplaceReview:
        """Create a review for an item."""
        # Check if already reviewed
        existing = self.db.query(MarketplaceReview).filter(
            MarketplaceReview.item_id == uuid.UUID(item_id),
            MarketplaceReview.user_id == uuid.UUID(user_id),
        ).first()
        if existing:
            raise BadRequestException("Already reviewed this item")

        # Check if purchased
        is_verified = self.check_purchase(item_id, user_id)

        # Create review
        review = MarketplaceReview(
            id=uuid.uuid4(),
            item_id=uuid.UUID(item_id),
            user_id=uuid.UUID(user_id),
            rating=rating,
            title=title,
            comment=comment,
            is_verified_purchase=is_verified,
        )
        self.db.add(review)

        # Update item rating
        self._update_item_rating(item_id)

        self.db.commit()
        self.db.refresh(review)

        return review

    def get_item_reviews(
        self, item_id: str, limit: int = 20, offset: int = 0
    ) -> tuple[List[MarketplaceReview], int]:
        """Get reviews for an item."""
        query = self.db.query(MarketplaceReview).filter(
            MarketplaceReview.item_id == uuid.UUID(item_id),
            MarketplaceReview.is_published == True,
        )

        total = query.count()
        reviews = (
            query.order_by(desc(MarketplaceReview.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

        return reviews, total

    def update_review(
        self,
        review_id: str,
        user_id: str,
        rating: Optional[int] = None,
        title: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> MarketplaceReview:
        """Update a review."""
        review = self.db.query(MarketplaceReview).filter(
            MarketplaceReview.id == uuid.UUID(review_id),
            MarketplaceReview.user_id == uuid.UUID(user_id),
        ).first()
        if not review:
            raise NotFoundException("Review not found")

        if rating is not None:
            review.rating = rating
        if title is not None:
            review.title = title
        if comment is not None:
            review.comment = comment

        review.updated_at = datetime.utcnow()

        # Update item rating
        self._update_item_rating(str(review.item_id))

        self.db.commit()
        self.db.refresh(review)

        return review

    def delete_review(self, review_id: str, user_id: str):
        """Delete a review."""
        review = self.db.query(MarketplaceReview).filter(
            MarketplaceReview.id == uuid.UUID(review_id),
            MarketplaceReview.user_id == uuid.UUID(user_id),
        ).first()
        if not review:
            raise NotFoundException("Review not found")

        item_id = str(review.item_id)
        self.db.delete(review)

        # Update item rating
        self._update_item_rating(item_id)

        self.db.commit()

    # Revenue Management
    def get_seller_revenue(
        self, seller_id: str, status: Optional[str] = None
    ) -> List[MarketplaceRevenue]:
        """Get revenue records for a seller."""
        query = self.db.query(MarketplaceRevenue).filter(
            MarketplaceRevenue.seller_id == uuid.UUID(seller_id)
        )

        if status:
            query = query.filter(MarketplaceRevenue.payout_status == status)

        revenues = query.order_by(desc(MarketplaceRevenue.created_at)).all()
        return revenues

    def get_seller_stats(self, seller_id: str) -> Dict[str, Any]:
        """Get seller statistics."""
        total_revenue = (
            self.db.query(func.sum(MarketplaceRevenue.seller_amount))
            .filter(MarketplaceRevenue.seller_id == uuid.UUID(seller_id))
            .scalar()
            or Decimal("0")
        )

        pending_payout = (
            self.db.query(func.sum(MarketplaceRevenue.seller_amount))
            .filter(
                MarketplaceRevenue.seller_id == uuid.UUID(seller_id),
                MarketplaceRevenue.payout_status == "pending",
            )
            .scalar()
            or Decimal("0")
        )

        total_sales = (
            self.db.query(func.count(MarketplacePurchase.id))
            .join(MarketplaceRevenue)
            .filter(MarketplaceRevenue.seller_id == uuid.UUID(seller_id))
            .scalar()
            or 0
        )

        return {
            "total_revenue": float(total_revenue),
            "pending_payout": float(pending_payout),
            "total_sales": total_sales,
        }

    # Category & Tag Management
    def get_categories(self) -> List[MarketplaceCategory]:
        """Get all active categories."""
        categories = (
            self.db.query(MarketplaceCategory)
            .filter(MarketplaceCategory.is_active == True)
            .order_by(MarketplaceCategory.display_order)
            .all()
        )
        return categories

    def get_popular_tags(self, limit: int = 20) -> List[MarketplaceTag]:
        """Get popular tags."""
        tags = (
            self.db.query(MarketplaceTag)
            .order_by(desc(MarketplaceTag.usage_count))
            .limit(limit)
            .all()
        )
        return tags

    # Helper Methods
    def _generate_license_key(self) -> str:
        """Generate a unique license key."""
        return f"LIC-{secrets.token_hex(16).upper()}"

    def _create_revenue_record(
        self, purchase: MarketplacePurchase, item: MarketplaceItem
    ):
        """Create revenue distribution record."""
        gross_amount = purchase.price_paid
        platform_fee = gross_amount * self.PLATFORM_FEE_PERCENTAGE
        seller_amount = gross_amount - platform_fee

        revenue = MarketplaceRevenue(
            id=uuid.uuid4(),
            purchase_id=purchase.id,
            item_id=item.id,
            seller_id=item.author_id,
            gross_amount=gross_amount,
            platform_fee=platform_fee,
            seller_amount=seller_amount,
            payout_status="pending",
        )
        self.db.add(revenue)

    def _update_item_rating(self, item_id: str):
        """Update item's average rating."""
        result = (
            self.db.query(
                func.avg(MarketplaceReview.rating).label("avg_rating"),
                func.count(MarketplaceReview.id).label("count"),
            )
            .filter(
                MarketplaceReview.item_id == uuid.UUID(item_id),
                MarketplaceReview.is_published == True,
            )
            .first()
        )

        item = self.get_marketplace_item(item_id)
        item.rating = float(result.avg_rating or 0)
        item.rating_count = result.count or 0
