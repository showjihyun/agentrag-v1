"""
NLP Workflow Generation Service
LLM-based natural language to workflow conversion with structured output
"""

import logging
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class WorkflowComplexity(Enum):
    """Workflow complexity levels."""
    SIMPLE = "simple"      # 1-3 nodes
    MODERATE = "moderate"  # 4-7 nodes
    COMPLEX = "complex"    # 8+ nodes


@dataclass
class GeneratedNode:
    """Generated workflow node."""
    id: str
    type: str
    label: str
    config: Dict[str, Any]
    position: Dict[str, int]


@dataclass
class GeneratedEdge:
    """Generated workflow edge."""
    id: str
    source: str
    target: str
    label: Optional[str] = None
    source_handle: Optional[str] = None


@dataclass
class GenerationResult:
    """Result of workflow generation."""
    success: bool
    workflow_name: str
    workflow_description: str
    nodes: List[GeneratedNode]
    edges: List[GeneratedEdge]
    explanation: str
    confidence: float
    suggestions: List[str]
    complexity: WorkflowComplexity
    estimated_execution_time: str
    error: Optional[str] = None


# Available node types with their schemas
NODE_SCHEMAS = {
    # Triggers
    "manual_trigger": {
        "category": "trigger",
        "description": "수동으로 워크플로우 시작",
        "config_schema": {},
    },
    "schedule_trigger": {
        "category": "trigger", 
        "description": "스케줄에 따라 자동 실행",
        "config_schema": {"cron": "string", "timezone": "string"},
    },
    "webhook_trigger": {
        "category": "trigger",
        "description": "웹훅 요청으로 시작",
        "config_schema": {"path": "string", "method": "string"},
    },
    # AI
    "openai_chat": {
        "category": "ai",
        "description": "OpenAI GPT 모델로 텍스트 생성",
        "config_schema": {"model": "string", "prompt": "string", "temperature": "number"},
    },
    "anthropic_claude": {
        "category": "ai",
        "description": "Anthropic Claude 모델로 텍스트 생성",
        "config_schema": {"model": "string", "prompt": "string"},
    },
    "ai_agent": {
        "category": "ai",
        "description": "자율 AI 에이전트 실행",
        "config_schema": {"goal": "string", "tools": "array"},
    },
    # Search
    "tavily_search": {
        "category": "search",
        "description": "Tavily AI 검색",
        "config_schema": {"query": "string", "max_results": "number"},
    },
    "wikipedia_search": {
        "category": "search",
        "description": "위키피디아 검색",
        "config_schema": {"query": "string", "language": "string"},
    },
    "arxiv_search": {
        "category": "search",
        "description": "학술 논문 검색",
        "config_schema": {"query": "string", "max_results": "number"},
    },
    "youtube_search": {
        "category": "search",
        "description": "YouTube 동영상 검색",
        "config_schema": {"query": "string", "max_results": "number"},
    },
    # Data
    "http_request": {
        "category": "integration",
        "description": "HTTP API 요청",
        "config_schema": {"url": "string", "method": "string", "headers": "object", "body": "string"},
    },
    "postgresql_query": {
        "category": "data",
        "description": "PostgreSQL 데이터베이스 쿼리",
        "config_schema": {"query": "string", "connection": "string"},
    },
    "mongodb_query": {
        "category": "data",
        "description": "MongoDB 쿼리",
        "config_schema": {"collection": "string", "query": "object"},
    },
    "redis_operation": {
        "category": "data",
        "description": "Redis 캐시 작업",
        "config_schema": {"operation": "string", "key": "string"},
    },
    "vector_search": {
        "category": "data",
        "description": "벡터 유사도 검색",
        "config_schema": {"query": "string", "top_k": "number"},
    },
    # Communication
    "slack": {
        "category": "communication",
        "description": "Slack 메시지 전송",
        "config_schema": {"channel": "string", "message": "string"},
    },
    "sendgrid": {
        "category": "communication",
        "description": "이메일 전송",
        "config_schema": {"to": "string", "subject": "string", "body": "string"},
    },
    "discord": {
        "category": "communication",
        "description": "Discord 메시지 전송",
        "config_schema": {"channel_id": "string", "message": "string"},
    },
    # Transform
    "transform": {
        "category": "transform",
        "description": "데이터 변환",
        "config_schema": {"expression": "string"},
    },
    "filter": {
        "category": "transform",
        "description": "데이터 필터링",
        "config_schema": {"condition": "string"},
    },
    "json_transform": {
        "category": "transform",
        "description": "JSON 데이터 변환",
        "config_schema": {"mapping": "object"},
    },
    # Control Flow
    "condition": {
        "category": "control",
        "description": "조건 분기",
        "config_schema": {"condition": "string"},
    },
    "switch": {
        "category": "control",
        "description": "다중 분기",
        "config_schema": {"expression": "string", "cases": "array"},
    },
    "loop": {
        "category": "control",
        "description": "반복 실행",
        "config_schema": {"items": "string", "batch_size": "number"},
    },
    "parallel": {
        "category": "control",
        "description": "병렬 실행",
        "config_schema": {"branches": "number"},
    },
    "merge": {
        "category": "control",
        "description": "결과 병합",
        "config_schema": {"mode": "string"},
    },
    "delay": {
        "category": "control",
        "description": "지연 실행",
        "config_schema": {"duration": "number", "unit": "string"},
    },
    "try_catch": {
        "category": "control",
        "description": "에러 처리",
        "config_schema": {"retry_count": "number"},
    },
    "human_approval": {
        "category": "control",
        "description": "사람 승인 대기",
        "config_schema": {"message": "string", "timeout": "number"},
    },
    # Code
    "python_code": {
        "category": "code",
        "description": "Python 코드 실행",
        "config_schema": {"code": "string"},
    },
    "javascript_code": {
        "category": "code",
        "description": "JavaScript 코드 실행",
        "config_schema": {"code": "string"},
    },
    # Storage
    "s3_upload": {
        "category": "storage",
        "description": "S3 파일 업로드",
        "config_schema": {"bucket": "string", "key": "string"},
    },
    # Output
    "end": {
        "category": "output",
        "description": "워크플로우 종료",
        "config_schema": {},
    },
    "webhook_response": {
        "category": "output",
        "description": "웹훅 응답 반환",
        "config_schema": {"status_code": "number", "body": "string"},
    },
}


