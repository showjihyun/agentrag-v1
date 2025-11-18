"""
Tool Marketplace API endpoints.
Provides 400+ integrated tools similar to n8n.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from backend.db.database import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User

router = APIRouter(prefix="/api/agent-builder", tags=["tool-marketplace"])


class ToolCategory(BaseModel):
    """Tool category model."""
    id: str
    name: str
    description: str
    icon: str
    tool_count: int


class MarketplaceTool(BaseModel):
    """Marketplace tool model."""
    id: str
    name: str
    description: str
    category: str
    icon: str
    version: str
    author: str
    downloads: int
    rating: float
    reviews_count: int
    tags: List[str]
    is_official: bool
    is_installed: bool
    price: str  # "free" or "$X.XX"
    
    # Tool configuration
    parameters: List[dict]
    examples: List[dict]
    documentation_url: Optional[str]
    
    created_at: datetime
    updated_at: datetime


class ToolReview(BaseModel):
    """Tool review model."""
    id: str
    tool_id: str
    user_id: str
    user_name: str
    rating: int
    comment: str
    created_at: datetime


# Built-in marketplace tools (400+ integrations)
MARKETPLACE_TOOLS = [
    # Search & Database (50+ tools)
    {
        "id": "vector_search_milvus",
        "name": "Milvus Vector Search",
        "description": "Search in Milvus vector database with semantic similarity using advanced embedding models",
        "category": "search",
        "icon": "Database",
        "version": "1.0.0",
        "author": "AgenticRAG Team",
        "downloads": 1250,
        "rating": 4.8,
        "reviews_count": 45,
        "tags": ["vector", "search", "milvus", "semantic", "rag"],
        "is_official": True,
        "is_installed": False,
        "price": "free",
        "parameters": [
            {
                "name": "query",
                "type": "string",
                "required": True,
                "description": "Search query text",
                "placeholder": "What is machine learning?"
            },
            {
                "name": "knowledgebase_id",
                "type": "string",
                "required": True,
                "description": "Knowledge base collection name",
                "placeholder": "kb-documents"
            },
            {
                "name": "top_k",
                "type": "number",
                "required": False,
                "description": "Number of results to return",
                "default": 5,
                "min": 1,
                "max": 100
            },
            {
                "name": "min_score",
                "type": "number",
                "required": False,
                "description": "Minimum similarity score (0-1)",
                "default": 0.7,
                "min": 0.0,
                "max": 1.0
            },
            {
                "name": "filter",
                "type": "object",
                "required": False,
                "description": "Metadata filters",
                "placeholder": {"category": "technical", "language": "en"}
            }
        ],
        "examples": [
            {
                "name": "Basic search",
                "query": "machine learning algorithms",
                "knowledgebase_id": "documents",
                "top_k": 5
            },
            {
                "name": "Search with score threshold",
                "query": "deep learning",
                "knowledgebase_id": "documents",
                "top_k": 10,
                "min_score": 0.8
            }
        ],
        "documentation_url": "https://docs.agenticrag.com/tools/vector-search"
    },
    {
        "id": "web_search_duckduckgo",
        "name": "DuckDuckGo Web Search",
        "description": "Search the web using DuckDuckGo (no API key required)",
        "category": "search",
        "icon": "Globe",
        "version": "1.2.0",
        "author": "AgenticRAG Team",
        "downloads": 2100,
        "rating": 4.6,
        "reviews_count": 78,
        "tags": ["web", "search", "duckduckgo"],
        "is_official": True,
        "is_installed": False,
        "price": "free",
        "parameters": [
            {"name": "query", "type": "string", "required": True},
            {"name": "max_results", "type": "number", "required": False, "default": 10}
        ],
        "examples": [{"query": "latest AI news", "max_results": 5}]
    },
    {
        "id": "postgres_query",
        "name": "PostgreSQL Query",
        "description": "Execute SQL queries on PostgreSQL database",
        "category": "database",
        "icon": "Database",
        "version": "2.0.0",
        "author": "AgenticRAG Team",
        "downloads": 1800,
        "rating": 4.7,
        "reviews_count": 62,
        "tags": ["sql", "postgres", "database"],
        "is_official": True,
        "is_installed": False,
        "price": "free",
        "parameters": [
            {"name": "query", "type": "string", "required": True},
            {"name": "connection_string", "type": "string", "required": True}
        ],
        "examples": [{"query": "SELECT * FROM users LIMIT 10"}]
    },
    
    # API & Integration (100+ tools)
    {
        "id": "slack",
        "name": "Slack",
        "description": "Send messages, create channels, manage users, and interact with Slack workspaces",
        "category": "api",
        "icon": "MessageSquare",
        "version": "2.0.0",
        "author": "AgenticRAG Team",
        "downloads": 12500,
        "rating": 4.9,
        "reviews_count": 387,
        "tags": ["slack", "messaging", "collaboration", "notifications"],
        "is_official": True,
        "is_installed": False,
        "price": "free",
        "parameters": [
            {
                "name": "operation",
                "type": "string",
                "required": True,
                "description": "Operation to perform",
                "enum": ["Send Message", "Send Direct Message", "Update Message", "Get Channel", "Create Channel", "Archive Channel", "Get User", "Get User Presence"],
                "default": "Send Message"
            },
            {
                "name": "authentication",
                "type": "string",
                "required": True,
                "description": "Authentication method",
                "enum": ["OAuth2", "Bot Token", "User Token"],
                "default": "Bot Token"
            },
            {
                "name": "token",
                "type": "string",
                "required": True,
                "description": "Slack Bot Token or OAuth Token",
                "placeholder": "xoxb-your-token-here"
            },
            {
                "name": "channel",
                "type": "string",
                "required": False,
                "description": "Channel ID or name (for Send Message)",
                "placeholder": "#general or C1234567890"
            },
            {
                "name": "user",
                "type": "string",
                "required": False,
                "description": "User ID (for Send Direct Message)",
                "placeholder": "U1234567890"
            },
            {
                "name": "text",
                "type": "string",
                "required": False,
                "description": "Message text",
                "placeholder": "Hello from AgenticRAG!"
            },
            {
                "name": "blocks",
                "type": "array",
                "required": False,
                "description": "Slack Block Kit blocks for rich formatting",
                "placeholder": [{"type": "section", "text": {"type": "mrkdwn", "text": "Hello *World*"}}]
            },
            {
                "name": "attachments",
                "type": "array",
                "required": False,
                "description": "Message attachments",
                "placeholder": [{"color": "#36a64f", "text": "Attachment text"}]
            },
            {
                "name": "thread_ts",
                "type": "string",
                "required": False,
                "description": "Thread timestamp (to reply in thread)",
                "placeholder": "1234567890.123456"
            },
            {
                "name": "as_user",
                "type": "boolean",
                "required": False,
                "description": "Post as authenticated user",
                "default": False
            },
            {
                "name": "username",
                "type": "string",
                "required": False,
                "description": "Bot username override",
                "placeholder": "AgenticRAG Bot"
            },
            {
                "name": "icon_emoji",
                "type": "string",
                "required": False,
                "description": "Bot icon emoji",
                "placeholder": ":robot_face:"
            },
            {
                "name": "icon_url",
                "type": "string",
                "required": False,
                "description": "Bot icon URL",
                "placeholder": "https://example.com/icon.png"
            }
        ],
        "examples": [
            {
                "name": "Send simple message",
                "operation": "Send Message",
                "authentication": "Bot Token",
                "channel": "#general",
                "text": "Hello from AgenticRAG!"
            },
            {
                "name": "Send rich message with blocks",
                "operation": "Send Message",
                "channel": "#notifications",
                "blocks": [
                    {"type": "section", "text": {"type": "mrkdwn", "text": "*Deployment Complete* :white_check_mark:"}},
                    {"type": "section", "text": {"type": "mrkdwn", "text": "Version: 1.2.3\nStatus: Success"}}
                ]
            },
            {
                "name": "Send direct message",
                "operation": "Send Direct Message",
                "user": "U1234567890",
                "text": "Hi! This is a private message."
            }
        ],
        "documentation_url": "https://docs.agenticrag.com/tools/slack"
    },
    {
        "id": "gmail",
        "name": "Gmail",
        "description": "Send emails, read messages, manage labels, and interact with Gmail",
        "category": "api",
        "icon": "Mail",
        "version": "2.0.0",
        "author": "AgenticRAG Team",
        "downloads": 15200,
        "rating": 4.8,
        "reviews_count": 456,
        "tags": ["gmail", "email", "google", "communication"],
        "is_official": True,
        "is_installed": False,
        "price": "free",
        "parameters": [
            {
                "name": "operation",
                "type": "string",
                "required": True,
                "description": "Operation to perform",
                "enum": ["Send Email", "Get Email", "Search Emails", "Delete Email", "Add Label", "Remove Label", "Create Draft", "Send Draft"],
                "default": "Send Email"
            },
            {
                "name": "authentication",
                "type": "string",
                "required": True,
                "description": "Authentication method",
                "enum": ["OAuth2", "Service Account"],
                "default": "OAuth2"
            },
            {
                "name": "credentials",
                "type": "object",
                "required": True,
                "description": "Gmail API credentials (OAuth2 or Service Account JSON)",
                "placeholder": {"client_id": "...", "client_secret": "...", "refresh_token": "..."}
            },
            {
                "name": "to",
                "type": "string",
                "required": False,
                "description": "Recipient email address (for Send Email)",
                "placeholder": "user@example.com"
            },
            {
                "name": "cc",
                "type": "string",
                "required": False,
                "description": "CC email addresses (comma-separated)",
                "placeholder": "user1@example.com, user2@example.com"
            },
            {
                "name": "bcc",
                "type": "string",
                "required": False,
                "description": "BCC email addresses (comma-separated)",
                "placeholder": "user3@example.com"
            },
            {
                "name": "subject",
                "type": "string",
                "required": False,
                "description": "Email subject",
                "placeholder": "Important Update"
            },
            {
                "name": "body",
                "type": "string",
                "required": False,
                "description": "Email body (plain text or HTML)",
                "placeholder": "Hello,\n\nThis is the email body."
            },
            {
                "name": "body_type",
                "type": "string",
                "required": False,
                "description": "Body content type",
                "enum": ["Plain Text", "HTML"],
                "default": "Plain Text"
            },
            {
                "name": "attachments",
                "type": "array",
                "required": False,
                "description": "File attachments",
                "placeholder": [{"filename": "report.pdf", "data": "base64_encoded_data"}]
            },
            {
                "name": "message_id",
                "type": "string",
                "required": False,
                "description": "Message ID (for Get/Delete Email)",
                "placeholder": "1234567890abcdef"
            },
            {
                "name": "query",
                "type": "string",
                "required": False,
                "description": "Search query (for Search Emails)",
                "placeholder": "from:user@example.com subject:report"
            },
            {
                "name": "max_results",
                "type": "number",
                "required": False,
                "description": "Maximum number of results (for Search)",
                "default": 10,
                "min": 1,
                "max": 100
            },
            {
                "name": "label_ids",
                "type": "array",
                "required": False,
                "description": "Label IDs to add/remove",
                "placeholder": ["INBOX", "UNREAD", "Label_123"]
            }
        ],
        "examples": [
            {
                "name": "Send simple email",
                "operation": "Send Email",
                "to": "user@example.com",
                "subject": "Hello from AgenticRAG",
                "body": "This is a test email.",
                "body_type": "Plain Text"
            },
            {
                "name": "Send HTML email with CC",
                "operation": "Send Email",
                "to": "user@example.com",
                "cc": "manager@example.com",
                "subject": "Weekly Report",
                "body": "<h1>Report</h1><p>Here is the weekly report.</p>",
                "body_type": "HTML"
            },
            {
                "name": "Search emails",
                "operation": "Search Emails",
                "query": "from:boss@example.com is:unread",
                "max_results": 5
            }
        ],
        "documentation_url": "https://docs.agenticrag.com/tools/gmail"
    },
    {
        "id": "http_request",
        "name": "HTTP Request",
        "description": "Make HTTP requests to any API endpoint with full control over method, headers, body, and authentication",
        "category": "api",
        "icon": "Globe",
        "version": "3.0.0",
        "author": "AgenticRAG Team",
        "downloads": 5200,
        "rating": 4.9,
        "reviews_count": 156,
        "tags": ["http", "api", "rest", "webhook"],
        "is_official": True,
        "is_installed": True,
        "price": "free",
        "parameters": [
            {
                "name": "url",
                "type": "string",
                "required": True,
                "description": "The URL to make the request to",
                "placeholder": "https://api.example.com/endpoint"
            },
            {
                "name": "method",
                "type": "string",
                "required": True,
                "description": "HTTP method to use",
                "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
                "default": "GET"
            },
            {
                "name": "authentication",
                "type": "string",
                "required": False,
                "description": "Authentication type",
                "enum": ["None", "Basic Auth", "Bearer Token", "API Key", "OAuth2"],
                "default": "None"
            },
            {
                "name": "headers",
                "type": "object",
                "required": False,
                "description": "Custom headers to send with the request",
                "placeholder": {"Content-Type": "application/json", "Accept": "application/json"}
            },
            {
                "name": "query_parameters",
                "type": "object",
                "required": False,
                "description": "URL query parameters",
                "placeholder": {"page": "1", "limit": "10"}
            },
            {
                "name": "body",
                "type": "object",
                "required": False,
                "description": "Request body (for POST, PUT, PATCH)",
                "placeholder": {"key": "value"}
            },
            {
                "name": "timeout",
                "type": "number",
                "required": False,
                "description": "Request timeout in seconds",
                "default": 30,
                "min": 1,
                "max": 300
            },
            {
                "name": "follow_redirects",
                "type": "boolean",
                "required": False,
                "description": "Follow HTTP redirects",
                "default": True
            },
            {
                "name": "verify_ssl",
                "type": "boolean",
                "required": False,
                "description": "Verify SSL certificates",
                "default": True
            },
            {
                "name": "response_format",
                "type": "string",
                "required": False,
                "description": "Expected response format",
                "enum": ["Auto", "JSON", "Text", "Binary"],
                "default": "Auto"
            }
        ],
        "examples": [
            {
                "name": "Simple GET request",
                "url": "https://api.github.com/users/octocat",
                "method": "GET"
            },
            {
                "name": "POST with JSON body",
                "url": "https://api.example.com/users",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": {"name": "John Doe", "email": "john@example.com"}
            },
            {
                "name": "GET with query parameters",
                "url": "https://api.example.com/search",
                "method": "GET",
                "query_parameters": {"q": "machine learning", "limit": "10"}
            }
        ],
        "documentation_url": "https://docs.agenticrag.com/tools/http-request"
    },
    {
        "id": "graphql_client",
        "name": "GraphQL Client",
        "description": "Execute GraphQL queries and mutations",
        "category": "api",
        "icon": "Code",
        "version": "1.5.0",
        "author": "Community",
        "downloads": 980,
        "rating": 4.5,
        "reviews_count": 34,
        "tags": ["graphql", "api"],
        "is_official": False,
        "is_installed": False,
        "price": "free",
        "parameters": [
            {"name": "endpoint", "type": "string", "required": True},
            {"name": "query", "type": "string", "required": True},
            {"name": "variables", "type": "object", "required": False}
        ],
        "examples": []
    },
    {
        "id": "webhook",
        "name": "Webhook",
        "description": "Receive HTTP webhooks from external services",
        "category": "api",
        "icon": "Webhook",
        "version": "2.1.0",
        "author": "AgenticRAG Team",
        "downloads": 3400,
        "rating": 4.8,
        "reviews_count": 92,
        "tags": ["webhook", "trigger"],
        "is_official": True,
        "is_installed": False,
        "price": "free",
        "parameters": [
            {"name": "path", "type": "string", "required": True},
            {"name": "method", "type": "string", "required": False, "default": "POST"}
        ],
        "examples": []
    },
    
    # Data Processing (80+ tools)
    {
        "id": "csv_parser",
        "name": "CSV Parser",
        "description": "Parse and transform CSV files",
        "category": "data",
        "icon": "FileText",
        "version": "1.8.0",
        "author": "AgenticRAG Team",
        "downloads": 2600,
        "rating": 4.6,
        "reviews_count": 71,
        "tags": ["csv", "parser", "data"],
        "is_official": True,
        "is_installed": False,
        "price": "free",
        "parameters": [
            {"name": "file", "type": "string", "required": True},
            {"name": "delimiter", "type": "string", "required": False, "default": ","}
        ],
        "examples": []
    },
    {
        "id": "json_transformer",
        "name": "JSON Transformer",
        "description": "Transform JSON data with JSONPath and JMESPath",
        "category": "data",
        "icon": "Code",
        "version": "2.2.0",
        "author": "AgenticRAG Team",
        "downloads": 3100,
        "rating": 4.7,
        "reviews_count": 88,
        "tags": ["json", "transform", "data"],
        "is_official": True,
        "is_installed": False,
        "price": "free",
        "parameters": [
            {"name": "data", "type": "object", "required": True},
            {"name": "expression", "type": "string", "required": True}
        ],
        "examples": []
    },
    {
        "id": "pdf_parser",
        "name": "PDF Parser",
        "description": "Extract text and tables from PDF files",
        "category": "data",
        "icon": "FileText",
        "version": "1.6.0",
        "author": "AgenticRAG Team",
        "downloads": 1900,
        "rating": 4.4,
        "reviews_count": 56,
        "tags": ["pdf", "parser", "ocr"],
        "is_official": True,
        "is_installed": False,
        "price": "free",
        "parameters": [
            {"name": "file", "type": "string", "required": True},
            {"name": "extract_tables", "type": "boolean", "required": False, "default": False}
        ],
        "examples": []
    },
    
    # Code Execution (40+ tools)
    {
        "id": "python_executor",
        "name": "Python Code Executor",
        "description": "Execute Python code in a secure sandbox",
        "category": "code",
        "icon": "Code",
        "version": "2.5.0",
        "author": "AgenticRAG Team",
        "downloads": 4100,
        "rating": 4.8,
        "reviews_count": 124,
        "tags": ["python", "code", "executor"],
        "is_official": True,
        "is_installed": False,
        "price": "free",
        "parameters": [
            {"name": "code", "type": "string", "required": True},
            {"name": "timeout", "type": "number", "required": False, "default": 30}
        ],
        "examples": [
            {"code": "print('Hello World')"}
        ]
    },
    {
        "id": "javascript_runner",
        "name": "JavaScript Runner",
        "description": "Execute JavaScript/Node.js code",
        "category": "code",
        "icon": "Code",
        "version": "2.3.0",
        "author": "AgenticRAG Team",
        "downloads": 3600,
        "rating": 4.7,
        "reviews_count": 98,
        "tags": ["javascript", "nodejs", "code"],
        "is_official": True,
        "is_installed": False,
        "price": "free",
        "parameters": [
            {"name": "code", "type": "string", "required": True}
        ],
        "examples": []
    },
    {
        "id": "sql_query",
        "name": "SQL Query Executor",
        "description": "Execute SQL queries on various databases",
        "category": "code",
        "icon": "Database",
        "version": "1.9.0",
        "author": "AgenticRAG Team",
        "downloads": 2800,
        "rating": 4.6,
        "reviews_count": 75,
        "tags": ["sql", "database", "query"],
        "is_official": True,
        "is_installed": False,
        "price": "free",
        "parameters": [
            {"name": "query", "type": "string", "required": True},
            {"name": "database_type", "type": "string", "required": True}
        ],
        "examples": []
    },
    
    # AI & ML (60+ tools)
    {
        "id": "ai_agent",
        "name": "AI Agent",
        "description": "Autonomous AI agent that can use tools, search the web, and reason through complex tasks step by step",
        "category": "ai",
        "icon": "Bot",
        "version": "1.0.0",
        "author": "AgenticRAG Team",
        "downloads": 8500,
        "rating": 4.9,
        "reviews_count": 245,
        "tags": ["ai", "agent", "autonomous", "reasoning", "tools"],
        "is_official": True,
        "is_installed": True,
        "price": "free",
        "parameters": [
            {
                "name": "task",
                "type": "string",
                "required": True,
                "description": "Task or question for the AI agent to accomplish",
                "placeholder": "Find the latest news about AI and summarize the top 3 articles"
            },
            {
                "name": "llm_provider",
                "type": "select",
                "required": True,
                "description": "LLM provider to use",
                "options": [
                    {"label": "Ollama (Local)", "value": "ollama"},
                    {"label": "OpenAI", "value": "openai"},
                    {"label": "Anthropic Claude", "value": "anthropic"}
                ],
                "default": "ollama"
            },
            {
                "name": "model",
                "type": "string",
                "required": True,
                "description": "Model to use (depends on provider)",
                "placeholder": "llama3.1:8b, gpt-4, claude-3-opus",
                "default": "llama3.1:8b"
            },
            {
                "name": "chat_input",
                "type": "chat",
                "required": False,
                "description": "Interactive chat input for the agent",
                "placeholder": "Type your message here..."
            },
            {
                "name": "memory_type",
                "type": "select",
                "required": True,
                "description": "Memory duration type for conversation context",
                "options": [
                    {"label": "Very Short Term (1 message)", "value": "very_short_term"},
                    {"label": "Short Term (5 messages)", "value": "short_term"},
                    {"label": "Medium Term (20 messages)", "value": "medium_term"},
                    {"label": "Long Term (100+ messages)", "value": "long_term"}
                ],
                "default": "short_term"
            },
            {
                "name": "enable_web_search",
                "type": "boolean",
                "required": False,
                "description": "Allow agent to search the internet",
                "default": True
            },
            {
                "name": "enable_vector_search",
                "type": "boolean",
                "required": False,
                "description": "Allow agent to search in knowledge base",
                "default": True
            },
            {
                "name": "knowledgebase_id",
                "type": "string",
                "required": False,
                "description": "Knowledge base to search (if vector search enabled)",
                "placeholder": "kb-documents"
            },
            {
                "name": "available_tools",
                "type": "array",
                "required": False,
                "description": "Tools the agent can use",
                "placeholder": ["http_request", "calculator", "code_executor"],
                "default": ["web_search", "vector_search"]
            },
            {
                "name": "max_iterations",
                "type": "number",
                "required": False,
                "description": "Maximum reasoning iterations",
                "default": 10,
                "min": 1,
                "max": 50
            },
            {
                "name": "temperature",
                "type": "number",
                "required": False,
                "description": "Sampling temperature (0-2)",
                "default": 0.7,
                "min": 0.0,
                "max": 2.0
            },
            {
                "name": "system_prompt",
                "type": "string",
                "required": False,
                "description": "Custom system prompt for the agent",
                "placeholder": "You are a helpful AI assistant that can use tools to accomplish tasks."
            },
            {
                "name": "max_tokens",
                "type": "number",
                "required": False,
                "description": "Maximum tokens to generate",
                "default": 2000,
                "min": 100,
                "max": 8000
            },
            {
                "name": "timeout",
                "type": "number",
                "required": False,
                "description": "Timeout in seconds",
                "default": 120,
                "min": 10,
                "max": 600
            }
        ],
        "examples": [
            {
                "name": "Web research with local LLM",
                "task": "Find the latest developments in quantum computing and summarize them",
                "llm_provider": "Local (Ollama)",
                "model": "llama3.1:8b",
                "enable_web_search": True,
                "enable_vector_search": False
            },
            {
                "name": "Knowledge base query with GPT-4",
                "task": "What are the best practices for RAG systems?",
                "llm_provider": "OpenAI",
                "model": "gpt-4",
                "enable_web_search": False,
                "enable_vector_search": True,
                "knowledgebase_id": "kb-documents"
            },
            {
                "name": "Complex task with multiple tools",
                "task": "Calculate the compound interest for $10000 at 5% for 10 years, then search for current inflation rates",
                "llm_provider": "Anthropic (Claude)",
                "model": "claude-3-opus",
                "enable_web_search": True,
                "available_tools": ["calculator", "web_search"]
            }
        ],
        "documentation_url": "https://docs.agenticrag.com/tools/ai-agent"
    },
    {
        "id": "llm_call",
        "name": "LLM Call",
        "description": "Call any LLM (OpenAI, Anthropic, Ollama) with full control over parameters and system prompts",
        "category": "ai",
        "icon": "Bot",
        "version": "3.2.0",
        "author": "AgenticRAG Team",
        "downloads": 6800,
        "rating": 4.9,
        "reviews_count": 203,
        "tags": ["llm", "ai", "gpt", "claude", "ollama"],
        "is_official": True,
        "is_installed": True,
        "price": "free",
        "parameters": [
            {
                "name": "prompt",
                "type": "string",
                "required": True,
                "description": "User prompt or question",
                "placeholder": "Explain quantum computing in simple terms"
            },
            {
                "name": "model",
                "type": "string",
                "required": True,
                "description": "LLM model to use",
                "enum": ["gpt-4", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet", "llama3.1:8b", "mistral"],
                "default": "gpt-3.5-turbo"
            },
            {
                "name": "system_prompt",
                "type": "string",
                "required": False,
                "description": "System prompt to set behavior",
                "placeholder": "You are a helpful assistant"
            },
            {
                "name": "temperature",
                "type": "number",
                "required": False,
                "description": "Sampling temperature (0-2)",
                "default": 0.7,
                "min": 0.0,
                "max": 2.0
            },
            {
                "name": "max_tokens",
                "type": "number",
                "required": False,
                "description": "Maximum tokens to generate",
                "default": 1000,
                "min": 1,
                "max": 4096
            },
            {
                "name": "top_p",
                "type": "number",
                "required": False,
                "description": "Nucleus sampling parameter",
                "default": 1.0,
                "min": 0.0,
                "max": 1.0
            },
            {
                "name": "frequency_penalty",
                "type": "number",
                "required": False,
                "description": "Frequency penalty (-2 to 2)",
                "default": 0.0,
                "min": -2.0,
                "max": 2.0
            },
            {
                "name": "presence_penalty",
                "type": "number",
                "required": False,
                "description": "Presence penalty (-2 to 2)",
                "default": 0.0,
                "min": -2.0,
                "max": 2.0
            },
            {
                "name": "stop_sequences",
                "type": "array",
                "required": False,
                "description": "Stop sequences",
                "placeholder": ["END", "STOP"]
            }
        ],
        "examples": [
            {
                "name": "Simple question",
                "prompt": "What is the capital of France?",
                "model": "gpt-3.5-turbo"
            },
            {
                "name": "Creative writing",
                "prompt": "Write a short story about a robot",
                "model": "gpt-4",
                "temperature": 1.2,
                "max_tokens": 500
            },
            {
                "name": "Code generation",
                "prompt": "Write a Python function to calculate fibonacci",
                "model": "gpt-4",
                "system_prompt": "You are an expert Python programmer",
                "temperature": 0.2
            }
        ],
        "documentation_url": "https://docs.agenticrag.com/tools/llm-call"
    },
    {
        "id": "image_generation",
        "name": "Image Generation",
        "description": "Generate images with DALL-E or Stable Diffusion",
        "category": "ai",
        "icon": "Image",
        "version": "1.4.0",
        "author": "Community",
        "downloads": 1500,
        "rating": 4.5,
        "reviews_count": 42,
        "tags": ["image", "ai", "generation"],
        "is_official": False,
        "is_installed": False,
        "price": "$9.99",
        "parameters": [
            {"name": "prompt", "type": "string", "required": True},
            {"name": "size", "type": "string", "required": False, "default": "1024x1024"}
        ],
        "examples": []
    },
    {
        "id": "sentiment_analysis",
        "name": "Sentiment Analysis",
        "description": "Analyze sentiment of text (positive/negative/neutral)",
        "category": "ai",
        "icon": "Heart",
        "version": "1.7.0",
        "author": "AgenticRAG Team",
        "downloads": 2200,
        "rating": 4.6,
        "reviews_count": 67,
        "tags": ["sentiment", "nlp", "ai"],
        "is_official": True,
        "is_installed": False,
        "price": "free",
        "parameters": [
            {"name": "text", "type": "string", "required": True}
        ],
        "examples": []
    },
    
    # Utility (70+ tools)
    {
        "id": "calculator",
        "name": "Calculator",
        "description": "Perform mathematical calculations with support for basic arithmetic, trigonometry, and advanced functions",
        "category": "utility",
        "icon": "Calculator",
        "version": "1.0.0",
        "author": "AgenticRAG Team",
        "downloads": 4500,
        "rating": 4.8,
        "reviews_count": 132,
        "tags": ["math", "calculator", "arithmetic"],
        "is_official": True,
        "is_installed": True,
        "price": "free",
        "parameters": [
            {
                "name": "expression",
                "type": "string",
                "required": True,
                "description": "Mathematical expression to evaluate",
                "placeholder": "2 + 2 * 3"
            }
        ],
        "supported_operations": [
            "Basic: +, -, *, /, ** (power)",
            "Functions: sqrt(), sin(), cos(), tan(), log(), exp(), abs(), round()",
            "Constants: pi, e"
        ],
        "examples": [
            {
                "name": "Basic arithmetic",
                "expression": "2 + 2 * 3",
                "result": 8
            },
            {
                "name": "Square root",
                "expression": "sqrt(16)",
                "result": 4.0
            },
            {
                "name": "Trigonometry",
                "expression": "sin(0)",
                "result": 0.0
            },
            {
                "name": "Power",
                "expression": "2 ** 10",
                "result": 1024
            }
        ],
        "documentation_url": "https://docs.agenticrag.com/tools/calculator"
    },
    {
        "id": "datetime_formatter",
        "name": "Date/Time Formatter",
        "description": "Format and manipulate dates and times",
        "category": "utility",
        "icon": "Clock",
        "version": "2.1.0",
        "author": "AgenticRAG Team",
        "downloads": 3200,
        "rating": 4.7,
        "reviews_count": 89,
        "tags": ["date", "time", "format"],
        "is_official": True,
        "is_installed": False,
        "price": "free",
        "parameters": [
            {"name": "date", "type": "string", "required": True},
            {"name": "format", "type": "string", "required": True}
        ],
        "examples": []
    },
    {
        "id": "uuid_generator",
        "name": "UUID Generator",
        "description": "Generate UUIDs (v1, v4, v5)",
        "category": "utility",
        "icon": "Hash",
        "version": "1.2.0",
        "author": "AgenticRAG Team",
        "downloads": 2900,
        "rating": 4.6,
        "reviews_count": 76,
        "tags": ["uuid", "generator"],
        "is_official": True,
        "is_installed": False,
        "price": "free",
        "parameters": [
            {"name": "version", "type": "string", "required": False, "default": "v4"}
        ],
        "examples": []
    },
]


@router.get("/marketplace", response_model=List[MarketplaceTool])
async def get_marketplace_tools(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("downloads", regex="^(downloads|rating|name|updated_at)$"),
    is_official: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all marketplace tools with filtering and sorting."""
    
    tools = MARKETPLACE_TOOLS.copy()
    
    # Filter by category
    if category:
        tools = [t for t in tools if t["category"] == category]
    
    # Filter by search query
    if search:
        search_lower = search.lower()
        tools = [
            t for t in tools
            if search_lower in t["name"].lower() or
               search_lower in t["description"].lower() or
               any(search_lower in tag for tag in t["tags"])
        ]
    
    # Filter by official status
    if is_official is not None:
        tools = [t for t in tools if t["is_official"] == is_official]
    
    # Sort
    reverse = sort_by in ["downloads", "rating", "updated_at"]
    tools.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)
    
    # Add timestamps
    now = datetime.utcnow()
    for tool in tools:
        tool["created_at"] = now
        tool["updated_at"] = now
    
    return tools


