"""API endpoints for credit management."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field

from backend.db.database import get_db
from backend.services.credit_service import CreditService
from backend.services.payment_service import PaymentService
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User


router = APIRouter(prefix="/api/v1/credits", tags=["credits"])


# Pydantic Models
class CreditBalanceResponse(BaseModel):
    """Credit balance response."""
    balance: float
    lifetime_purchased: float
    lifetime_used: float
    auto_recharge_enabled: bool
    auto_recharge_threshold: Optional[float]
    auto_recharge_package: Optional[str]


class PackageInfo(BaseModel):
    """Credit package information."""
    package: str
    credits: float
    price: float
    discount_percentage: Optional[float] = None


class PurchaseRequest(BaseModel):
    """Request to purchase credits."""
    package: str = Field(..., description="Package type: starter, pro, business, enterprise")


class PurchaseResponse(BaseModel):
    """Purchase response."""
    id: str
    package: str
    credits_amount: float
    price_paid: float
    payment_status: str
    created_at: str


class AutoRechargeConfig(BaseModel):
    """Auto-recharge configuration."""
    enabled: bool
    threshold: Optional[float] = Field(None, ge=0)
    package: Optional[str] = None


class UsageStatsResponse(BaseModel):
    """Usage statistics response."""
    total_usage: float
    usage_by_type: List[dict]
    daily_usage: List[dict]


class TransactionResponse(BaseModel):
    """Transaction response."""
    id: str
    transaction_type: str
    amount: float
    balance_after: float
    description: Optional[str]
    created_at: str


class AlertResponse(BaseModel):
    """Alert response."""
    id: str
    alert_type: str
    threshold: Optional[float]
    current_balance: float
    is_read: bool
    created_at: str


# Balance Endpoints
@router.get("/balance", response_model=CreditBalanceResponse)
def get_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current credit balance."""
    service = CreditService(db)
    balance = service.get_or_create_balance(str(current_user.id))

    return {
        "balance": float(balance.balance),
        "lifetime_purchased": float(balance.lifetime_purchased),
        "lifetime_used": float(balance.lifetime_used),
        "auto_recharge_enabled": balance.auto_recharge_enabled,
        "auto_recharge_threshold": float(balance.auto_recharge_threshold) if balance.auto_recharge_threshold else None,
        "auto_recharge_package": balance.auto_recharge_package,
    }


# Package Endpoints
@router.get("/packages", response_model=List[PackageInfo])
def list_packages():
    """List available credit packages."""
    packages = []
    base_price_per_credit = Decimal("0.01")  # $0.01 per credit at base rate

    for package_name, info in CreditService.PACKAGES.items():
        credits = info["credits"]
        price = info["price"]
        
        # Calculate discount
        expected_price = credits * base_price_per_credit
        discount = ((expected_price - price) / expected_price * 100) if expected_price > 0 else 0

        packages.append({
            "package": package_name,
            "credits": float(credits),
            "price": float(price),
            "discount_percentage": float(discount) if discount > 0 else None,
        })

    return packages