def get_system_prompt() -> str:
    """Get system prompt for LLM workflow generation."""
    node_list = "\n".join([
        f"- {node_type}: {schema['description']} (category: {schema['category']})"
        for node_type, schema in NODE_SCHEMAS.items()
    ])
    
    return f"""You are an expert workflow designer. Your task is to convert natural language descriptions into structured workflow definitions.

Available node types:
{node_list}

Rules:
1. Every workflow MUST start with a trigger node (manual_trigger, schedule_trigger, or webhook_trigger)
2. Every workflow MUST end with an end node or webhook_response
3. Nodes must be connected logically based on data flow
4. Use appropriate node types for each task
5. Include error handling (try_catch) for complex workflows
6. Use parallel execution when tasks are independent
7. Position nodes vertically with 120px spacing

Output format (JSON):
{{
  "workflow_name": "워크플로우 이름",
  "workflow_description": "설명",
  "complexity": "simple|moderate|complex",
  "nodes": [
    {{
      "id": "unique_id",
      "type": "node_type",
      "label": "노드 레이블",
      "config": {{}},
      "position": {{"x": 200, "y": 100}}
    }}
  ],
  "edges": [
    {{
      "id": "edge_id",
      "source": "source_node_id",
      "target": "target_node_id",
      "label": "optional_label"
    }}
  ],
  "explanation": "워크플로우 설명",
  "suggestions": ["개선 제안 1", "개선 제안 2"]
}}

Always respond with valid JSON only. No markdown, no explanations outside JSON."""


def get_user_prompt(description: str, language: str = "ko") -> str:
    """Get user prompt for workflow generation."""
    lang_instruction = "응답은 한국어로 작성하세요." if language == "ko" else "Respond in English."
    
    return f"""Create a workflow for the following request:

"{description}"

{lang_instruction}

Generate a complete, production-ready workflow with proper error handling and optimizations."""


