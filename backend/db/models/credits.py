"""Credit system models for usage-based billing."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Integer, Numeric, Index, CheckConstraint, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum
from backend.db.database import Base


class CreditPackage(str, enum.Enum):
    """Credit package types."""
    STARTER = "starter"  # 1,000 credits - $10
    PRO = "pro"  # 10,000 credits - $80 (20% discount)
    BUSINESS = "business"  # 50,000 credits - $350 (30% discount)
    ENTERPRISE = "enterprise"  # 200,000 credits - $1,200 (40% discount)


class TransactionType(str, enum.Enum):
    """Credit transaction types."""
    PURCHASE = "purchase"
    USAGE = "usage"
    REFUND = "refund"
    BONUS = "bonus"
    ADJUSTMENT = "adjustment"


class CreditBalance(Base):
    """User credit balance."""
    __tablename__ = "credit_balances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Balance
    balance = Column(Numeric(12, 2), nullable=False, default=0)  # Current balance
    lifetime_purchased = Column(Numeric(12, 2), nullable=False, default=0)  # Total purchased
    lifetime_used = Column(Numeric(12, 2), nullable=False, default=0)  # Total used
    
    # Auto-recharge settings
    auto_recharge_enabled = Column(Boolean, default=False)
    auto_recharge_threshold = Column(Numeric(12, 2), nullable=True)  # Recharge when below this
    auto_recharge_amount = Column(Numeric(12, 2), nullable=True)  # Amount to recharge
    auto_recharge_package = Column(String(50), nullable=True)  # Package to purchase
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_purchase_at = Column(DateTime, nullable=True)
    last_usage_at = Column(DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint("balance >= 0", name="check_balance_non_negative"),
    )


class CreditTransaction(Base):
    """Credit transaction history."""
    __tablename__ = "credit_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Transaction details
    transaction_type = Column(Enum(TransactionType), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)  # Positive for credit, negative for debit
    balance_after = Column(Numeric(12, 2), nullable=False)  # Balance after transaction
    
    # Description
    description = Column(Text, nullable=True)
    meta_data = Column(JSONB, default=dict)  # Additional data (execution_id, workflow_id, etc.)
    
    # Related records
    purchase_id = Column(UUID(as_uuid=True), ForeignKey("credit_purchases.id", ondelete="SET NULL"), nullable=True)
    usage_id = Column(UUID(as_uuid=True), ForeignKey("credit_usage.id", ondelete="SET NULL"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("ix_credit_transactions_user_type", "user_id", "transaction_type"),
        Index("ix_credit_transactions_created", "created_at"),
    )


class CreditPurchase(Base):
    """Credit purchase records."""
    __tablename__ = "credit_purchases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Purchase details
    package = Column(String(50), nullable=False)  # starter, pro, business, enterprise
    credits_amount = Column(Numeric(12, 2), nullable=False)
    price_paid = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    
    # Payment info
    stripe_payment_intent_id = Column(String(255), nullable=True)
    stripe_charge_id = Column(String(255), nullable=True)
    payment_status = Column(String(50), default="pending")  # pending, completed, failed, refunded
    
    # Auto-recharge
    is_auto_recharge = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    refunded_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_credit_purchases_user_status", "user_id", "payment_status"),
    )


class CreditUsage(Base):
    """Credit usage records for tracking consumption."""
    __tablename__ = "credit_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Usage details
    resource_type = Column(String(50), nullable=False, index=True)  # workflow, agent, llm_call, etc.
    resource_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    resource_name = Column(String(255), nullable=True)
    
    # Cost breakdown
    credits_used = Column(Numeric(12, 2), nullable=False)
    estimated_cost = Column(Numeric(12, 2), nullable=True)  # Estimated before execution
    actual_cost = Column(Numeric(12, 2), nullable=True)  # Actual after execution
    
    # Execution details
    execution_id = Column(UUID(as_uuid=True), nullable=True)
    execution_duration_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    
    # Metadata
    meta_data = Column(JSONB, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_credit_usage_user_resource", "user_id", "resource_type"),
        Index("ix_credit_usage_resource", "resource_type", "resource_id"),
    )


class CreditPricing(Base):
    """Pricing configuration for different resources."""
    __tablename__ = "credit_pricing"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Resource identification
    resource_type = Column(String(50), nullable=False, unique=True, index=True)
    resource_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Pricing
    base_cost = Column(Numeric(12, 6), nullable=False)  # Base cost in credits
    unit = Column(String(50), nullable=False)  # per_execution, per_1k_tokens, per_minute, etc.
    
    # Multipliers
    multipliers = Column(JSONB, default=dict)  # Model-specific or tier-specific multipliers
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CreditAlert(Base):
    """Credit balance alerts and notifications."""
    __tablename__ = "credit_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Alert details
    alert_type = Column(String(50), nullable=False)  # low_balance, depleted, usage_spike
    threshold = Column(Numeric(12, 2), nullable=True)
    current_balance = Column(Numeric(12, 2), nullable=False)
    
    # Status
    is_read = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_credit_alerts_user_unread", "user_id", "is_read"),
    )
