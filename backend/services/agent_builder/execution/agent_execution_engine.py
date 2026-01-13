"""
Agent Execution Engine
실제 LLM 기반 Agent 실행 엔진
"""
import asyncio
import json
import time
from typing import Dict, List, Any, Optional, AsyncGenerator, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.callbacks.base import BaseCallbackHandler
from langchain.memory import ConversationBufferWindowMemory
from langgraph import StateGraph, END
from langgraph.graph import Graph

from backend.core.dependencies import get_redis_client
from backend.core.cache.plugin_cache import PluginCacheManager
from backend.services.rag.vector_search import VectorSearchService
from backend.services.rag.web_search import WebSearchService
from backend.services.rag.local_data import LocalDataService
from backend.core.error_handling.plugin_errors import (
    PluginException,
    PluginErrorCode,
    handle_plugin_errors
)

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Agent 타입"""
    OPENAI_FUNCTIONS = "openai_functions"
    ANTHROPIC_CLAUDE = "anthropic_claude"
    LANGGRAPH_WORKFLOW = "langgraph_workflow"
    CUSTOM_AGENT = "custom_agent"


class ExecutionMode(Enum):
    """실행 모드"""
    SYNC = "sync"
    ASYNC = "async"
    STREAMING = "streaming"


@dataclass
class AgentConfig:
    """Agent 설정"""
    agent_type: AgentType
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 300
    memory_window: int = 10
    tools: List[str] = field(default_factory=list)
    system_prompt: Optional[str] = None
    custom_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    """실행 컨텍스트"""
    user_id: str
    session_id: str
    workflow_id: Optional[str] = None
    execution_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """실행 결과"""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    token_usage: Dict[str, int] = field(default_factory=dict)
    intermediate_steps: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class StreamingCallbackHandler(BaseCallbackHandler):
    """스트리밍 콜백 핸들러"""
    
    def __init__(self, callback_func):
        self.callback_func = callback_func
        self.current_step = 0
    
    def on_agent_action(self, action, **kwargs):
        """Agent 액션 시작"""
        self.current_step += 1
        asyncio.create_task(self.callback_func({
            "type": "agent_action",
            "step": self.current_step,
            "action": action.tool,
            "input": action.tool_input,
            "timestamp": datetime.now().isoformat()
        }))
    
    def on_agent_finish(self, finish, **kwargs):
        """Agent 완료"""
        asyncio.create_task(self.callback_func({
            "type": "agent_finish",
            "result": finish.return_values,
            "timestamp": datetime.now().isoformat()
        }))
    
    def on_tool_start(self, serialized, input_str, **kwargs):
        """도구 실행 시작"""
        asyncio.create_task(self.callback_func({
            "type": "tool_start",
            "tool": serialized.get("name", "unknown"),
            "input": input_str,
            "timestamp": datetime.now().isoformat()
        }))
    
    def on_tool_end(self, output, **kwargs):
        """도구 실행 완료"""
        asyncio.create_task(self.callback_func({
            "type": "tool_end",
            "output": str(output)[:500],  # 출력 길이 제한
            "timestamp": datetime.now().isoformat()
        }))


class AgentExecutionEngine:
    """Agent 실행 엔진"""
    
    def __init__(self):
        self.cache_manager = PluginCacheManager()
        self.vector_search = VectorSearchService()
        self.web_search = WebSearchService()
        self.local_data = LocalDataService()
        
        # 사용 가능한 도구들
        self.available_tools = {
            "vector_search": self._create_vector_search_tool(),
            "web_search": self._create_web_search_tool(),
            "local_data": self._create_local_data_tool(),
            "calculator": self._create_calculator_tool(),
            "code_executor": self._create_code_executor_tool()
        }
        
        # Agent 인스턴스 캐시
        self.agent_cache: Dict[str, Any] = {}
    
    def _create_vector_search_tool(self) -> Tool:
        """벡터 검색 도구 생성"""
        async def vector_search_func(query: str) -> str:
            try:
                results = await self.vector_search.search(query, top_k=5)
                return json.dumps(results, ensure_ascii=False)
            except Exception as e:
                return f"Vector search error: {str(e)}"
        
        return Tool(
            name="vector_search",
            description="Search through documents using semantic similarity",
            func=vector_search_func
        )
    
    def _create_web_search_tool(self) -> Tool:
        """웹 검색 도구 생성"""
        async def web_search_func(query: str) -> str:
            try:
                results = await self.web_search.search(query, max_results=5)
                return json.dumps(results, ensure_ascii=False)
            except Exception as e:
                return f"Web search error: {str(e)}"
        
        return Tool(
            name="web_search",
            description="Search the web for current information",
            func=web_search_func
        )
    
    def _create_local_data_tool(self) -> Tool:
        """로컬 데이터 도구 생성"""
        async def local_data_func(query: str) -> str:
            try:
                results = await self.local_data.query(query)
                return json.dumps(results, ensure_ascii=False)
            except Exception as e:
                return f"Local data error: {str(e)}"
        
        return Tool(
            name="local_data",
            description="Query local data and files",
            func=local_data_func
        )
    
    def _create_calculator_tool(self) -> Tool:
        """계산기 도구 생성"""
        def calculator_func(expression: str) -> str:
            try:
                # 안전한 수식 계산
                allowed_chars = set('0123456789+-*/.() ')
                if not all(c in allowed_chars for c in expression):
                    return "Invalid characters in expression"
                
                result = eval(expression)
                return str(result)
            except Exception as e:
                return f"Calculation error: {str(e)}"
        
        return Tool(
            name="calculator",
            description="Perform mathematical calculations",
            func=calculator_func
        )
    
    def _create_code_executor_tool(self) -> Tool:
        """코드 실행 도구 생성"""
        def code_executor_func(code: str) -> str:
            try:
                # 보안상 제한된 Python 코드만 실행
                allowed_imports = ['math', 'datetime', 'json', 're']
                
                # 간단한 보안 검사
                dangerous_keywords = ['import os', 'import sys', 'exec', 'eval', '__']
                if any(keyword in code for keyword in dangerous_keywords):
                    return "Dangerous code detected"
                
                # 제한된 환경에서 실행
                local_vars = {}
                exec(code, {"__builtins__": {}}, local_vars)
                
                return str(local_vars.get('result', 'No result'))
            except Exception as e:
                return f"Code execution error: {str(e)}"
        
        return Tool(
            name="code_executor",
            description="Execute simple Python code",
            func=code_executor_func
        )
    
    async def _create_llm(self, config: AgentConfig):
        """LLM 인스턴스 생성"""
        if config.agent_type == AgentType.OPENAI_FUNCTIONS:
            return ChatOpenAI(
                model=config.model_name,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                request_timeout=config.timeout
            )
        elif config.agent_type == AgentType.ANTHROPIC_CLAUDE:
            return ChatAnthropic(
                model=config.model_name,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                timeout=config.timeout
            )
        else:
            raise ValueError(f"Unsupported agent type: {config.agent_type}")
    
    async def _create_agent(self, config: AgentConfig, context: ExecutionContext) -> Any:
        """Agent 인스턴스 생성"""
        cache_key = f"agent:{config.agent_type.value}:{config.model_name}:{context.user_id}"
        
        # 캐시에서 확인
        if cache_key in self.agent_cache:
            return self.agent_cache[cache_key]
        
        # LLM 생성
        llm = await self._create_llm(config)
        
        # 도구 선택
        tools = [self.available_tools[tool_name] for tool_name in config.tools 
                if tool_name in self.available_tools]
        
        # 프롬프트 템플릿
        system_prompt = config.system_prompt or """
