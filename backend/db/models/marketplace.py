"""Marketplace models for purchases, reviews, and revenue."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Integer, Float, Index, CheckConstraint, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from backend.db.database import Base


class MarketplacePurchase(Base):
    """Purchase record for marketplace items."""
    __tablename__ = "marketplace_purchases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    item_id = Column(UUID(as_uuid=True), ForeignKey("marketplace_items.id", ondelete="CASCADE"), nullable=False, index=True)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Purchase Details
    price_paid = Column(Numeric(10, 2), nullable=False)  # Amount paid in USD
    currency = Column(String(3), default="USD")
    
    # Payment Info
    stripe_payment_intent_id = Column(String(255), nullable=True)
    stripe_charge_id = Column(String(255), nullable=True)
    payment_status = Column(String(50), default="pending")  # pending, completed, failed, refunded
    
    # License
    license_key = Column(String(255), unique=True, nullable=True)
    license_type = Column(String(50), default="single_user")  # single_user, team, enterprise
    
    # Status
    is_active = Column(Boolean, default=True)
    refunded_at = Column(DateTime, nullable=True)
    refund_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_purchases_buyer_item", "buyer_id", "item_id"),
        Index("ix_purchases_status", "payment_status", "is_active"),
    )


class MarketplaceReview(Base):
    """Review and rating for marketplace items."""
    __tablename__ = "marketplace_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    item_id = Column(UUID(as_uuid=True), ForeignKey("marketplace_items.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    purchase_id = Column(UUID(as_uuid=True), ForeignKey("marketplace_purchases.id", ondelete="SET NULL"), nullable=True)
    
    # Review Content
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String(255), nullable=True)
    comment = Column(Text, nullable=True)
    
    # Helpful votes
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)
    
    # Status
    is_verified_purchase = Column(Boolean, default=False)
    is_published = Column(Boolean, default=True)
    is_flagged = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_reviews_item_user", "item_id", "user_id", unique=True),
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_review_rating_range"),
    )


class MarketplaceRevenue(Base):
    """Revenue tracking and distribution for marketplace sales."""
    __tablename__ = "marketplace_revenue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    purchase_id = Column(UUID(as_uuid=True), ForeignKey("marketplace_purchases.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("marketplace_items.id", ondelete="CASCADE"), nullable=False, index=True)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Revenue Split
    gross_amount = Column(Numeric(10, 2), nullable=False)  # Total sale amount
    platform_fee = Column(Numeric(10, 2), nullable=False)  # Platform commission (30%)
    seller_amount = Column(Numeric(10, 2), nullable=False)  # Amount to seller (70%)
    
    # Payout Info
    payout_status = Column(String(50), default="pending")  # pending, processing, paid, failed
    payout_method = Column(String(50), nullable=True)  # stripe_connect, paypal, bank_transfer
    payout_id = Column(String(255), nullable=True)  # External payout reference
    payout_date = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_revenue_seller_status", "seller_id", "payout_status"),
        Index("ix_revenue_created", "created_at"),
    )


class MarketplaceCategory(Base):
    """Categories for marketplace items."""
    __tablename__ = "marketplace_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    
    # Hierarchy
    parent_id = Column(UUID(as_uuid=True), ForeignKey("marketplace_categories.id", ondelete="CASCADE"), nullable=True)
    
    # Display
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Stats
    item_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MarketplaceTag(Base):
    """Tags for marketplace items."""
    __tablename__ = "marketplace_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    name = Column(String(50), unique=True, nullable=False, index=True)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    
    # Stats
    usage_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


class MarketplaceItemTag(Base):
    """Many-to-many relationship between items and tags."""
    __tablename__ = "marketplace_item_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = Column(UUID(as_uuid=True), ForeignKey("marketplace_items.id", ondelete="CASCADE"), nullable=False, index=True)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("marketplace_tags.id", ondelete="CASCADE"), nullable=False, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_item_tags_item_tag", "item_id", "tag_id", unique=True),
    )
