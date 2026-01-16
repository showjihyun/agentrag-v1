"""Enhanced marketplace API endpoints with purchase and payment."""
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal

from backend.db.database import get_db
from backend.services.marketplace_service import MarketplaceService
from backend.services.payment_service import PaymentService
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/v1/marketplace", tags=["marketplace-enhanced"])


# Pydantic Models
class PaymentIntentRequest(BaseModel):
    """Request to create a payment intent."""
    item_id: str
    currency: str = "usd"


class PaymentIntentResponse(BaseModel):
    """Payment intent response."""
    client_secret: str
    payment_intent_id: str
    amount: float
    currency: str


class PurchaseRequest(BaseModel):
    """Request to complete a purchase."""
    item_id: str
    payment_intent_id: str


class PurchaseResponse(BaseModel):
    """Purchase response."""
    id: str
    item_id: str
    buyer_id: str
    price_paid: float
    license_key: str
    payment_status: str
    created_at: str

    class Config:
        from_attributes = True


class ReviewRequest(BaseModel):
    """Request to create/update a review."""
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = None
    comment: Optional[str] = None


class ReviewResponse(BaseModel):
    """Review response."""
    id: str
    item_id: str
    user_id: str
    rating: int
    title: Optional[str]
    comment: Optional[str]
    is_verified_purchase: bool
    helpful_count: int
    created_at: str

    class Config:
        from_attributes = True


class SellerStatsResponse(BaseModel):
    """Seller statistics response."""
    total_revenue: float
    pending_payout: float
    total_sales: int