class NLPWorkflowService:
    """Service for LLM-based workflow generation."""
    
    def __init__(self):
        self.node_schemas = NODE_SCHEMAS
    
    async def generate_workflow(
        self,
        description: str,
        language: str = "ko",
        user_id: Optional[str] = None,
    ) -> GenerationResult:
        """
        Generate a workflow from natural language description using LLM.
        
        Args:
            description: Natural language description of the workflow
            language: Output language (ko, en)
            user_id: Optional user ID for personalization
            
        Returns:
            GenerationResult with generated workflow
        """
        try:
            # Call LLM for workflow generation
            llm_response = await self._call_llm(description, language)
            
            # Parse and validate response
            workflow_data = self._parse_llm_response(llm_response)
            
            # Validate and fix workflow structure
            validated_data = self._validate_workflow(workflow_data)
            
            # Build result
            nodes = [
                GeneratedNode(
                    id=n["id"],
                    type=n["type"],
                    label=n["label"],
                    config=n.get("config", {}),
                    position=n.get("position", {"x": 200, "y": 100}),
                )
                for n in validated_data["nodes"]
            ]
            
            edges = [
                GeneratedEdge(
                    id=e["id"],
                    source=e["source"],
                    target=e["target"],
                    label=e.get("label"),
                    source_handle=e.get("source_handle"),
                )
                for e in validated_data["edges"]
            ]
            
            complexity = WorkflowComplexity(validated_data.get("complexity", "moderate"))
            
            return GenerationResult(
                success=True,
                workflow_name=validated_data.get("workflow_name", "Generated Workflow"),
                workflow_description=validated_data.get("workflow_description", description),
                nodes=nodes,
                edges=edges,
                explanation=validated_data.get("explanation", ""),
                confidence=self._calculate_confidence(validated_data),
                suggestions=validated_data.get("suggestions", []),
                complexity=complexity,
                estimated_execution_time=self._estimate_execution_time(nodes),
            )
            
        except Exception as e:
            logger.error(f"Workflow generation failed: {e}", exc_info=True)
            
            # Fallback to rule-based generation
            return await self._fallback_generation(description, language)
    
    async def _call_llm(self, description: str, language: str) -> str:
        """Call LLM for workflow generation."""
        try:
            from backend.services.llm_manager import LLMManager
            from backend.config import settings
            
            # Use longer timeout for workflow generation (complex task)
            llm_manager = LLMManager()
            
            # Use system-configured model, not hardcoded
            model = settings.LLM_MODEL
            
            # Build generation params with longer timeout for complex generation
            gen_params = {
                "messages": [
                    {"role": "system", "content": get_system_prompt()},
                    {"role": "user", "content": get_user_prompt(description, language)},
                ],
                "temperature": 0.3,  # Lower temperature for more consistent output
                "timeout": 60.0,  # Longer timeout for workflow generation
            }
            
            # Only add response_format for OpenAI models that support it
            if settings.LLM_PROVIDER == "openai" and "gpt" in model.lower():
                gen_params["response_format"] = {"type": "json_object"}
            
            response = await llm_manager.generate(**gen_params)
            
            # Handle both string and dict responses
            if isinstance(response, str):
                return response
            return response.get("content", "{}")
            
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response to workflow data."""
        try:
            # Clean response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            data = json.loads(response)
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise ValueError(f"Invalid JSON response: {e}")
    
    def _validate_workflow(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix workflow structure."""
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        
        # Ensure we have nodes
        if not nodes:
            raise ValueError("No nodes in workflow")
        
        # Check for trigger node
        trigger_types = {"manual_trigger", "schedule_trigger", "webhook_trigger"}
        has_trigger = any(n.get("type") in trigger_types for n in nodes)
        
        if not has_trigger:
            # Add manual trigger at the beginning
            trigger_node = {
                "id": f"trigger_{uuid.uuid4().hex[:8]}",
                "type": "manual_trigger",
                "label": "시작",
                "config": {},
                "position": {"x": 200, "y": 100},
            }
            nodes.insert(0, trigger_node)
            
            # Connect trigger to first non-trigger node
            if len(nodes) > 1:
                edges.insert(0, {
                    "id": f"e_{trigger_node['id']}_{nodes[1]['id']}",
                    "source": trigger_node["id"],
                    "target": nodes[1]["id"],
                })
        
        # Check for end node
        end_types = {"end", "webhook_response"}
        has_end = any(n.get("type") in end_types for n in nodes)
        
        if not has_end:
            # Add end node
            last_node = nodes[-1]
            end_node = {
                "id": f"end_{uuid.uuid4().hex[:8]}",
                "type": "end",
                "label": "완료",
                "config": {},
                "position": {"x": 200, "y": last_node.get("position", {}).get("y", 100) + 120},
            }
            nodes.append(end_node)
            
            # Connect last node to end
            edges.append({
                "id": f"e_{last_node['id']}_{end_node['id']}",
                "source": last_node["id"],
                "target": end_node["id"],
            })
        
        # Validate node types
        for node in nodes:
            if node.get("type") not in self.node_schemas:
                logger.warning(f"Unknown node type: {node.get('type')}, defaulting to transform")
                node["type"] = "transform"
        
        # Fix positions if needed
        y_pos = 100
        for node in nodes:
            if "position" not in node:
                node["position"] = {"x": 200, "y": y_pos}
            y_pos = node["position"]["y"] + 120
        
        # Ensure all edges have IDs
        for i, edge in enumerate(edges):
            if "id" not in edge:
                edge["id"] = f"e_{i}_{edge['source']}_{edge['target']}"
        
        data["nodes"] = nodes
        data["edges"] = edges
        
        return data
    
    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score for generated workflow."""
        score = 0.5  # Base score
        
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        
        # More nodes = more complex = potentially lower confidence
        if len(nodes) <= 5:
            score += 0.2
        elif len(nodes) <= 10:
            score += 0.1
        
        # Check edge connectivity
        node_ids = {n["id"] for n in nodes}
        connected_nodes = set()
        for edge in edges:
            if edge["source"] in node_ids and edge["target"] in node_ids:
                connected_nodes.add(edge["source"])
                connected_nodes.add(edge["target"])
        
        connectivity_ratio = len(connected_nodes) / len(node_ids) if node_ids else 0
        score += connectivity_ratio * 0.2
        
        # Check for proper trigger and end
        trigger_types = {"manual_trigger", "schedule_trigger", "webhook_trigger"}
        end_types = {"end", "webhook_response"}
        
        has_trigger = any(n.get("type") in trigger_types for n in nodes)
        has_end = any(n.get("type") in end_types for n in nodes)
        
        if has_trigger:
            score += 0.05
        if has_end:
            score += 0.05
        
        return min(0.95, max(0.3, score))
    
    def _estimate_execution_time(self, nodes: List[GeneratedNode]) -> str:
        """Estimate workflow execution time."""
        # Simple estimation based on node types
        time_estimates = {
            "ai": 5,  # AI nodes take longer
            "search": 3,
            "data": 2,
            "communication": 1,
            "transform": 0.5,
            "control": 0.1,
            "trigger": 0,
            "output": 0,
            "code": 2,
            "storage": 2,
            "integration": 2,
        }
        
        total_seconds = 0
        for node in nodes:
            node_schema = self.node_schemas.get(node.type, {})
            category = node_schema.get("category", "transform")
            total_seconds += time_estimates.get(category, 1)
        
        if total_seconds < 5:
            return "< 5초"
        elif total_seconds < 30:
            return f"약 {int(total_seconds)}초"
        elif total_seconds < 60:
            return "약 1분"
        else:
            return f"약 {int(total_seconds / 60)}분"
    
    async def _fallback_generation(
        self,
        description: str,
        language: str,
    ) -> GenerationResult:
        """Fallback to rule-based generation when LLM fails."""
        logger.info("Using fallback rule-based generation")
        
        # Simple keyword-based generation
        description_lower = description.lower()
        
        nodes = []
        edges = []
        y_pos = 100
        
        def add_node(node_type: str, label: str, config: Dict = None) -> str:
            nonlocal y_pos
            node_id = f"{node_type}_{uuid.uuid4().hex[:8]}"
            nodes.append(GeneratedNode(
                id=node_id,
                type=node_type,
                label=label,
                config=config or {},
                position={"x": 200, "y": y_pos},
            ))
            y_pos += 120
            return node_id
        
        # Determine trigger type
        if any(w in description_lower for w in ["매일", "매시간", "스케줄", "schedule", "daily", "hourly"]):
            trigger_id = add_node("schedule_trigger", "스케줄 트리거", {"cron": "0 9 * * *"})
        elif any(w in description_lower for w in ["웹훅", "webhook", "api"]):
            trigger_id = add_node("webhook_trigger", "웹훅 트리거")
        else:
            trigger_id = add_node("manual_trigger", "시작")
        
        last_id = trigger_id
        
        # Add nodes based on keywords
        if any(w in description_lower for w in ["검색", "search", "찾", "find"]):
            node_id = add_node("tavily_search", "웹 검색", {"query": "{{input.query}}"})
            edges.append(GeneratedEdge(id=f"e_{last_id}_{node_id}", source=last_id, target=node_id))
            last_id = node_id
        
        if any(w in description_lower for w in ["ai", "gpt", "생성", "요약", "분석", "generate", "summarize"]):
            node_id = add_node("openai_chat", "AI 처리", {"model": "gpt-4o-mini", "prompt": "{{input}}"})
            edges.append(GeneratedEdge(id=f"e_{last_id}_{node_id}", source=last_id, target=node_id))
            last_id = node_id
        
        if any(w in description_lower for w in ["슬랙", "slack", "알림", "notify"]):
            node_id = add_node("slack", "Slack 전송", {"channel": "#general"})
            edges.append(GeneratedEdge(id=f"e_{last_id}_{node_id}", source=last_id, target=node_id))
            last_id = node_id
        
        if any(w in description_lower for w in ["이메일", "email", "메일"]):
            node_id = add_node("sendgrid", "이메일 전송")
            edges.append(GeneratedEdge(id=f"e_{last_id}_{node_id}", source=last_id, target=node_id))
            last_id = node_id
        
        if any(w in description_lower for w in ["저장", "save", "database", "db"]):
            node_id = add_node("postgresql_query", "데이터 저장")
            edges.append(GeneratedEdge(id=f"e_{last_id}_{node_id}", source=last_id, target=node_id))
            last_id = node_id
        
        # Add end node
        end_id = add_node("end", "완료")
        edges.append(GeneratedEdge(id=f"e_{last_id}_{end_id}", source=last_id, target=end_id))
        
        return GenerationResult(
            success=True,
            workflow_name="생성된 워크플로우",
            workflow_description=description,
            nodes=nodes,
            edges=edges,
            explanation="키워드 기반으로 생성된 기본 워크플로우입니다. 필요에 따라 수정하세요.",
            confidence=0.5,
            suggestions=[
                "LLM 기반 생성을 위해 더 자세한 설명을 입력하세요",
                "노드 설정을 확인하고 필요한 파라미터를 입력하세요",
            ],
            complexity=WorkflowComplexity.SIMPLE,
            estimated_execution_time="< 5초",
        )
    
    async def refine_workflow(
        self,
        workflow_data: Dict[str, Any],
        refinement_request: str,
        language: str = "ko",
    ) -> GenerationResult:
        """
        Refine an existing workflow based on user feedback.
        
        Args:
            workflow_data: Current workflow definition
            refinement_request: User's refinement request
            language: Output language
            
        Returns:
            Refined workflow
        """
        try:
            from backend.services.llm_manager import LLMManager
            
            llm_manager = LLMManager()
            
            refinement_prompt = f"""Current workflow:
{json.dumps(workflow_data, ensure_ascii=False, indent=2)}

