"""
A2A Protocol Block.

워크플로우에서 외부 A2A 에이전트를 호출하는 블록.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, AsyncGenerator

from models.a2a import (
    Message,
    Task,
    TaskState,
    Part,
    Role,
    StreamResponse,
    SendMessageConfiguration,
)
from services.a2a.client import A2AClient, create_text_message, A2AClientError
from services.a2a.registry import get_a2a_registry

logger = logging.getLogger(__name__)


# Block definition for registry
A2A_BLOCK_DEFINITION = {
    "type": "a2a_agent",
    "name": "A2A Agent",
    "description": "외부 A2A 에이전트를 호출합니다",
    "category": "tools",
    "icon": "globe",
    "bg_color": "#6366F1",
    "sub_blocks": [
        {
            "id": "agent_config_id",
            "type": "dropdown",
            "title": "A2A 에이전트",
            "required": True,
            "placeholder": "연결된 에이전트 선택",
            "dynamic_options": "a2a_agents",
        },
        {
            "id": "input_type",
            "type": "dropdown",
            "title": "입력 타입",
            "required": True,
            "options": ["text", "json"],
            "default_value": "text",
        },
        {
            "id": "message",
            "type": "long-input",
            "title": "메시지",
            "placeholder": "에이전트에 보낼 메시지 (변수 사용 가능: {{input}})",
            "condition": {"field": "input_type", "value": "text"},
        },
        {
            "id": "json_data",
            "type": "code",
            "title": "JSON 데이터",
            "language": "json",
            "placeholder": '{"key": "value"}',
            "condition": {"field": "input_type", "value": "json"},
        },
        {
            "id": "streaming",
            "type": "checkbox",
            "title": "스트리밍 응답",
            "default_value": False,
        },
        {
            "id": "blocking",
            "type": "checkbox",
            "title": "완료까지 대기",
            "default_value": True,
        },
        {
            "id": "timeout",
            "type": "number-input",
            "title": "타임아웃 (초)",
            "default_value": 60,
        },
    ],
    "inputs": {
        "input": {"type": "string", "description": "입력 데이터"},
        "context": {"type": "object", "description": "컨텍스트 데이터"},
    },
    "outputs": {
        "response": {"type": "string", "description": "에이전트 응답"},
        "task_id": {"type": "string", "description": "태스크 ID"},
        "status": {"type": "string", "description": "태스크 상태"},
        "artifacts": {"type": "array", "description": "생성된 아티팩트"},
    },
}


async def execute_a2a_block(
    config: Dict[str, Any],
    inputs: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute A2A agent block.
    
    Args:
        config: Block configuration (sub_blocks values)
        inputs: Input data from previous blocks
        context: Execution context
        
    Returns:
        Block output data
    """
    agent_config_id = config.get("agent_config_id")
    input_type = config.get("input_type", "text")
    message_template = config.get("message", "")
    json_data = config.get("json_data", "{}")
    streaming = config.get("streaming", False)
    blocking = config.get("blocking", True)
    timeout = config.get("timeout", 60)
    
    if not agent_config_id:
        raise ValueError("A2A 에이전트를 선택해주세요")
        
    # Get user_id from context
    user_id = context.get("user_id", "default-user")
    
    # Get registry and client
    registry = get_a2a_registry()
    
    try:
        client = await registry.get_client(user_id, agent_config_id)
    except ValueError as e:
        raise ValueError(f"A2A 에이전트 연결 실패: {e}")
        
    # Prepare message
    if input_type == "text":
        # Resolve variables in message template
        message_text = message_template
        for key, value in inputs.items():
            message_text = message_text.replace(f"{{{{{key}}}}}", str(value))
            
        message = create_text_message(message_text)
    else:
        # Parse JSON data
        import json
        try:
            data = json.loads(json_data)
            # Merge with inputs
            for key, value in inputs.items():
                if f"{{{{{key}}}}}" in json_data:
                    data = json.loads(
                        json_data.replace(f'"{{{{{key}}}}}"', json.dumps(value))
                    )
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 파싱 오류: {e}")
            
        from services.a2a.client import create_data_message
        message = create_data_message(data)
        
    # Send message
    try:
        async with client:
            if streaming:
                # Streaming mode - collect all responses
                responses = []
                artifacts = []
                task_id = None
                status = None
                
                async for response in client.send_message_streaming(
                    message,
                    configuration=SendMessageConfiguration(blocking=blocking),
                ):
                    if response.task:
                        task_id = response.task.id
                        status = response.task.status.state.value
                        
                    if response.status_update:
                        status = response.status_update.status.state.value
                        
                    if response.artifact_update:
                        artifact = response.artifact_update.artifact
                        # Extract text from artifact
                        for part in artifact.parts:
                            if part.text:
                                responses.append(part.text)
                        artifacts.append({
                            "id": artifact.artifact_id,
                            "name": artifact.name,
                            "parts": [p.model_dump() for p in artifact.parts],
                        })
                        
                return {
                    "response": "\n".join(responses),
                    "task_id": task_id,
                    "status": status,
                    "artifacts": artifacts,
                }
                
            else:
                # Non-streaming mode
                result = await client.send_message(
                    message,
                    configuration=SendMessageConfiguration(blocking=blocking),
                )
                
                if result.task:
                    task = result.task
                    
                    # Extract response from artifacts
                    response_text = ""
                    artifacts = []
                    
                    if task.artifacts:
                        for artifact in task.artifacts:
                            for part in artifact.parts:
                                if part.text:
                                    response_text += part.text
                            artifacts.append({
                                "id": artifact.artifact_id,
                                "name": artifact.name,
                            })
                            
                    return {
                        "response": response_text,
                        "task_id": task.id,
                        "status": task.status.state.value,
                        "artifacts": artifacts,
                    }
                    
                elif result.message:
                    # Direct message response
                    response_text = ""
                    for part in result.message.parts:
                        if part.text:
                            response_text += part.text
                            
                    return {
                        "response": response_text,
                        "task_id": None,
                        "status": "completed",
                        "artifacts": [],
                    }
                    
    except A2AClientError as e:
        raise RuntimeError(f"A2A 에이전트 호출 실패: {e}")
    except asyncio.TimeoutError:
        raise RuntimeError(f"A2A 에이전트 응답 타임아웃 ({timeout}초)")


