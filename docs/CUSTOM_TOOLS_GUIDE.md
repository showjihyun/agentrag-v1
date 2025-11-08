# Custom Tools Guide

## Overview

Custom Tools allow you to extend your agents with external API integrations without writing code. Create tools that call any REST API, test them, share them with others, and use them in your agents.

## Features

- 🔧 **No-Code Tool Builder**: Create API integrations through a visual interface
- 🧪 **Built-in Testing**: Test tools with sample data before using them
- 🌐 **Marketplace**: Share and discover tools created by the community
- ⭐ **Ratings & Reviews**: Rate and review marketplace tools
- 📊 **Usage Analytics**: Track tool performance and usage
- 🔐 **Authentication Support**: API keys, OAuth2, and Basic auth
- 🎯 **Type Safety**: Define parameter types for validation

## Getting Started

### Creating Your First Tool

1. **Navigate to Custom Tools**
   - Go to `/agent-builder/custom-tools`
   - Or click "Manage Custom Tools" in AgentWizard

2. **Click "Create Tool"**

3. **Fill in Basic Information**
   ```
   Name: Weather Lookup
   Description: Get current weather for any city
   Category: API
   Icon: 🌤️
   ```

4. **Configure API Endpoint**
   ```
   Method: GET
   URL: https://api.openweathermap.org/data/2.5/weather?q={{city}}&appid={{api_key}}
   ```

5. **Define Parameters**
   ```
   Parameter 1:
   - Name: city
   - Type: string
   - Required: Yes
   - Description: City name

   Parameter 2:
   - Name: api_key
   - Type: string
   - Required: Yes
   - Description: OpenWeatherMap API key
   ```

6. **Test the Tool**
   - Click "Test Tool"
   - Enter sample values (e.g., city: "London", api_key: "your_key")
   - Review the response

7. **Save and Use**
   - Click "Save Tool"
   - Tool is now available in AgentWizard

## Tool Configuration

### HTTP Methods

Supported methods:
- **GET**: Retrieve data
- **POST**: Create or submit data
- **PUT**: Update data
- **DELETE**: Remove data

### URL Templates

Use `{{variable}}` syntax for dynamic values:

```
https://api.example.com/users/{{userId}}/posts/{{postId}}
```

Variables are replaced with parameter values at runtime.

### Parameters

Define inputs for your tool:

```json
{
  "name": "userId",
  "type": "string",
  "required": true,
  "description": "User ID to fetch"
}
```

**Supported Types:**
- `string`: Text values
- `number`: Numeric values
- `boolean`: True/false
- `array`: List of values
- `object`: Complex nested data

### Headers

Add custom headers:

```json
{
  "Authorization": "Bearer {{api_token}}",
  "Content-Type": "application/json",
  "X-Custom-Header": "value"
}
```

### Query Parameters

Add URL query parameters:

```json
{
  "limit": "10",
  "sort": "desc",
  "filter": "{{filterValue}}"
}
```

### Request Body (POST/PUT)

Define request body template:

```json
{
  "user": {
    "name": "{{userName}}",
    "email": "{{userEmail}}"
  },
  "metadata": {
    "source": "agent"
  }
}
```

## Authentication

### API Key

```json
{
  "auth_type": "api_key",
  "auth_config": {
    "header_name": "X-API-Key",
    "key": "{{api_key}}"
  }
}
```

### Bearer Token

```json
{
  "auth_type": "bearer",
  "auth_config": {
    "token": "{{access_token}}"
  }
}
```

### Basic Auth

```json
{
  "auth_type": "basic",
  "auth_config": {
    "username": "{{username}}",
    "password": "{{password}}"
  }
}
```

## Using Custom Tools in Agents

### In AgentWizard

1. Create or edit an agent
2. Go to "Select Tools" step
3. Toggle "Custom Only" to see your custom tools
4. Select tools like built-in tools
5. Custom tools are marked with "Custom" badge

### Tool Execution

When an agent uses your custom tool:

1. Agent determines tool is needed
2. Agent provides parameter values
3. Tool makes HTTP request
4. Response is returned to agent
5. Agent uses response in reasoning

## Marketplace

### Sharing Your Tools

1. Edit your tool
2. Enable "Public" to make it visible
3. Enable "Marketplace" to feature it
4. Other users can clone and rate it

### Using Marketplace Tools

1. Go to "Marketplace" tab
2. Browse featured tools
3. Click a tool to view details
4. Click "Add to My Tools" to clone
5. Rate and review tools you use

### Rating Tools

- 1-5 star rating
- Optional written review
- Helps others find quality tools
- Improves tool discoverability

## Best Practices

### Tool Design

1. **Clear Names**: Use descriptive, action-oriented names
   - ✅ "Get GitHub User Info"
   - ❌ "GitHub Tool"

2. **Good Descriptions**: Explain what the tool does and when to use it
   ```
   Get detailed information about a GitHub user including their
   repositories, followers, and profile data. Use this when you
   need to look up GitHub user details.
   ```

3. **Required vs Optional**: Mark parameters appropriately
   - Required: Essential for tool to work
   - Optional: Provide defaults or make conditional

4. **Type Safety**: Use correct parameter types
   - Helps with validation
   - Improves agent understanding
   - Prevents errors

### API Integration

1. **Error Handling**: Test with invalid inputs
2. **Rate Limits**: Be aware of API rate limits
3. **Timeouts**: Tools timeout after 30 seconds
4. **Response Size**: Large responses may be truncated

### Security

1. **API Keys**: Never hardcode keys in URLs
   - ✅ Use parameters: `{{api_key}}`
   - ❌ Hardcode: `?key=abc123`

