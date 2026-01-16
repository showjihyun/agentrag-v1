"""Service for credit management and usage tracking."""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from backend.db.models.credits import (
    CreditBalance,
    CreditTransaction,
    CreditPurchase,
    CreditUsage,
    CreditPricing,
    CreditAlert,
    CreditPackage,
    TransactionType,
)
from backend.exceptions import (
    ResourceNotFoundException as NotFoundException,
    ValidationException as BadRequestException,
)


class CreditService:
    """Service for managing credits."""

    # Package definitions
    PACKAGES = {
        CreditPackage.STARTER: {"credits": Decimal("1000"), "price": Decimal("10.00")},
        CreditPackage.PRO: {"credits": Decimal("10000"), "price": Decimal("80.00")},
        CreditPackage.BUSINESS: {"credits": Decimal("50000"), "price": Decimal("350.00")},
        CreditPackage.ENTERPRISE: {"credits": Decimal("200000"), "price": Decimal("1200.00")},
    }

    def __init__(self, db: Session):
        self.db = db

    # Balance Management
    def get_or_create_balance(self, user_id: str) -> CreditBalance:
        """Get or create credit balance for user."""
        balance = self.db.query(CreditBalance).filter(
            CreditBalance.user_id == uuid.UUID(user_id)
        ).first()

        if not balance:
            balance = CreditBalance(
                id=uuid.uuid4(),
                user_id=uuid.UUID(user_id),
                balance=Decimal("0"),
            )
            self.db.add(balance)
            self.db.commit()
            self.db.refresh(balance)

        return balance

    def get_balance(self, user_id: str) -> Decimal:
        """Get current credit balance."""
        balance = self.get_or_create_balance(user_id)
        return balance.balance

    def check_sufficient_balance(self, user_id: str, required_credits: Decimal) -> bool:
        """Check if user has sufficient credits."""
        balance = self.get_balance(user_id)
        return balance >= required_credits

    # Purchase Management
    def create_purchase(
        self,
        user_id: str,
        package: str,
        payment_intent_id: str,
        is_auto_recharge: bool = False,
    ) -> CreditPurchase:
        """Create a credit purchase."""
        if package not in self.PACKAGES:
            raise BadRequestException("Invalid package")

        package_info = self.PACKAGES[package]

        purchase = CreditPurchase(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            package=package,
            credits_amount=package_info["credits"],
            price_paid=package_info["price"],
            stripe_payment_intent_id=payment_intent_id,
            payment_status="completed",
            is_auto_recharge=is_auto_recharge,
            completed_at=datetime.utcnow(),
        )
        self.db.add(purchase)

        # Add credits to balance
        self._add_credits(
            user_id=user_id,
            amount=package_info["credits"],
            transaction_type=TransactionType.PURCHASE,
            description=f"Purchased {package} package",
            purchase_id=purchase.id,
        )

        self.db.commit()
        self.db.refresh(purchase)

        return purchase

    def get_user_purchases(
        self, user_id: str, limit: int = 50
    ) -> List[CreditPurchase]:
        """Get user's purchase history."""
        purchases = (
            self.db.query(CreditPurchase)
            .filter(CreditPurchase.user_id == uuid.UUID(user_id))
            .order_by(desc(CreditPurchase.created_at))
            .limit(limit)
            .all()
        )
        return purchases

    # Usage Tracking
    def estimate_cost(
        self, resource_type: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Decimal:
        """Estimate cost for a resource execution."""
        pricing = self.db.query(CreditPricing).filter(
            CreditPricing.resource_type == resource_type,
            CreditPricing.is_active == True,
        ).first()

        if not pricing:
            # Default pricing if not configured
            return Decimal("1.0")

        base_cost = pricing.base_cost

        # Apply multipliers based on metadata
        if metadata and pricing.multipliers:
            for key, multiplier in pricing.multipliers.items():
                if key in metadata:
                    base_cost *= Decimal(str(multiplier))

        return base_cost

    def deduct_credits(
        self,
        user_id: str,
        resource_type: str,
        credits_amount: Decimal,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        execution_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CreditUsage:
        """Deduct credits for resource usage."""
        # Check balance
        if not self.check_sufficient_balance(user_id, credits_amount):
            raise BadRequestException("Insufficient credits")

        # Create usage record
        usage = CreditUsage(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            resource_type=resource_type,
            resource_id=uuid.UUID(resource_id) if resource_id else None,
            resource_name=resource_name,
            credits_used=credits_amount,
            actual_cost=credits_amount,
            execution_id=uuid.UUID(execution_id) if execution_id else None,
            meta_data=metadata or {},
            completed_at=datetime.utcnow(),
        )
        self.db.add(usage)

        # Deduct from balance
        self._deduct_credits(
            user_id=user_id,
            amount=credits_amount,
            description=f"Used {resource_type}",
            usage_id=usage.id,
        )

        # Check for low balance alerts
        self._check_balance_alerts(user_id)

        # Check auto-recharge
        self._check_auto_recharge(user_id)

        self.db.commit()
        self.db.refresh(usage)

        return usage

    def get_usage_history(
        self,
        user_id: str,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[CreditUsage]:
        """Get usage history."""
        query = self.db.query(CreditUsage).filter(
            CreditUsage.user_id == uuid.UUID(user_id)
        )

        if resource_type:
            query = query.filter(CreditUsage.resource_type == resource_type)

        if start_date:
            query = query.filter(CreditUsage.created_at >= start_date)

        if end_date:
            query = query.filter(CreditUsage.created_at <= end_date)

        usages = query.order_by(desc(CreditUsage.created_at)).limit(limit).all()
        return usages

    def get_usage_stats(
        self, user_id: str, days: int = 30
    ) -> Dict[str, Any]:
        """Get usage statistics."""
        start_date = datetime.utcnow() - timedelta(days=days)

        # Total usage
        total_usage = (
            self.db.query(func.sum(CreditUsage.credits_used))
            .filter(
                CreditUsage.user_id == uuid.UUID(user_id),
                CreditUsage.created_at >= start_date,
            )
            .scalar()
            or Decimal("0")
        )

        # Usage by resource type
        usage_by_type = (
            self.db.query(
                CreditUsage.resource_type,
                func.sum(CreditUsage.credits_used).label("total"),
                func.count(CreditUsage.id).label("count"),
            )
            .filter(
                CreditUsage.user_id == uuid.UUID(user_id),
                CreditUsage.created_at >= start_date,
            )
            .group_by(CreditUsage.resource_type)
            .all()
        )

        # Daily usage
        daily_usage = (
            self.db.query(
                func.date(CreditUsage.created_at).label("date"),
                func.sum(CreditUsage.credits_used).label("total"),
            )
            .filter(
                CreditUsage.user_id == uuid.UUID(user_id),
                CreditUsage.created_at >= start_date,
            )
            .group_by(func.date(CreditUsage.created_at))
            .order_by(func.date(CreditUsage.created_at))
            .all()
        )

        return {
            "total_usage": float(total_usage),
            "usage_by_type": [
                {
                    "resource_type": r.resource_type,
                    "total": float(r.total),
                    "count": r.count,
                }
                for r in usage_by_type
            ],
            "daily_usage": [
                {"date": d.date.isoformat(), "total": float(d.total)}
                for d in daily_usage
            ],
        }

    # Transaction History
    def get_transactions(
        self, user_id: str, limit: int = 100
    ) -> List[CreditTransaction]:
        """Get transaction history."""
        transactions = (
            self.db.query(CreditTransaction)
            .filter(CreditTransaction.user_id == uuid.UUID(user_id))
            .order_by(desc(CreditTransaction.created_at))
            .limit(limit)
            .all()
        )
        return transactions

    # Auto-recharge
    def configure_auto_recharge(
        self,
        user_id: str,
        enabled: bool,
        threshold: Optional[Decimal] = None,
        package: Optional[str] = None,
    ):
        """Configure auto-recharge settings."""
        balance = self.get_or_create_balance(user_id)

        balance.auto_recharge_enabled = enabled
        if threshold is not None:
            balance.auto_recharge_threshold = threshold
        if package:
            if package not in self.PACKAGES:
                raise BadRequestException("Invalid package")
            balance.auto_recharge_package = package
            balance.auto_recharge_amount = self.PACKAGES[package]["credits"]

        self.db.commit()

    # Alerts
    def get_alerts(self, user_id: str, unread_only: bool = False) -> List[CreditAlert]:
        """Get credit alerts."""
        query = self.db.query(CreditAlert).filter(
            CreditAlert.user_id == uuid.UUID(user_id)
        )

        if unread_only:
            query = query.filter(CreditAlert.is_read == False)

        alerts = query.order_by(desc(CreditAlert.created_at)).all()
        return alerts

    def mark_alert_read(self, alert_id: str, user_id: str):
        """Mark alert as read."""
        alert = self.db.query(CreditAlert).filter(
            CreditAlert.id == uuid.UUID(alert_id),
            CreditAlert.user_id == uuid.UUID(user_id),
        ).first()

        if alert:
            alert.is_read = True
            alert.read_at = datetime.utcnow()
            self.db.commit()

    # Helper Methods
    def _add_credits(
        self,
        user_id: str,
        amount: Decimal,
        transaction_type: TransactionType,
        description: str,
        purchase_id: Optional[uuid.UUID] = None,
    ):
        """Add credits to balance."""
        balance = self.get_or_create_balance(user_id)
        balance.balance += amount
        balance.lifetime_purchased += amount
        balance.last_purchase_at = datetime.utcnow()
        balance.updated_at = datetime.utcnow()

        # Create transaction
        transaction = CreditTransaction(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            transaction_type=transaction_type,
            amount=amount,
            balance_after=balance.balance,
            description=description,
            purchase_id=purchase_id,
        )
        self.db.add(transaction)

    def _deduct_credits(
        self,
        user_id: str,
        amount: Decimal,
        description: str,
        usage_id: Optional[uuid.UUID] = None,
    ):
        """Deduct credits from balance."""
        balance = self.get_or_create_balance(user_id)
        balance.balance -= amount
        balance.lifetime_used += amount
        balance.last_usage_at = datetime.utcnow()
        balance.updated_at = datetime.utcnow()

        # Create transaction
        transaction = CreditTransaction(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            transaction_type=TransactionType.USAGE,
            amount=-amount,  # Negative for deduction
            balance_after=balance.balance,
            description=description,
            usage_id=usage_id,
        )
        self.db.add(transaction)

    def _check_balance_alerts(self, user_id: str):
        """Check and create balance alerts."""
        balance = self.get_or_create_balance(user_id)

        # Low balance alert (below 100 credits)
        if balance.balance < Decimal("100") and balance.balance > Decimal("0"):
            # Check if alert already exists
            existing = self.db.query(CreditAlert).filter(
                CreditAlert.user_id == uuid.UUID(user_id),
                CreditAlert.alert_type == "low_balance",
                CreditAlert.is_dismissed == False,
            ).first()

            if not existing:
                alert = CreditAlert(
                    id=uuid.uuid4(),
                    user_id=uuid.UUID(user_id),
                    alert_type="low_balance",
                    threshold=Decimal("100"),
                    current_balance=balance.balance,
                )
                self.db.add(alert)

        # Depleted alert
        if balance.balance <= Decimal("0"):
            existing = self.db.query(CreditAlert).filter(
                CreditAlert.user_id == uuid.UUID(user_id),
                CreditAlert.alert_type == "depleted",
                CreditAlert.is_dismissed == False,
            ).first()

            if not existing:
                alert = CreditAlert(
                    id=uuid.uuid4(),
                    user_id=uuid.UUID(user_id),
                    alert_type="depleted",
                    current_balance=balance.balance,
                )
                self.db.add(alert)

    def _check_auto_recharge(self, user_id: str):
        """Check and trigger auto-recharge if needed."""
        balance = self.get_or_create_balance(user_id)

        if (
            balance.auto_recharge_enabled
            and balance.auto_recharge_threshold
            and balance.auto_recharge_package
            and balance.balance < balance.auto_recharge_threshold
        ):
            # Trigger auto-recharge (would integrate with payment service)
            # For now, just log that it should happen
            pass