# Purchase Endpoints
@router.post("/purchase/intent")
def create_purchase_intent(
    request: PurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a payment intent for credit purchase."""
    service = CreditService(db)
    payment_service = PaymentService()

    # Get package info
    if request.package not in service.PACKAGES:
        from backend.exceptions import ValidationException as BadRequestException
        raise BadRequestException("Invalid package")

    package_info = service.PACKAGES[request.package]

    # Create payment intent
    intent = payment_service.create_payment_intent(
        amount=package_info["price"],
        currency="usd",
        metadata={
            "user_id": str(current_user.id),
            "package": request.package,
            "credits": str(package_info["credits"]),
        },
    )

    return intent


@router.post("/purchase/complete", response_model=PurchaseResponse)
def complete_purchase(
    payment_intent_id: str,
    package: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Complete credit purchase after payment."""
    service = CreditService(db)
    payment_service = PaymentService()

    # Verify payment
    payment = payment_service.confirm_payment(payment_intent_id)
    if payment["status"] != "succeeded":
        from backend.exceptions import ValidationException as BadRequestException
        raise BadRequestException("Payment not completed")

    # Create purchase and add credits
    purchase = service.create_purchase(
        user_id=str(current_user.id),
        package=package,
        payment_intent_id=payment_intent_id,
    )

    return {
        "id": str(purchase.id),
        "package": purchase.package,
        "credits_amount": float(purchase.credits_amount),
        "price_paid": float(purchase.price_paid),
        "payment_status": purchase.payment_status,
        "created_at": purchase.created_at.isoformat(),
    }


@router.get("/purchases", response_model=List[PurchaseResponse])
def list_purchases(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List purchase history."""
    service = CreditService(db)
    purchases = service.get_user_purchases(str(current_user.id), limit)

    return [
        {
            "id": str(p.id),
            "package": p.package,
            "credits_amount": float(p.credits_amount),
            "price_paid": float(p.price_paid),
            "payment_status": p.payment_status,
            "created_at": p.created_at.isoformat(),
        }
        for p in purchases
    ]


# Usage Endpoints
@router.get("/usage/stats", response_model=UsageStatsResponse)
def get_usage_stats(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get usage statistics."""
    service = CreditService(db)
    stats = service.get_usage_stats(str(current_user.id), days)
    return stats


@router.get("/usage/history")
def get_usage_history(
    resource_type: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get usage history."""
    service = CreditService(db)
    usages = service.get_usage_history(
        str(current_user.id), resource_type=resource_type, limit=limit
    )

    return [
        {
            "id": str(u.id),
            "resource_type": u.resource_type,
            "resource_name": u.resource_name,
            "credits_used": float(u.credits_used),
            "execution_duration_ms": u.execution_duration_ms,
            "tokens_used": u.tokens_used,
            "created_at": u.created_at.isoformat(),
        }
        for u in usages
    ]


# Transaction Endpoints
@router.get("/transactions", response_model=List[TransactionResponse])
def list_transactions(
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List transaction history."""
    service = CreditService(db)
    transactions = service.get_transactions(str(current_user.id), limit)

    return [
        {
            "id": str(t.id),
            "transaction_type": t.transaction_type.value,
            "amount": float(t.amount),
            "balance_after": float(t.balance_after),
            "description": t.description,
            "created_at": t.created_at.isoformat(),
        }
        for t in transactions
    ]


# Auto-recharge Endpoints
@router.post("/auto-recharge/configure")
def configure_auto_recharge(
    config: AutoRechargeConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Configure auto-recharge settings."""
    service = CreditService(db)
    service.configure_auto_recharge(
        user_id=str(current_user.id),
        enabled=config.enabled,
        threshold=Decimal(str(config.threshold)) if config.threshold else None,
        package=config.package,
    )

    return {"message": "Auto-recharge configured successfully"}


# Alert Endpoints
@router.get("/alerts", response_model=List[AlertResponse])
def list_alerts(
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List credit alerts."""
    service = CreditService(db)
    alerts = service.get_alerts(str(current_user.id), unread_only)

    return [
        {
            "id": str(a.id),
            "alert_type": a.alert_type,
            "threshold": float(a.threshold) if a.threshold else None,
            "current_balance": float(a.current_balance),
            "is_read": a.is_read,
            "created_at": a.created_at.isoformat(),
        }
        for a in alerts
    ]


@router.post("/alerts/{alert_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_alert_read(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark alert as read."""
    service = CreditService(db)
    service.mark_alert_read(alert_id, str(current_user.id))


# Estimation Endpoint
@router.post("/estimate")
def estimate_cost(
    resource_type: str,
    metadata: Optional[dict] = None,
    db: Session = Depends(get_db),
):
    """Estimate cost for a resource execution."""
    service = CreditService(db)
    estimated_cost = service.estimate_cost(resource_type, metadata)

    return {
        "resource_type": resource_type,
        "estimated_credits": float(estimated_cost),
    }