# Payment Endpoints
@router.post("/payment-intent", response_model=PaymentIntentResponse)
def create_payment_intent(
    request: PaymentIntentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a payment intent for purchasing an item."""
    marketplace_service = MarketplaceService(db)
    payment_service = PaymentService()

    # Get item and price
    item = marketplace_service.get_marketplace_item(request.item_id)
    
    # For now, assume free items or fixed price
    # In production, parse item.price field
    if item.price == "free":
        amount = Decimal("0")
    else:
        # Parse price (e.g., "$9.99" -> 9.99)
        amount = Decimal("9.99")  # Default price for demo

    # Create payment intent
    intent = payment_service.create_payment_intent(
        amount=amount,
        currency=request.currency,
        metadata={
            "item_id": request.item_id,
            "buyer_id": str(current_user.id),
            "item_name": item.name,
        },
    )

    return intent


@router.post("/purchase", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
def complete_purchase(
    request: PurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Complete a purchase after payment confirmation."""
    marketplace_service = MarketplaceService(db)
    payment_service = PaymentService()

    # Verify payment
    payment = payment_service.confirm_payment(request.payment_intent_id)
    if payment["status"] != "succeeded":
        from backend.exceptions import ValidationException as BadRequestException
        raise BadRequestException("Payment not completed")

    # Create purchase record
    purchase = marketplace_service.create_purchase(
        item_id=request.item_id,
        buyer_id=str(current_user.id),
        payment_intent_id=request.payment_intent_id,
        amount=payment["amount"],
    )

    return {
        "id": str(purchase.id),
        "item_id": str(purchase.item_id),
        "buyer_id": str(purchase.buyer_id),
        "price_paid": float(purchase.price_paid),
        "license_key": purchase.license_key,
        "payment_status": purchase.payment_status,
        "created_at": purchase.created_at.isoformat(),
    }


@router.get("/purchases", response_model=List[PurchaseResponse])
def list_my_purchases(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all purchases for current user."""
    marketplace_service = MarketplaceService(db)
    purchases = marketplace_service.get_user_purchases(str(current_user.id))

    return [
        {
            "id": str(p.id),
            "item_id": str(p.item_id),
            "buyer_id": str(p.buyer_id),
            "price_paid": float(p.price_paid),
            "license_key": p.license_key,
            "payment_status": p.payment_status,
            "created_at": p.created_at.isoformat(),
        }
        for p in purchases
    ]


@router.get("/purchases/{item_id}/check")
def check_purchase(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check if user has purchased an item."""
    marketplace_service = MarketplaceService(db)
    has_purchased = marketplace_service.check_purchase(item_id, str(current_user.id))
    return {"has_purchased": has_purchased}


@router.post("/purchases/{purchase_id}/refund")
def refund_purchase(
    purchase_id: str,
    reason: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Request a refund for a purchase."""
    marketplace_service = MarketplaceService(db)
    purchase = marketplace_service.refund_purchase(
        purchase_id, str(current_user.id), reason
    )
    return {"message": "Refund processed", "purchase_id": str(purchase.id)}


# Review Endpoints
@router.post("/items/{item_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    item_id: str,
    review_data: ReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a review for an item."""
    marketplace_service = MarketplaceService(db)
    review = marketplace_service.create_review(
        item_id=item_id,
        user_id=str(current_user.id),
        rating=review_data.rating,
        title=review_data.title,
        comment=review_data.comment,
    )

    return {
        "id": str(review.id),
        "item_id": str(review.item_id),
        "user_id": str(review.user_id),
        "rating": review.rating,
        "title": review.title,
        "comment": review.comment,
        "is_verified_purchase": review.is_verified_purchase,
        "helpful_count": review.helpful_count,
        "created_at": review.created_at.isoformat(),
    }


@router.get("/items/{item_id}/reviews", response_model=List[ReviewResponse])
def list_reviews(
    item_id: str,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List reviews for an item."""
    marketplace_service = MarketplaceService(db)
    reviews, total = marketplace_service.get_item_reviews(item_id, limit, offset)

    return [
        {
            "id": str(r.id),
            "item_id": str(r.item_id),
            "user_id": str(r.user_id),
            "rating": r.rating,
            "title": r.title,
            "comment": r.comment,
            "is_verified_purchase": r.is_verified_purchase,
            "helpful_count": r.helpful_count,
            "created_at": r.created_at.isoformat(),
        }
        for r in reviews
    ]


@router.put("/reviews/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: str,
    review_data: ReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a review."""
    marketplace_service = MarketplaceService(db)
    review = marketplace_service.update_review(
        review_id=review_id,
        user_id=str(current_user.id),
        rating=review_data.rating,
        title=review_data.title,
        comment=review_data.comment,
    )

    return {
        "id": str(review.id),
        "item_id": str(review.item_id),
        "user_id": str(review.user_id),
        "rating": review.rating,
        "title": review.title,
        "comment": review.comment,
        "is_verified_purchase": review.is_verified_purchase,
        "helpful_count": review.helpful_count,
        "created_at": review.created_at.isoformat(),
    }


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a review."""
    marketplace_service = MarketplaceService(db)
    marketplace_service.delete_review(review_id, str(current_user.id))


# Seller Endpoints
@router.get("/seller/stats", response_model=SellerStatsResponse)
def get_seller_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get seller statistics."""
    marketplace_service = MarketplaceService(db)
    stats = marketplace_service.get_seller_stats(str(current_user.id))
    return stats


@router.get("/seller/revenue")
def get_seller_revenue(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get seller revenue records."""
    marketplace_service = MarketplaceService(db)
    revenues = marketplace_service.get_seller_revenue(str(current_user.id), status)

    return [
        {
            "id": str(r.id),
            "purchase_id": str(r.purchase_id),
            "gross_amount": float(r.gross_amount),
            "platform_fee": float(r.platform_fee),
            "seller_amount": float(r.seller_amount),
            "payout_status": r.payout_status,
            "payout_date": r.payout_date.isoformat() if r.payout_date else None,
            "created_at": r.created_at.isoformat(),
        }
        for r in revenues
    ]


# Webhook Endpoint
@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhooks."""
    payment_service = PaymentService()
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    try:
        event = payment_service.webhook_construct_event(
            payload, sig_header, webhook_secret
        )

        # Handle different event types
        if event["type"] == "payment_intent.succeeded":
            # Payment succeeded - could trigger notifications
            pass
        elif event["type"] == "payment_intent.payment_failed":
            # Payment failed - could trigger notifications
            pass

        return {"status": "success"}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))