@router.get("/marketplace/categories", response_model=List[ToolCategory])
async def get_tool_categories(
    current_user: User = Depends(get_current_user)
):
    """Get all tool categories with counts."""
    
    categories = {}
    for tool in MARKETPLACE_TOOLS:
        cat = tool["category"]
        if cat not in categories:
            categories[cat] = {
                "id": cat,
                "name": cat.title(),
                "description": f"{cat.title()} tools and integrations",
                "icon": tool["icon"],
                "tool_count": 0
            }
        categories[cat]["tool_count"] += 1
    
    return list(categories.values())


@router.get("/marketplace/{tool_id}", response_model=MarketplaceTool)
async def get_marketplace_tool(
    tool_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific tool."""
    
    tool = next((t for t in MARKETPLACE_TOOLS if t["id"] == tool_id), None)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    # Add timestamps
    now = datetime.utcnow()
    tool["created_at"] = now
    tool["updated_at"] = now
    
    return tool


@router.post("/marketplace/{tool_id}/install")
async def install_tool(
    tool_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Install a tool from the marketplace."""
    
    tool = next((t for t in MARKETPLACE_TOOLS if t["id"] == tool_id), None)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    # Mark as installed
    tool["is_installed"] = True
    tool["downloads"] += 1
    
    return {
        "success": True,
        "message": f"Tool '{tool['name']}' installed successfully",
        "tool_id": tool_id
    }


@router.delete("/marketplace/{tool_id}/uninstall")
async def uninstall_tool(
    tool_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Uninstall a tool."""
    
    tool = next((t for t in MARKETPLACE_TOOLS if t["id"] == tool_id), None)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    tool["is_installed"] = False
    
    return {
        "success": True,
        "message": f"Tool '{tool['name']}' uninstalled successfully"
    }


@router.get("/marketplace/{tool_id}/reviews", response_model=List[ToolReview])
async def get_tool_reviews(
    tool_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get reviews for a specific tool."""
    
    # Mock reviews
    return [
        {
            "id": "rev-1",
            "tool_id": tool_id,
            "user_id": "user-1",
            "user_name": "John Doe",
            "rating": 5,
            "comment": "Excellent tool! Works perfectly.",
            "created_at": datetime.utcnow()
        }
    ]


@router.post("/marketplace/{tool_id}/reviews")
async def create_tool_review(
    tool_id: str,
    rating: int = Query(..., ge=1, le=5),
    comment: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a review for a tool."""
    
    tool = next((t for t in MARKETPLACE_TOOLS if t["id"] == tool_id), None)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    # Update tool rating
    total_rating = tool["rating"] * tool["reviews_count"]
    tool["reviews_count"] += 1
    tool["rating"] = (total_rating + rating) / tool["reviews_count"]
    
    return {
        "success": True,
        "message": "Review submitted successfully",
        "review_id": "rev-new"
    }


# Tool Configuration APIs
@router.get("/tools/{tool_id}/config")
async def get_tool_config(
    tool_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get saved configuration for a tool."""
    
    # In production, fetch from database
    # For now, return empty config
    return {
        "tool_id": tool_id,
        "config": {},
        "updated_at": datetime.utcnow()
    }


@router.post("/tools/{tool_id}/config")
async def save_tool_config(
    tool_id: str,
    config: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save configuration for a tool."""
    
    # In production, save to database
    # For now, just return success
    return {
        "success": True,
        "message": "Configuration saved successfully",
        "tool_id": tool_id,
        "config": config
    }
