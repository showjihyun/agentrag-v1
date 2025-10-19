"""응답 청크 및 단계 타입 정의"""

from enum import Enum


class ChunkType(str, Enum):
    """응답 청크 타입"""
    STEP = "step"
    RESPONSE = "response"
    FINAL = "final"
    ERROR = "error"
    WARNING = "warning"
    DONE = "done"


class StepType(str, Enum):
    """처리 단계 타입"""
    PLANNING = "planning"
    ACTION = "action"
    THOUGHT = "thought"
    WARNING = "warning"
    OBSERVATION = "observation"


class SourceType(str, Enum):
    """소스 타입"""
    RAG = "rag"
    WEB = "web"
    HYBRID = "hybrid"
