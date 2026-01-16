# Agentic RAG Python SDK

Official Python client library for the Agentic RAG platform.

## Installation

```bash
pip install agentic-rag
```

## Quick Start

```python
from agentic_rag import AgenticRAGClient

# Initialize client
client = AgenticRAGClient(api_key="your-api-key")

# List agents
agents = client.agents.list()

# Execute workflow
result = client.workflows.execute(
    workflow_id="workflow-123",
    input_data={"query": "What is AI?"}
)

# Check credit balance
balance = client.credits.get_balance()
print(f"Credits remaining: {balance['balance']}")
```

## Features

### Agents

```python
# List agents
agents = client.agents.list(limit=10)

# Get agent
agent = client.agents.get("agent-123")

# Create agent
agent = client.agents.create(
    name="My Agent",
    agent_type="custom",
    llm_provider="openai",
    llm_model="gpt-4"
)

# Execute agent
result = client.agents.execute(
    agent_id="agent-123",
    input_data={"query": "Hello"}
)

# Update agent
client.agents.update("agent-123", name="Updated Name")

# Delete agent
client.agents.delete("agent-123")
```

### Workflows

```python
# List workflows
workflows = client.workflows.list()

# Execute workflow
result = client.workflows.execute(
    workflow_id="workflow-123",
    input_data={"query": "Test"}
)

# Get execution status
execution = client.workflows.get_execution("execution-123")
```

### Credits

```python
# Get balance
balance = client.credits.get_balance()

# List packages
packages = client.credits.list_packages()

# Purchase credits
intent = client.credits.purchase(package="pro")

# Get usage stats
stats = client.credits.get_usage_stats(days=30)

# Configure auto-recharge
client.credits.configure_auto_recharge(
    enabled=True,
    threshold=100.0,
    package="starter"
)
```

### Webhooks

```python
# Create webhook
webhook = client.webhooks.create(
    agent_id="agent-123",
    name="My Webhook",
    auth_type="bearer"
)
print(f"Webhook URL: {webhook['url']}")
print(f"Secret: {webhook['secret']}")

# List webhooks
webhooks = client.webhooks.list()

# Test webhook
result = client.webhooks.test(
    webhook_id="webhook-123",
    payload={"test": "data"}
)

# Regenerate secret
new_secret = client.webhooks.regenerate_secret("webhook-123")

# Delete webhook
client.webhooks.delete("webhook-123")
```

### Marketplace

```python
# List items
items = client.marketplace.list_items(category="agents")

# Get item
item = client.marketplace.get_item("item-123")

# Purchase item
intent = client.marketplace.purchase("item-123")

# List purchases
purchases = client.marketplace.list_purchases()

# Create review
review = client.marketplace.create_review(
    item_id="item-123",
    rating=5,
    title="Great agent!",
    comment="Works perfectly"
)
```

### Organizations

```python
# List organizations
orgs = client.organizations.list()

# Create organization
org = client.organizations.create(
    name="My Company",
    slug="my-company"
)

# Invite member
client.organizations.invite_member(
    org_id="org-123",
    email="user@example.com",
    role="member"
)

# List members
members = client.organizations.list_members("org-123")
```

## Error Handling

```python
from agentic_rag import (
    AgenticRAGError,
    AuthenticationError,
    RateLimitError,
    ResourceNotFoundError,
    InsufficientCreditsError
)

try:
    result = client.agents.execute("agent-123", {"query": "test"})
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limit exceeded. Retry after {e.retry_after}s")
except InsufficientCreditsError:
    print("Not enough credits")
except ResourceNotFoundError:
    print("Agent not found")
except AgenticRAGError as e:
    print(f"API error: {e.message}")
```

## Configuration

```python
# Custom base URL
client = AgenticRAGClient(
    api_key="your-api-key",
    base_url="https://custom.api.com",
    timeout=60  # Request timeout in seconds
)
```

## Rate Limiting

The SDK automatically handles rate limiting with appropriate error messages. When rate limited, a `RateLimitError` is raised with a `retry_after` attribute indicating when to retry.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- Documentation: https://docs.agenticrag.com
- Email: support@agenticrag.com
- GitHub Issues: https://github.com/agenticrag/python-sdk/issues
