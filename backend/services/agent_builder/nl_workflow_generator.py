"""
Natural Language Workflow Generator
자연어로 워크플로우를 생성하는 AI 시스템
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from backend.core.structured_logging import get_logger
from backend.config import settings

logger = get_logger(__name__)

class WorkflowNode:
    """워크플로우 노드 정의"""
    
    def __init__(self, node_id: str, node_type: str, name: str, config: Dict[str, Any]):
        self.id = node_id
        self.type = node_type
        self.name = name
        self.config = config
        self.position = {"x": 0, "y": 0}
        self.connections = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "config": self.config,
            "position": self.position,
            "connections": self.connections
        }

class WorkflowConnection:
    """워크플로우 연결 정의"""
    
    def __init__(self, source_id: str, target_id: str, source_port: str = "output", target_port: str = "input"):
        self.source_id = source_id
        self.target_id = target_id
        self.source_port = source_port
        self.target_port = target_port
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "sourcePort": self.source_port,
            "targetPort": self.target_port
        }

class NaturalLanguageWorkflowGenerator:
    """자연어 워크플로우 생성기"""
    
    def __init__(self):
        self.openai_client = None
        if OPENAI_AVAILABLE and settings.OPENAI_API_KEY:
            self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # 노드 타입 매핑
        self.node_templates = {
            # 트리거 노드
            "webhook": {
                "type": "webhook_trigger",
                "name": "웹훅 트리거",
                "config": {"method": "POST", "path": "/webhook"}
            },
            "schedule": {
                "type": "schedule_trigger", 
                "name": "스케줄 트리거",
                "config": {"cron": "0 9 * * *", "timezone": "Asia/Seoul"}
            },
            "manual": {
                "type": "manual_trigger",
                "name": "수동 트리거", 
                "config": {"button_text": "시작"}
            },
            
            # AI 처리 노드
            "llm": {
                "type": "openai_chat",
                "name": "AI 분석",
                "config": {"model": "gpt-4o-mini", "temperature": 0.7}
            },
            "sentiment": {
                "type": "openai_chat",
                "name": "감정 분석",
                "config": {
                    "model": "gpt-4o-mini",
                    "prompt": "다음 텍스트의 감정을 분석해주세요. positive, negative, neutral 중 하나로 답변해주세요: {{input}}"
                }
            },
            "summarize": {
                "type": "openai_chat", 
                "name": "요약",
                "config": {
                    "model": "gpt-4o-mini",
                    "prompt": "다음 내용을 3줄로 요약해주세요: {{input}}"
                }
            },
            "translate": {
                "type": "openai_chat",
                "name": "번역",
                "config": {
                    "model": "gpt-4o-mini", 
                    "prompt": "다음 텍스트를 영어로 번역해주세요: {{input}}"
                }
            },
            
            # 조건 및 제어 노드
            "condition": {
                "type": "condition",
                "name": "조건 분기",
                "config": {"condition": "input === 'positive'"}
            },
            "filter": {
                "type": "filter",
                "name": "필터",
                "config": {"condition": "value > 0"}
            },
            "delay": {
                "type": "delay",
                "name": "대기",
                "config": {"duration": 5, "unit": "seconds"}
            },
            
            # 통신 노드
            "slack": {
                "type": "slack",
                "name": "슬랙 메시지",
                "config": {"channel": "#general", "message": "알림: {{input}}"}
            },
            "email": {
                "type": "gmail",
                "name": "이메일 발송",
                "config": {"to": "", "subject": "알림", "body": "{{input}}"}
            },
            "sms": {
                "type": "sms",
                "name": "SMS 발송", 
                "config": {"to": "", "message": "{{input}}"}
            },
            
            # 데이터 처리 노드
            "database": {
                "type": "postgres",
                "name": "데이터베이스 조회",
                "config": {"query": "SELECT * FROM table WHERE condition"}
            },
            "http": {
                "type": "http_request",
                "name": "HTTP 요청",
                "config": {"method": "GET", "url": "https://api.example.com"}
            },
            "transform": {
                "type": "transform",
                "name": "데이터 변환",
                "config": {"script": "return { result: input.toUpperCase() }"}
            }
        }
        
        # 자연어 패턴 매핑
        self.language_patterns = {
            # 트리거 패턴
            r"웹훅|webhook|HTTP 요청을? 받": "webhook",
            r"스케줄|정기적|매일|매주|매월|시간마다": "schedule", 
            r"수동|버튼|클릭|시작": "manual",
            
            # AI 처리 패턴
            r"감정 ?분석|sentiment": "sentiment",
            r"요약|정리|summary": "summarize", 
            r"번역|translate": "translate",
            r"AI|분석|처리|LLM": "llm",
            
            # 조건 패턴
            r"만약|if|조건|분기": "condition",
            r"필터|거르|선별": "filter",
            r"대기|기다|delay|wait": "delay",
            
            # 통신 패턴
            r"슬랙|slack": "slack",
            r"이메일|메일|email": "email", 
            r"SMS|문자": "sms",
            
            # 데이터 패턴
            r"데이터베이스|DB|조회|저장": "database",
            r"API|HTTP|요청": "http",
            r"변환|transform|가공": "transform"
        }
    
    async def generate_workflow_from_text(
        self,
        description: str,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        자연어 설명으로부터 워크플로우 생성
        
        Args:
            description: 자연어 워크플로우 설명
            user_preferences: 사용자 선호 설정
            
        Returns:
            생성된 워크플로우 정의
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting workflow generation from text: {description[:100]}...")
            
            # 1. 자연어 분석 및 의도 파악
            analysis_result = await self._analyze_natural_language(description)
            
            # 2. 노드 생성
            nodes = await self._generate_nodes(analysis_result, user_preferences)
            
            # 3. 연결 생성
            connections = await self._generate_connections(nodes, analysis_result)
            
            # 4. 레이아웃 최적화
            positioned_nodes = self._optimize_layout(nodes)
            
            # 5. 워크플로우 메타데이터 생성
            metadata = self._generate_metadata(description, analysis_result)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            workflow = {
                "success": True,
                "workflow": {
                    "id": f"nl_workflow_{int(datetime.now().timestamp())}",
                    "name": metadata["name"],
                    "description": description,
                    "nodes": [node.to_dict() for node in positioned_nodes],
                    "connections": [conn.to_dict() for conn in connections],
                    "metadata": metadata
                },
                "analysis": analysis_result,
                "generation_time_seconds": processing_time,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Workflow generation completed in {processing_time:.2f}s")
            return workflow
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Workflow generation failed: {str(e)}", exc_info=True)
            
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "generation_time_seconds": processing_time,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analyze_natural_language(self, description: str) -> Dict[str, Any]:
        """자연어 분석 및 의도 파악"""
        
        # 기본 패턴 매칭
        detected_nodes = []
        for pattern, node_type in self.language_patterns.items():
            if re.search(pattern, description, re.IGNORECASE):
                detected_nodes.append(node_type)
        
        # 중복 제거
        detected_nodes = list(set(detected_nodes))
        
        # OpenAI를 사용한 고급 분석 (사용 가능한 경우)
        advanced_analysis = None
        if self.openai_client:
            try:
                advanced_analysis = await self._openai_analysis(description)
            except Exception as e:
                logger.warning(f"OpenAI analysis failed: {e}")
        
        return {
            "original_text": description,
            "detected_nodes": detected_nodes,
            "advanced_analysis": advanced_analysis,
            "complexity": self._assess_complexity(description),
            "estimated_execution_time": self._estimate_execution_time(detected_nodes)
        }
    
    async def _openai_analysis(self, description: str) -> Dict[str, Any]:
        """OpenAI를 사용한 고급 자연어 분석"""
        
        system_prompt = """
        당신은 워크플로우 자동화 전문가입니다. 사용자의 자연어 설명을 분석하여 워크플로우 구조를 파악해주세요.
        
        다음 형식으로 JSON 응답해주세요:
        {
            "workflow_type": "automation|data_processing|communication|analysis",
            "trigger": "webhook|schedule|manual|email",
            "main_steps": ["step1", "step2", "step3"],
            "conditions": ["condition1", "condition2"],
            "outputs": ["slack", "email", "database"],
            "complexity": "simple|medium|complex",
            "estimated_nodes": 5
        }
        """
        
        response = await self.openai_client.chat.completions.acreate(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"워크플로우 설명: {description}"}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {"error": "Failed to parse OpenAI response"}
    
    async def _generate_nodes(
        self, 
        analysis: Dict[str, Any], 
        preferences: Optional[Dict[str, Any]] = None
    ) -> List[WorkflowNode]:
        """분석 결과를 바탕으로 노드 생성"""
        
        nodes = []
        node_counter = 1
        
        detected_nodes = analysis.get("detected_nodes", [])
        advanced = analysis.get("advanced_analysis", {})
        
        # 트리거 노드 추가 (항상 첫 번째)
        trigger_type = "manual"  # 기본값
        if "webhook" in detected_nodes:
            trigger_type = "webhook"
        elif "schedule" in detected_nodes:
            trigger_type = "schedule"
        
        trigger_template = self.node_templates[trigger_type].copy()
        trigger_node = WorkflowNode(
            node_id=f"node_{node_counter}",
            node_type=trigger_template["type"],
            name=trigger_template["name"],
            config=trigger_template["config"]
        )
        nodes.append(trigger_node)
        node_counter += 1
        
        # 메인 처리 노드들 추가
        for node_type in detected_nodes:
            if node_type in ["webhook", "schedule", "manual"]:
                continue  # 트리거는 이미 추가됨
            
            if node_type in self.node_templates:
                template = self.node_templates[node_type].copy()
                node = WorkflowNode(
                    node_id=f"node_{node_counter}",
                    node_type=template["type"],
                    name=template["name"],
                    config=template["config"]
                )
                nodes.append(node)
                node_counter += 1
        
        # OpenAI 분석 결과 반영
        if advanced and "main_steps" in advanced:
            for step in advanced["main_steps"]:
                # 단계별 노드 추가 로직
                pass
        
        return nodes
    
    async def _generate_connections(
        self, 
        nodes: List[WorkflowNode], 
        analysis: Dict[str, Any]
    ) -> List[WorkflowConnection]:
        """노드 간 연결 생성"""
        
        connections = []
        
        # 기본적으로 순차 연결
        for i in range(len(nodes) - 1):
            connection = WorkflowConnection(
                source_id=nodes[i].id,
                target_id=nodes[i + 1].id
            )
            connections.append(connection)
        
        # 조건부 분기 처리
        condition_nodes = [node for node in nodes if node.type == "condition"]
        for condition_node in condition_nodes:
            # 조건에 따른 분기 연결 로직
            pass
        
        return connections
    
    def _optimize_layout(self, nodes: List[WorkflowNode]) -> List[WorkflowNode]:
        """노드 레이아웃 최적화"""
        
        # 간단한 세로 배치
        y_offset = 0
        for node in nodes:
            node.position = {"x": 200, "y": y_offset}
            y_offset += 150
        
        return nodes
    
    def _generate_metadata(self, description: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """워크플로우 메타데이터 생성"""
        
        # 설명에서 제목 추출 (첫 10단어)
        words = description.split()[:10]
        name = " ".join(words)
        if len(name) > 50:
            name = name[:47] + "..."
        
        return {
            "name": name,
            "category": "자동 생성",
            "tags": ["자연어", "자동생성"],
            "complexity": analysis.get("complexity", "medium"),
            "estimated_execution_time": analysis.get("estimated_execution_time", "5초"),
            "created_by": "nl_generator",
            "version": "1.0"
        }
    
    def _assess_complexity(self, description: str) -> str:
        """워크플로우 복잡도 평가"""
        
        word_count = len(description.split())
        condition_words = len(re.findall(r"만약|if|조건|분기", description, re.IGNORECASE))
        
        if word_count < 20 and condition_words == 0:
            return "simple"
        elif word_count < 50 and condition_words <= 2:
            return "medium"
        else:
            return "complex"
    
    def _estimate_execution_time(self, detected_nodes: List[str]) -> str:
        """예상 실행 시간 계산"""
        
        # 노드별 예상 시간 (초)
        node_times = {
            "llm": 3.0,
            "sentiment": 2.0,
            "summarize": 2.5,
            "translate": 2.0,
            "slack": 1.0,
            "email": 2.0,
            "database": 1.5,
            "http": 2.0,
            "condition": 0.1,
            "transform": 0.5
        }
        
        total_time = sum(node_times.get(node, 1.0) for node in detected_nodes)
        
        if total_time < 3:
            return "3초 이내"
        elif total_time < 10:
            return f"{int(total_time)}초 내외"
        else:
            return f"{int(total_time)}초 이상"

# 싱글톤 인스턴스
_nl_generator = None

def get_nl_workflow_generator() -> NaturalLanguageWorkflowGenerator:
    """자연어 워크플로우 생성기 싱글톤 인스턴스 반환"""
    global _nl_generator
    if _nl_generator is None:
        _nl_generator = NaturalLanguageWorkflowGenerator()
    return _nl_generator