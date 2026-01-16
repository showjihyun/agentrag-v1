"""Payment service for Stripe integration."""
from typing import Dict, Any, Optional
from decimal import Decimal
import os

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False

from backend.config import settings
from backend.exceptions import ValidationException as BadRequestException


class PaymentService:
    """Service for handling payments via Stripe."""

    def __init__(self):
        if STRIPE_AVAILABLE:
            stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
            self.stripe_enabled = bool(stripe.api_key)
        else:
            self.stripe_enabled = False

    def create_payment_intent(
        self,
        amount: Decimal,
        currency: str = "usd",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a Stripe payment intent."""
        if not self.stripe_enabled:
            raise BadRequestException("Stripe is not configured")

        try:
            # Convert amount to cents
            amount_cents = int(amount * 100)

            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                metadata=metadata or {},
                automatic_payment_methods={"enabled": True},
            )

            return {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
                "amount": amount,
                "currency": currency,
            }
        except stripe.error.StripeError as e:
            raise BadRequestException(f"Payment error: {str(e)}")

    def confirm_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """Confirm a payment intent."""
        if not self.stripe_enabled:
            raise BadRequestException("Stripe is not configured")

        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            return {
                "status": intent.status,
                "amount": Decimal(intent.amount) / 100,
                "currency": intent.currency,
                "payment_method": intent.payment_method,
            }
        except stripe.error.StripeError as e:
            raise BadRequestException(f"Payment confirmation error: {str(e)}")

    def create_refund(
        self, payment_intent_id: str, amount: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """Create a refund for a payment."""
        if not self.stripe_enabled:
            raise BadRequestException("Stripe is not configured")

        try:
            refund_params = {"payment_intent": payment_intent_id}
            if amount:
                refund_params["amount"] = int(amount * 100)

            refund = stripe.Refund.create(**refund_params)

            return {
                "refund_id": refund.id,
                "status": refund.status,
                "amount": Decimal(refund.amount) / 100,
            }
        except stripe.error.StripeError as e:
            raise BadRequestException(f"Refund error: {str(e)}")

    def create_customer(self, email: str, name: Optional[str] = None) -> str:
        """Create a Stripe customer."""
        if not self.stripe_enabled:
            raise BadRequestException("Stripe is not configured")

        try:
            customer = stripe.Customer.create(email=email, name=name)
            return customer.id
        except stripe.error.StripeError as e:
            raise BadRequestException(f"Customer creation error: {str(e)}")

    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a subscription for a customer."""
        if not self.stripe_enabled:
            raise BadRequestException("Stripe is not configured")

        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                metadata=metadata or {},
            )

            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "current_period_end": subscription.current_period_end,
            }
        except stripe.error.StripeError as e:
            raise BadRequestException(f"Subscription error: {str(e)}")

    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel a subscription."""
        if not self.stripe_enabled:
            raise BadRequestException("Stripe is not configured")

        try:
            subscription = stripe.Subscription.delete(subscription_id)

            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
            }
        except stripe.error.StripeError as e:
            raise BadRequestException(f"Subscription cancellation error: {str(e)}")

    def create_payout(
        self, amount: Decimal, destination: str, currency: str = "usd"
    ) -> Dict[str, Any]:
        """Create a payout to a connected account."""
        if not self.stripe_enabled:
            raise BadRequestException("Stripe is not configured")

        try:
            # Convert amount to cents
            amount_cents = int(amount * 100)

            payout = stripe.Payout.create(
                amount=amount_cents,
                currency=currency,
                destination=destination,
            )

            return {
                "payout_id": payout.id,
                "status": payout.status,
                "amount": amount,
            }
        except stripe.error.StripeError as e:
            raise BadRequestException(f"Payout error: {str(e)}")

    def webhook_construct_event(
        self, payload: bytes, sig_header: str, webhook_secret: str
    ) -> Any:
        """Construct and verify a webhook event."""
        if not self.stripe_enabled:
            raise BadRequestException("Stripe is not configured")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            return event
        except ValueError:
            raise BadRequestException("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise BadRequestException("Invalid signature")