User's refinement request:
"{refinement_request}"

Modify the workflow according to the request. Keep the same JSON structure.
{"응답은 한국어로 작성하세요." if language == "ko" else "Respond in English."}"""
            
            response = await llm_manager.generate(
                messages=[
                    {"role": "system", "content": get_system_prompt()},
                    {"role": "user", "content": refinement_prompt},
                ],
                model="gpt-4o-mini",
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            
            refined_data = self._parse_llm_response(response.get("content", "{}"))
            validated_data = self._validate_workflow(refined_data)
            
            nodes = [
                GeneratedNode(
                    id=n["id"],
                    type=n["type"],
                    label=n["label"],
                    config=n.get("config", {}),
                    position=n.get("position", {"x": 200, "y": 100}),
                )
                for n in validated_data["nodes"]
            ]
            
            edges = [
                GeneratedEdge(
                    id=e["id"],
                    source=e["source"],
                    target=e["target"],
                    label=e.get("label"),
                )
                for e in validated_data["edges"]
            ]
            
            return GenerationResult(
                success=True,
                workflow_name=validated_data.get("workflow_name", "Refined Workflow"),
                workflow_description=validated_data.get("workflow_description", ""),
                nodes=nodes,
                edges=edges,
                explanation=f"'{refinement_request}' 요청에 따라 수정되었습니다.",
                confidence=self._calculate_confidence(validated_data),
                suggestions=validated_data.get("suggestions", []),
                complexity=WorkflowComplexity(validated_data.get("complexity", "moderate")),
                estimated_execution_time=self._estimate_execution_time(nodes),
            )
            
        except Exception as e:
            logger.error(f"Workflow refinement failed: {e}", exc_info=True)
            return GenerationResult(
                success=False,
                workflow_name="",
                workflow_description="",
                nodes=[],
                edges=[],
                explanation="",
                confidence=0,
                suggestions=[],
                complexity=WorkflowComplexity.SIMPLE,
                estimated_execution_time="",
                error=str(e),
            )
    
    def get_available_nodes(self) -> Dict[str, Any]:
        """Get available node types with their schemas."""
        return self.node_schemas
