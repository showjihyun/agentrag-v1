# API Layer Structure

## Overview

The API layer is organized by domain for better maintainability and discoverability.

## Directory Structure

```
api/
├── __init__.py           # Package exports
├── README.md             # This file
│
├── auth/                 # Authentication domain
│   └── __init__.py       # Groups auth.py, auth_sessions.py, permissions.py
│
├── documents/            # Document management domain
│   └── __init__.py       # Groups documents.py, document_preview.py, etc.
│
├── conversations/        # Conversation domain
│   └── __init__.py       # Groups conversations.py, chat_history.py, etc.
│
├── query/                # Query processing domain
│   └── __init__.py       # Groups query.py, advanced_rag.py, web_search.py
│
├── monitoring/           # Monitoring domain
│   └── __init__.py       # Groups health.py, metrics.py, monitoring.py, etc.
│
├── admin/                # Administration domain
│   └── __init__.py       # Groups admin.py, config.py, llm_settings.py, etc.
│
├── agent_builder/        # Agent Builder feature (separate module)
│   ├── __init__.py
│   ├── agents.py
│   ├── workflows.py
│   └── ...
│
├── v1/                   # API version 1 (legacy)
│   └── __init__.py
│
├── v2/                   # API version 2
│   └── __init__.py
│
└── [root-level files]    # Backward compatibility (to be migrated)
```

## Domain Groupings

### Authentication (`auth/`)
- `auth.py` - Login, register, token management
- `auth_sessions.py` - Session management
- `permissions.py` - Permission checks

### Documents (`documents/`)
- `documents.py` - Document CRUD operations
- `document_preview.py` - Preview generation
- `knowledge_base.py` - Knowledge base management
- `paddleocr_advanced.py` - Advanced OCR

### Conversations (`conversations/`)
- `conversations.py` - Conversation CRUD
- `chat_history.py` - Chat history
- `bookmarks.py` - Message bookmarks
- `share.py` - Sharing functionality
- `export.py`, `exports.py` - Export features

### Query (`query/`)
- `query.py` - Main query processing
- `advanced_rag.py` - Advanced RAG features
- `web_search.py` - Web search integration
- `confidence.py` - Confidence scoring

### Monitoring (`monitoring/`)
- `health.py` - Health checks
- `metrics.py` - Application metrics
- `monitoring.py` - System monitoring
- `monitoring_stats.py` - Statistics
- `cache_metrics.py` - Cache metrics
- `database_metrics.py` - Database metrics
- `pool_metrics.py` - Connection pool metrics
- `circuit_breaker_status.py` - Circuit breaker
- `react_stats.py` - ReAct agent stats

### Admin (`admin/`)
- `admin.py` - Admin operations
- `config.py` - System configuration
- `llm_settings.py` - LLM settings
- `models.py` - Model management
- `cache_management.py` - Cache admin
- `enterprise.py` - Enterprise features
- `experiments.py` - A/B testing

## Usage

### Importing routers

```python
# Import from domain module
from backend.api.monitoring import health, metrics

# Import specific router
from backend.api.health import router as health_router

# Import from package
from backend.api import health_router, auth_router
```

### Adding new endpoints

1. Identify the appropriate domain
2. Add to existing file or create new file in domain folder
3. Update domain's `__init__.py` to export the router
4. Register router in `main.py` or `app/routers/__init__.py`

## Migration Notes

Root-level files are maintained for backward compatibility.
New features should be added to appropriate domain folders.
Gradually migrate root-level files to domain folders as needed.