async def stream_a2a_block(
    config: Dict[str, Any],
    inputs: Dict[str, Any],
    context: Dict[str, Any],
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Execute A2A agent block with streaming output.
    
    Yields intermediate results for real-time updates.
    """
    agent_config_id = config.get("agent_config_id")
    message_template = config.get("message", "")
    
    if not agent_config_id:
        raise ValueError("A2A 에이전트를 선택해주세요")
        
    user_id = context.get("user_id", "default-user")
    registry = get_a2a_registry()
    
    try:
        client = await registry.get_client(user_id, agent_config_id)
    except ValueError as e:
        raise ValueError(f"A2A 에이전트 연결 실패: {e}")
        
    # Prepare message
    message_text = message_template
    for key, value in inputs.items():
        message_text = message_text.replace(f"{{{{{key}}}}}", str(value))
        
    message = create_text_message(message_text)
    
    try:
        async with client:
            async for response in client.send_message_streaming(message):
                if response.task:
                    yield {
                        "type": "task",
                        "task_id": response.task.id,
                        "status": response.task.status.state.value,
                    }
                    
                if response.status_update:
                    yield {
                        "type": "status",
                        "status": response.status_update.status.state.value,
                        "final": response.status_update.final,
                    }
                    
                if response.artifact_update:
                    artifact = response.artifact_update.artifact
                    text = ""
                    for part in artifact.parts:
                        if part.text:
                            text += part.text
                            
                    yield {
                        "type": "artifact",
                        "artifact_id": artifact.artifact_id,
                        "text": text,
                        "last_chunk": response.artifact_update.last_chunk,
                    }
                    
    except A2AClientError as e:
        yield {
            "type": "error",
            "error": str(e),
        }
