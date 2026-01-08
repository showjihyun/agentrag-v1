"""
Google A2A (Agent-to-Agent) Protocol Service.

이 모듈은 A2A 프로토콜을 통한 외부 에이전트 연동 기능을 제공합니다.
"""

from .client import A2AClient
from .server import A2AServer
from .registry import A2AAgentRegistry

__all__ = ["A2AClient", "A2AServer", "A2AAgentRegistry"]
