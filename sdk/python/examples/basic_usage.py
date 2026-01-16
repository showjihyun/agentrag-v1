"""Basic usage examples for Agentic RAG SDK."""
import os
from agentic_rag import AgenticRAGClient

# Initialize client
api_key = os.getenv("AGENTIC_RAG_API_KEY")
client = AgenticRAGClient(api_key=api_key)


def example_agents():
    """Example: Working with agents."""
    print("=== Agents Example ===")
    
    # List agents
    agents = client.agents.list(limit=5)
    print(f"Found {len(agents)} agents")
    
    # Create agent
    agent = client.agents.create(
        name="Example Agent",
        agent_type="custom",
        llm_provider="openai",
        llm_model="gpt-4",
        description="An example agent"
    )
    print(f"Created agent: {agent['id']}")
    
    # Execute agent
    result = client.agents.execute(
        agent_id=agent['id'],
        input_data={"query": "What is artificial intelligence?"}
    )
    print(f"Execution result: {result}")
    
    # Clean up
    client.agents.delete(agent['id'])
    print("Agent deleted")


def example_credits():
    """Example: Managing credits."""
    print("\n=== Credits Example ===")
    
    # Get balance
    balance = client.credits.get_balance()
    print(f"Current balance: {balance['balance']} credits")
    print(f"Lifetime purchased: {balance['lifetime_purchased']}")
    print(f"Lifetime used: {balance['lifetime_used']}")
    
    # List packages
    packages = client.credits.list_packages()
    print("\nAvailable packages:")
    for pkg in packages:
        print(f"  - {pkg['package']}: {pkg['credits']} credits for ${pkg['price']}")
    
    # Get usage stats
    stats = client.credits.get_usage_stats(days=7)
    print(f"\nTotal usage (7 days): {stats['total_usage']} credits")
    
    # Configure auto-recharge
    client.credits.configure_auto_recharge(
        enabled=True,
        threshold=100.0,
        package="starter"
    )
    print("Auto-recharge configured")


def example_webhooks():
    """Example: Working with webhooks."""
    print("\n=== Webhooks Example ===")
    
    # Assume we have an agent
    agents = client.agents.list(limit=1)
    if not agents:
        print("No agents available")
        return
    
    agent_id = agents[0]['id']
    
    # Create webhook
    webhook = client.webhooks.create(
        agent_id=agent_id,
        name="Example Webhook",
        auth_type="bearer"
    )
    print(f"Created webhook: {webhook['url']}")
    print(f"Secret: {webhook['secret']}")
    
    # Test webhook
    result = client.webhooks.test(
        webhook_id=webhook['id'],
        payload={"test": "data"}
    )
    print(f"Test result: {result}")
    
    # Clean up
    client.webhooks.delete(webhook['id'])
    print("Webhook deleted")


def example_marketplace():
    """Example: Using marketplace."""
    print("\n=== Marketplace Example ===")
    
    # List items
    items = client.marketplace.list_items(limit=5)
    print(f"Found {len(items)} marketplace items")
    
    if items:
        item = items[0]
        print(f"\nItem: {item['name']}")
        print(f"Description: {item.get('description', 'N/A')}")
        print(f"Rating: {item.get('rating', 0)}/5")
        
        # Check if purchased
        purchases = client.marketplace.list_purchases()
        purchased_ids = [p['item_id'] for p in purchases]
        
        if item['id'] in purchased_ids:
            print("Already purchased!")
        else:
            print("Not purchased yet")


def example_error_handling():
    """Example: Error handling."""
    print("\n=== Error Handling Example ===")
    
    from agentic_rag import (
        AuthenticationError,
        RateLimitError,
        ResourceNotFoundError,
        InsufficientCreditsError
    )
    
    try:
        # Try to get non-existent agent
        client.agents.get("non-existent-id")
    except ResourceNotFoundError:
        print("Caught ResourceNotFoundError (expected)")
    
    try:
        # Try with invalid API key
        bad_client = AgenticRAGClient(api_key="invalid-key")
        bad_client.agents.list()
    except AuthenticationError:
        print("Caught AuthenticationError (expected)")


if __name__ == "__main__":
    # Run examples
    try:
        example_agents()
        example_credits()
        example_webhooks()
        example_marketplace()
        example_error_handling()
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
