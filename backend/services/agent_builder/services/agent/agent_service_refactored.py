"""
Agent Service Refactored - Backward Compatibility Module

This module re-exports AgentService as AgentServiceRefactored
for backward compatibility with existing code.
"""

from backend.services.agent_builder.agent_service import AgentService

# Backward compatibility alias
AgentServiceRefactored = AgentService

__all__ = ["AgentServiceRefactored"]
