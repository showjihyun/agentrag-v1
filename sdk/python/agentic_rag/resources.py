"""Resource managers for Agentic RAG SDK."""
from typing import Dict, Any, Optional, List


class BaseResource:
    """Base class for resource managers."""
    
    def __init__(self, client):
        self.client = client


class AgentsResource(BaseResource):
    """Manage agents."""
    
    def list(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """List all agents."""
        return self.client.get("/api/v1/agents", params={"limit": limit, "offset": offset})
    
    def get(self, agent_id: str) -> Dict[str, Any]:
        """Get agent by ID."""
        return self.client.get(f"/api/v1/agents/{agent_id}")
    
    def create(self, name: str, agent_type: str, **kwargs) -> Dict[str, Any]:
        """Create a new agent."""
        data = {"name": name, "agent_type": agent_type, **kwargs}
        return self.client.post("/api/v1/agents", data=data)
    
    def update(self, agent_id: str, **kwargs) -> Dict[str, Any]:
        """Update agent."""
        return self.client.patch(f"/api/v1/agents/{agent_id}", data=kwargs)
    
    def delete(self, agent_id: str) -> None:
        """Delete agent."""
        self.client.delete(f"/api/v1/agents/{agent_id}")
    
    def execute(self, agent_id: str, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute agent."""
        data = {"input_data": input_data, **kwargs}
        return self.client.post(f"/api/v1/agents/{agent_id}/execute", data=data)


class WorkflowsResource(BaseResource):
    """Manage workflows."""
    
    def list(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """List all workflows."""
        return self.client.get("/api/v1/workflows", params={"limit": limit, "offset": offset})
    
    def get(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow by ID."""
        return self.client.get(f"/api/v1/workflows/{workflow_id}")
    
    def create(self, name: str, **kwargs) -> Dict[str, Any]:
        """Create a new workflow."""
        data = {"name": name, **kwargs}
        return self.client.post("/api/v1/workflows", data=data)
    
    def update(self, workflow_id: str, **kwargs) -> Dict[str, Any]:
        """Update workflow."""
        return self.client.patch(f"/api/v1/workflows/{workflow_id}", data=kwargs)
    
    def delete(self, workflow_id: str) -> None:
        """Delete workflow."""
        self.client.delete(f"/api/v1/workflows/{workflow_id}")
    
    def execute(self, workflow_id: str, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute workflow."""
        data = {"input_data": input_data, **kwargs}
        return self.client.post(f"/api/v1/workflows/{workflow_id}/execute", data=data)
    
    def get_execution(self, execution_id: str) -> Dict[str, Any]:
        """Get execution status."""
        return self.client.get(f"/api/v1/executions/{execution_id}")


class CreditsResource(BaseResource):
    """Manage credits."""
    
    def get_balance(self) -> Dict[str, Any]:
        """Get current credit balance."""
        return self.client.get("/api/v1/credits/balance")
    
    def list_packages(self) -> List[Dict[str, Any]]:
        """List available credit packages."""
        return self.client.get("/api/v1/credits/packages")
    
    def purchase(self, package: str) -> Dict[str, Any]:
        """Purchase credits."""
        # First create payment intent
        intent = self.client.post("/api/v1/credits/purchase/intent", data={"package": package})
        return intent
    
    def get_usage_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get usage statistics."""
        return self.client.get("/api/v1/credits/usage/stats", params={"days": days})
    
    def list_transactions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List credit transactions."""
        return self.client.get("/api/v1/credits/transactions", params={"limit": limit})
    
    def configure_auto_recharge(
        self, enabled: bool, threshold: Optional[float] = None, package: Optional[str] = None
    ) -> Dict[str, Any]:
        """Configure auto-recharge."""
        data = {"enabled": enabled}
        if threshold is not None:
            data["threshold"] = threshold
        if package is not None:
            data["package"] = package
        return self.client.post("/api/v1/credits/auto-recharge/configure", data=data)


class WebhooksResource(BaseResource):
    """Manage webhooks."""
    
    def list(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all webhooks."""
        params = {}
        if agent_id:
            params["agent_id"] = agent_id
        return self.client.get("/api/v1/webhooks", params=params)
    
    def get(self, webhook_id: str) -> Dict[str, Any]:
        """Get webhook by ID."""
        return self.client.get(f"/api/v1/webhooks/{webhook_id}")
    
    def create(
        self,
        agent_id: str,
        name: str,
        auth_type: str = "bearer",
        allowed_methods: List[str] = None,
    ) -> Dict[str, Any]:
        """Create a new webhook."""
        data = {
            "agent_id": agent_id,
            "name": name,
            "auth_type": auth_type,
            "allowed_methods": allowed_methods or ["POST"],
        }
        return self.client.post("/api/v1/webhooks", data=data)
    
    def update(self, webhook_id: str, **kwargs) -> Dict[str, Any]:
        """Update webhook."""
        return self.client.patch(f"/api/v1/webhooks/{webhook_id}", data=kwargs)
    
    def delete(self, webhook_id: str) -> None:
        """Delete webhook."""
        self.client.delete(f"/api/v1/webhooks/{webhook_id}")
    
    def test(self, webhook_id: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        """Test webhook."""
        data = {"payload": payload or {}}
        return self.client.post(f"/api/v1/webhooks/{webhook_id}/test", data=data)
    
    def regenerate_secret(self, webhook_id: str) -> Dict[str, Any]:
        """Regenerate webhook secret."""
        return self.client.post(f"/api/v1/webhooks/{webhook_id}/regenerate-secret")


class MarketplaceResource(BaseResource):
    """Manage marketplace items."""
    
    def list_items(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """List marketplace items."""
        params = {"limit": limit}
        if category:
            params["category"] = category
        if search:
            params["search"] = search
        return self.client.get("/api/v1/marketplace/items", params=params)
    
    def get_item(self, item_id: str) -> Dict[str, Any]:
        """Get marketplace item."""
        return self.client.get(f"/api/v1/marketplace/items/{item_id}")
    
    def purchase(self, item_id: str) -> Dict[str, Any]:
        """Purchase marketplace item."""
        # First create payment intent
        intent = self.client.post(
            "/api/v1/marketplace/payment-intent",
            data={"item_id": item_id}
        )
        return intent
    
    def list_purchases(self) -> List[Dict[str, Any]]:
        """List user's purchases."""
        return self.client.get("/api/v1/marketplace/purchases")
    
    def create_review(
        self, item_id: str, rating: int, title: Optional[str] = None, comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a review."""
        data = {"rating": rating}
        if title:
            data["title"] = title
        if comment:
            data["comment"] = comment
        return self.client.post(f"/api/v1/marketplace/items/{item_id}/reviews", data=data)


class OrganizationsResource(BaseResource):
    """Manage organizations."""
    
    def list(self) -> List[Dict[str, Any]]:
        """List user's organizations."""
        return self.client.get("/organizations")
    
    def get(self, org_id: str) -> Dict[str, Any]:
        """Get organization."""
        return self.client.get(f"/organizations/{org_id}")
    
    def create(self, name: str, slug: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create organization."""
        data = {"name": name, "slug": slug}
        if description:
            data["description"] = description
        return self.client.post("/organizations", data=data)
    
    def update(self, org_id: str, **kwargs) -> Dict[str, Any]:
        """Update organization."""
        return self.client.put(f"/organizations/{org_id}", data=kwargs)
    
    def delete(self, org_id: str) -> None:
        """Delete organization."""
        self.client.delete(f"/organizations/{org_id}")
    
    def list_members(self, org_id: str) -> List[Dict[str, Any]]:
        """List organization members."""
        return self.client.get(f"/organizations/{org_id}/members")
    
    def invite_member(self, org_id: str, email: str, role: str = "member") -> Dict[str, Any]:
        """Invite member to organization."""
        data = {"email": email, "role": role}
        return self.client.post(f"/organizations/{org_id}/members", data=data)