You are a helpful AI assistant. Use the available tools to answer questions and complete tasks.
Always provide clear, accurate, and helpful responses.
"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # 메모리 설정
        memory = ConversationBufferWindowMemory(
            k=config.memory_window,
            memory_key="chat_history",
            return_messages=True
        )
        
        if config.agent_type == AgentType.OPENAI_FUNCTIONS:
            # OpenAI Functions Agent
            agent = create_openai_functions_agent(llm, tools, prompt)
            agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                memory=memory,
                verbose=True,
                max_iterations=10,
                max_execution_time=config.timeout
            )
        else:
            # 다른 Agent 타입들도 유사하게 구현
            agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                memory=memory,
                verbose=True
            )
        
        # 캐시에 저장
        self.agent_cache[cache_key] = agent_executor
        
        return agent_executor
    
    @handle_plugin_errors(attempt_recovery=True, max_retries=2)
    async def execute_agent(
        self,
        config: AgentConfig,
        input_data: Dict[str, Any],
        context: ExecutionContext,
        mode: ExecutionMode = ExecutionMode.ASYNC,
        streaming_callback: Optional[callable] = None
    ) -> Union[ExecutionResult, AsyncGenerator[Dict[str, Any], None]]:
        """Agent 실행"""
        
        start_time = time.time()
        execution_id = context.execution_id or f"exec_{int(time.time())}"
        
        try:
            # Agent 생성
            agent = await self._create_agent(config, context)
            
            # 입력 데이터 준비
            query = input_data.get("query", "")
            if not query:
                raise PluginException(
                    code=PluginErrorCode.VALIDATION_ERROR,
                    message="Query is required",
                    plugin_id="agent_execution_engine"
                )
            
            # 스트리밍 모드
            if mode == ExecutionMode.STREAMING:
                return self._execute_streaming(agent, query, context, streaming_callback)
            
            # 동기/비동기 실행
            if mode == ExecutionMode.SYNC:
                result = agent.invoke({"input": query})
            else:
                result = await agent.ainvoke({"input": query})
            
            execution_time = time.time() - start_time
            
            # 토큰 사용량 계산 (근사치)
            token_usage = {
                "prompt_tokens": len(query.split()) * 1.3,  # 근사치
                "completion_tokens": len(str(result.get("output", "")).split()) * 1.3,
                "total_tokens": 0
            }
            token_usage["total_tokens"] = token_usage["prompt_tokens"] + token_usage["completion_tokens"]
            
            return ExecutionResult(
                success=True,
                result=result,
                execution_time=execution_time,
                token_usage=token_usage,
                metadata={
                    "execution_id": execution_id,
                    "agent_type": config.agent_type.value,
                    "model_name": config.model_name
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Agent execution failed: {str(e)}")
            
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=execution_time,
                metadata={
                    "execution_id": execution_id,
                    "agent_type": config.agent_type.value,
                    "error_type": type(e).__name__
                }
            )
    
    async def _execute_streaming(
        self,
        agent: Any,
        query: str,
        context: ExecutionContext,
        callback: Optional[callable]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """스트리밍 실행"""
        
        # 스트리밍 콜백 설정
        if callback:
            streaming_handler = StreamingCallbackHandler(callback)
            agent.callbacks = [streaming_handler]
        
        try:
            # 스트리밍 실행 (실제로는 단계별 결과를 yield)
            yield {
                "type": "start",
                "timestamp": datetime.now().isoformat(),
                "query": query
            }
            
            # Agent 실행
            result = await agent.ainvoke({"input": query})
            
            yield {
                "type": "result",
                "timestamp": datetime.now().isoformat(),
                "result": result
            }
            
            yield {
                "type": "complete",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            yield {
                "type": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def create_langgraph_workflow(
        self,
        config: Dict[str, Any],
        context: ExecutionContext
    ) -> Graph:
        """LangGraph 워크플로우 생성"""
        
        # 상태 정의
        class WorkflowState:
            def __init__(self):
                self.messages = []
                self.current_step = 0
                self.results = {}
        
        # 워크플로우 그래프 생성
        workflow = StateGraph(WorkflowState)
        
        # 노드 추가 (설정에 따라 동적으로)
        for step in config.get("steps", []):
            step_name = step["name"]
            step_type = step["type"]
            
            if step_type == "llm":
                workflow.add_node(step_name, self._create_llm_node(step))
            elif step_type == "tool":
                workflow.add_node(step_name, self._create_tool_node(step))
            elif step_type == "condition":
                workflow.add_node(step_name, self._create_condition_node(step))
        
        # 엣지 추가
        for edge in config.get("edges", []):
            workflow.add_edge(edge["from"], edge["to"])
        
        # 시작점과 끝점 설정
        workflow.set_entry_point(config.get("entry_point", "start"))
        workflow.set_finish_point(config.get("finish_point", "end"))
        
        return workflow.compile()
    
    def _create_llm_node(self, config: Dict[str, Any]):
        """LLM 노드 생성"""
        async def llm_node(state: Any):
            # LLM 호출 로직
            pass
        return llm_node
    
    def _create_tool_node(self, config: Dict[str, Any]):
        """도구 노드 생성"""
        async def tool_node(state: Any):
            # 도구 실행 로직
            pass
        return tool_node
    
    def _create_condition_node(self, config: Dict[str, Any]):
        """조건 노드 생성"""
        async def condition_node(state: Any):
            # 조건 평가 로직
            pass
        return condition_node
    
    async def cleanup_cache(self):
        """캐시 정리"""
        # 오래된 Agent 인스턴스 정리
        current_time = time.time()
        keys_to_remove = []
        
        for key, agent in self.agent_cache.items():
            # 1시간 이상 사용되지 않은 Agent 제거
            if hasattr(agent, '_last_used'):
                if current_time - agent._last_used > 3600:
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.agent_cache[key]
        
        logger.info(f"Cleaned up {len(keys_to_remove)} cached agents")


# 전역 인스턴스
agent_execution_engine = AgentExecutionEngine()