2. **Sensitive Data**: Don't expose in public tools
3. **HTTPS Only**: Always use HTTPS endpoints
4. **Validate Inputs**: Define parameter types

## Examples

### Example 1: GitHub User Lookup

```json
{
  "name": "GitHub User Info",
  "description": "Get GitHub user profile information",
  "category": "api",
  "icon": "🐙",
  "method": "GET",
  "url": "https://api.github.com/users/{{username}}",
  "parameters": [
    {
      "name": "username",
      "type": "string",
      "required": true,
      "description": "GitHub username"
    }
  ]
}
```

### Example 2: Send Slack Message

```json
{
  "name": "Send Slack Message",
  "description": "Post a message to a Slack channel",
  "category": "communication",
  "icon": "💬",
  "method": "POST",
  "url": "https://slack.com/api/chat.postMessage",
  "headers": {
    "Authorization": "Bearer {{slack_token}}",
    "Content-Type": "application/json"
  },
  "body_template": {
    "channel": "{{channel}}",
    "text": "{{message}}"
  },
  "parameters": [
    {
      "name": "slack_token",
      "type": "string",
      "required": true,
      "description": "Slack Bot Token"
    },
    {
      "name": "channel",
      "type": "string",
      "required": true,
      "description": "Channel ID or name"
    },
    {
      "name": "message",
      "type": "string",
      "required": true,
      "description": "Message text"
    }
  ]
}
```

### Example 3: Database Query

```json
{
  "name": "Query Database",
  "description": "Execute a SQL query via REST API",
  "category": "data",
  "icon": "🗄️",
  "method": "POST",
  "url": "https://api.example.com/query",
  "headers": {
    "Authorization": "Bearer {{db_token}}"
  },
  "body_template": {
    "query": "{{sql_query}}",
    "database": "{{database_name}}"
  },
  "parameters": [
    {
      "name": "db_token",
      "type": "string",
      "required": true,
      "description": "Database API token"
    },
    {
      "name": "database_name",
      "type": "string",
      "required": true,
      "description": "Database name"
    },
    {
      "name": "sql_query",
      "type": "string",
      "required": true,
      "description": "SQL query to execute"
    }
  ]
}
```

## Troubleshooting

### Tool Test Fails

**Problem**: Tool test returns an error

**Solutions**:
1. Check URL is correct and accessible
2. Verify parameter values are valid
3. Check authentication credentials
4. Review API documentation
5. Check for rate limiting

### Tool Not Appearing in AgentWizard

**Problem**: Custom tool doesn't show in tool selector

**Solutions**:
1. Refresh the page
2. Check tool was saved successfully
3. Try toggling "Custom Only" filter
4. Check browser console for errors

### Agent Can't Use Tool

**Problem**: Agent fails when trying to use custom tool

**Solutions**:
1. Verify tool works in test mode
2. Check parameter types match agent's values
3. Review tool execution logs
4. Check for API rate limits or downtime

### Slow Tool Execution

**Problem**: Tool takes too long to execute

**Solutions**:
1. Check API response time
2. Reduce response size if possible
3. Consider caching for repeated calls
4. Check network connectivity

## API Reference

### Endpoints

```
GET    /api/agent-builder/custom-tools              # List tools
POST   /api/agent-builder/custom-tools              # Create tool
GET    /api/agent-builder/custom-tools/{id}         # Get tool
PUT    /api/agent-builder/custom-tools/{id}         # Update tool
DELETE /api/agent-builder/custom-tools/{id}         # Delete tool
POST   /api/agent-builder/custom-tools/{id}/test    # Test tool
POST   /api/agent-builder/custom-tools/{id}/clone   # Clone tool
GET    /api/agent-builder/custom-tools/{id}/usage   # Get usage stats
GET    /api/agent-builder/custom-tools/marketplace/featured  # Featured tools
POST   /api/agent-builder/custom-tools/{id}/rate    # Rate tool
GET    /api/agent-builder/custom-tools/{id}/ratings # Get ratings
```

### Tool Object

```typescript
interface CustomTool {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  category: string;
  icon: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  url: string;
  headers?: Record<string, string>;
  query_params?: Record<string, string>;
  body_template?: Record<string, any>;
  parameters: Parameter[];
  outputs?: Output[];
  requires_auth: boolean;
  auth_type?: 'api_key' | 'oauth2' | 'basic';
  auth_config?: Record<string, any>;
  is_public: boolean;
  is_marketplace: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

interface Parameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  required: boolean;
  description: string;
}
```

## Advanced Topics

### Response Mapping

Define how to extract data from API responses:

```json
{
  "outputs": [
    {
      "name": "user_name",
      "path": "data.user.name"
    },
    {
      "name": "user_email",
      "path": "data.user.email"
    }
  ]
}
```

### Conditional Logic

Use template variables for conditional behavior:

```
URL: https://api.example.com/{{endpoint}}?mode={{mode}}
```

Agent can dynamically choose endpoint and mode.

### Batch Operations

Create tools that process multiple items:

```json
{
  "parameters": [
    {
      "name": "user_ids",
      "type": "array",
      "description": "List of user IDs to process"
    }
  ]
}
```

## Support & Resources

- **Documentation**: `/docs/CUSTOM_TOOLS_GUIDE.md`
- **API Test Script**: `test_custom_tools_api.py`
- **Examples**: See marketplace for community tools
- **Issues**: Check browser console and backend logs

## Changelog

### v1.0.0 (Current)
- Initial release
- Tool builder UI
- Marketplace
- Rating system
- Usage analytics
- AgentWizard integration

### Planned Features
- OAuth2 flow support
- Webhook support
- Tool versioning
- OpenAPI import
- Code generation
- Advanced analytics
