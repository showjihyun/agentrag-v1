"""
External Data Connectors for Agent Builder.

Provides integration with external systems:
- CRM (Salesforce, HubSpot, Pipedrive)
- Databases (PostgreSQL, MySQL, MongoDB)
- APIs (REST, GraphQL)
- Data Sync Services
"""

from backend.services.connectors.base_connector import BaseConnector, ConnectorType
from backend.services.connectors.connection_manager import ConnectionManager
from backend.services.connectors.auth_manager import AuthManager

__all__ = [
    'BaseConnector',
    'ConnectorType',
    'ConnectionManager',
    'AuthManager',
]
