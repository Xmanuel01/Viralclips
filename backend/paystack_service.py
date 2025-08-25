import os
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from paystackapi.paystack import Paystack
from paystackapi.transaction import Transaction
from paystackapi.plan import Plan
from paystackapi.customer import Customer


class PaystackService:
    def __init__(self):
        self.secret_key = os.environ.get("PAYSTACK_SECRET_KEY")
        self.public_key = os.environ.get("PAYSTACK_PUBLIC_KEY")
        self.webhook_secret = os.environ.get("PAYSTACK_WEBHOOK_SECRET")
        
        if not self.secret_key:
            raise ValueError("PAYSTACK_SECRET_KEY environment variable is required")
        
        # Initialize Paystack
        Paystack.secret_key = self.secret_key
    
    def create_customer(self, email: str, user_id: str) -> Dict[str, Any]:
        """Create a customer in Paystack."""
        try:
            response = Customer.create(
                email=email,
                metadata={
                    "user_id": user_id,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            return response
        except Exception as e:
            print(f"Error creating Paystack customer: {str(e)}")
            raise
    
    def create_subscription_plans(self):
        """Create subscription plans in Paystack."""
        try:
            # Premium Monthly Plan
            premium_plan = Plan.create(
                name="Premium Monthly",
                amount=1500 * 100,  # $15 in kobo (Paystack uses kobo for NGN, cents for USD)
                interval="monthly",
                description="Premium plan with 1080p exports, no watermark, 20 clips/day",
                currency="USD"
            )
            
            # Lifetime Plan
            lifetime_plan = Plan.create(
                name="Lifetime Access",
                amount=9900 * 100,  # $99 in cents
                interval="annually",  # We'll handle lifetime logic separately
                description="One-time payment for lifetime access to all premium features",
                currency="USD"
            )
            
            return {
                "premium_monthly": premium_plan,
                "lifetime": lifetime_plan
            }
            
        except Exception as e:
            print(f"Error creating Paystack plans: {str(e)}")
            raise
    
    def initialize_transaction(self, email: str, amount: int, plan_code: str = None, 
                            metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Initialize a transaction for subscription or one-time payment."""
        try:
            transaction_data = {
                "email": email,
                "amount": amount,  # Amount in kobo/cents
                "currency": "USD",
                "callback_url": f"{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/payment/callback",
                "metadata": metadata or {}
            }
            
            if plan_code:
                transaction_data["plan"] = plan_code
            
            response = Transaction.initialize(**transaction_data)
            return response
            
        except Exception as e:
            print(f"Error initializing Paystack transaction: {str(e)}")
            raise
    
    def verify_transaction(self, reference: str) -> Dict[str, Any]:
        """Verify a transaction using its reference."""
        try:
            response = Transaction.verify(reference=reference)
            return response
        except Exception as e:
            print(f"Error verifying Paystack transaction: {str(e)}")
            raise
    
    def create_subscription(self, customer_email: str, plan_code: str, 
                          authorization_code: str = None) -> Dict[str, Any]:
        """Create a subscription for a customer."""
        try:
            from paystackapi.subscription import Subscription
            
            subscription_data = {
                "customer": customer_email,
                "plan": plan_code
            }
            
            if authorization_code:
                subscription_data["authorization"] = authorization_code
            
            response = Subscription.create(**subscription_data)
            return response
            
        except Exception as e:
            print(f"Error creating Paystack subscription: {str(e)}")
            raise
    
    def cancel_subscription(self, subscription_code: str, token: str) -> Dict[str, Any]:
        """Cancel a subscription."""
        try:
            from paystackapi.subscription import Subscription
            
            response = Subscription.disable(
                code=subscription_code,
                token=token
            )
            return response
            
        except Exception as e:
            print(f"Error canceling Paystack subscription: {str(e)}")
            raise
    
    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature from Paystack."""
        try:
            if not self.webhook_secret:
                return False
            
            # Compute expected signature
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha512
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            print(f"Error verifying Paystack webhook: {str(e)}")
            return False
    
    def get_payment_url(self, email: str, amount: int, plan_type: str, user_id: str) -> str:
        """Get payment URL for a specific plan."""
        try:
            metadata = {
                "user_id": user_id,
                "plan_type": plan_type,
                "upgrade_timestamp": datetime.utcnow().isoformat()
            }
            
            response = self.initialize_transaction(
                email=email,
                amount=amount,
                metadata=metadata
            )
            
            return response["data"]["authorization_url"]
            
        except Exception as e:
            print(f"Error getting Paystack payment URL: {str(e)}")
            raise
    
    def process_successful_payment(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a successful payment and return subscription details."""
        try:
            metadata = transaction_data.get("metadata", {})
            user_id = metadata.get("user_id")
            plan_type = metadata.get("plan_type")
            amount = transaction_data.get("amount", 0) / 100  # Convert from kobo/cents
            
            if plan_type == "premium":
                # Monthly subscription
                subscription_tier = "premium"
                expires_at = datetime.utcnow() + timedelta(days=30)
            elif plan_type == "lifetime":
                # Lifetime access
                subscription_tier = "lifetime"
                expires_at = datetime.utcnow() + timedelta(days=36500)  # 100 years
            else:
                raise ValueError(f"Unknown plan type: {plan_type}")
            
            return {
                "user_id": user_id,
                "subscription_tier": subscription_tier,
                "expires_at": expires_at,
                "amount_paid": amount,
                "plan_type": plan_type,
                "transaction_reference": transaction_data.get("reference"),
                "customer_email": transaction_data.get("customer", {}).get("email")
            }
            
        except Exception as e:
            print(f"Error processing successful payment: {str(e)}")
            raise


# Paystack pricing configuration
PAYSTACK_PLANS = {
    "premium": {
        "name": "Premium Monthly",
        "amount": 1500,  # $15.00 in cents
        "currency": "USD",
        "interval": "monthly",
        "description": "Premium plan with 1080p exports, no watermark, 20 clips/day"
    },
    "lifetime": {
        "name": "Lifetime Access",
        "amount": 9900,  # $99.00 in cents
        "currency": "USD",
        "interval": "one-time",
        "description": "One-time payment for lifetime access to all premium features"
    }
}


def get_plan_amount(plan_type: str) -> int:
    """Get the amount for a specific plan in cents."""
    plan = PAYSTACK_PLANS.get(plan_type)
    if not plan:
        raise ValueError(f"Unknown plan type: {plan_type}")
    return plan["amount"] * 100  # Convert to kobo/cents
