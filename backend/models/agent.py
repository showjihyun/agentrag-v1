"""Agent state and step models."""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class AgentStep(BaseModel):
    """Represents a single step in the agent's reasoning process."""

    step_id: str = Field(..., description="Unique identifier for this step")
    type: Literal[
        "thought",
        "action",
        "observation",
        "planning",
        "reflection",
        "response",
        "memory",
        "error",
    ] = Field(..., description="Type of step")
    content: str = Field(..., description="The content of this step")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When this step occurred"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "step_id": "step_001",
                "type": "thought",
                "content": "I need to search the vector database for relevant documents.",
                "timestamp": "2024-01-01T12:00:00",
                "metadata": {"action": "vector_search"},
            }
        }
    )


class AgentState(BaseModel):
    """Represents the complete state of the agent during query processing."""

    query: str = Field(..., description="The user's query")
    session_id: Optional[str] = Field(None, description="Session ID for context")
    planning_steps: List[str] = Field(
        default_factory=list, description="Chain of Thought planning steps"
    )
    action_history: List[Dict[str, Any]] = Field(
        default_factory=list, description="ReAct action log"
    )
    retrieved_docs: List[Dict[str, Any]] = Field(
        default_factory=list, description="Retrieved documents"
    )
    reasoning_steps: List[AgentStep] = Field(
        default_factory=list, description="All reasoning steps"
    )
    final_response: Optional[str] = Field(
        None, description="The final generated response"
    )
    memory_context: Dict[str, Any] = Field(
        default_factory=dict, description="Context from memory systems"
    )
    current_action: Optional[Dict[str, Any]] = Field(
        None, description="Current action being executed"
    )
    reflection_decision: Optional[str] = Field(
        None, description="Decision from reflection step"
    )
    error: Optional[str] = Field(None, description="Error message if processing failed")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "What are the benefits of machine learning?",
                "session_id": "session_123",
                "planning_steps": [
                    "Step 1: Search vector database",
                    "Step 2: Synthesize response",
                ],
                "action_history": [],
                "retrieved_docs": [],
                "reasoning_steps": [],
                "final_response": None,
                "memory_context": {},
                "current_action": None,
                "reflection_decision": None,
                "error": None,
            }
        }
    )
