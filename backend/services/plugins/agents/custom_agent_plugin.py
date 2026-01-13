"""
Custom Agent Plugin

사용자가 생성한 Custom Agent를 Plugin 형태로 래핑하는 시스템
"""
from typing import Dict, List, Any, Optional
import json
from datetime import datetime

from backend.services.plugins.agents.base_agent_plugin import (
    BaseAgentPlugin, 
    AgentCapability, 
    AgentExecutionContext
)
from backend.models.plugin import PluginManifest
from backend.models.agent_builder import AgentResponse
from backend.agents.base import BaseAgent
from backend.db.models.agent_builder import Agent as AgentModel
from backend.services.agent_builder.agent_service import AgentService
from backend.services.llm_manager import LLMManager
from backend.core.error_handling.plugin_errors import plugin_error_handler, PluginException, PluginErrorCode


class CustomAgentInstance(BaseAgent):
    """Custom Agent의 실제 실행 인스턴스"""
    
    def __init__(self, agent_data: AgentResponse, llm_manager: LLMManager):
        self.agent_data = agent_data
        self.llm_manager = llm_manager
        self.agent_id = agent_data.id
        self.name = agent_data.name
        self.description = agent_data.description
        self.prompt_template = agent_data.configuration.get("prompt_template", "")
        self.llm_provider = agent_data.llm_provider
        self.llm_model = agent_data.llm_model
        self.tools = agent_data.tools
        self.knowledgebases = agent_data.knowledgebases
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Custom Agent 실행"""
        try:
            # 입력 데이터 처리
            user_input = input_data.get("input", input_data.get("query", ""))
            if not user_input:
                return {
                    "success": False,
                    "error": "No input provided",
                    "agent_id": self.agent_id
                }
            
            # 프롬프트 템플릿 처리
            formatted_prompt = self._format_prompt(user_input, input_data, context)
            
            # LLM 호출
            llm_response = await self._call_llm(formatted_prompt, context)
            
            # 도구 실행 (필요시)
            tool_results = await self._execute_tools(input_data, context)
            
            # 지식베이스 검색 (필요시)
            kb_results = await self._search_knowledgebases(user_input, context)
            
            # 최종 응답 구성
            final_response = await self._generate_final_response(
                llm_response, tool_results, kb_results, context
            )
            
            return {
                "success": True,
                "response": final_response,
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "llm_provider": self.llm_provider,
                "llm_model": self.llm_model,
                "tool_results": tool_results,
                "kb_results": kb_results,
                "execution_metadata": {
                    "prompt_length": len(formatted_prompt),
                    "tools_used": len(tool_results),
                    "kb_searched": len(kb_results) > 0
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent_id": self.agent_id,
                "agent_name": self.name
            }
    
    def _format_prompt(self, user_input: str, input_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """프롬프트 템플릿 포맷팅"""
        prompt = self.prompt_template or "You are a helpful AI assistant. User input: {input}"
        
        # 변수 치환
        variables = {
            "input": user_input,
            "user_input": user_input,
            "agent_name": self.name,
            "agent_description": self.description,
            **input_data,
            **(context or {})
        }
        
        try:
            return prompt.format(**variables)
        except KeyError as e:
            # 누락된 변수가 있으면 기본 프롬프트 사용
            return f"You are {self.name}. {self.description or ''}\n\nUser: {user_input}"
    
    async def _call_llm(self, prompt: str, context: Dict[str, Any]) -> str:
        """LLM 호출"""
        try:
            # LLM Manager를 통한 호출
            response = await self.llm_manager.generate_response(
                prompt=prompt,
                provider=self.llm_provider,
                model=self.llm_model,
                context=context
            )
            return response.get("content", response.get("response", ""))
        except Exception as e:
            return f"LLM 호출 실패: {str(e)}"
    
    async def _execute_tools(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """연결된 도구들 실행"""
        tool_results = []
        
        for tool in self.tools:
            try:
                # 도구 실행 로직 (실제 구현에서는 Tool Service 사용)
                tool_result = {
                    "tool_id": tool.get("id", "unknown"),
                    "tool_name": tool.get("name", "Unknown Tool"),
                    "success": True,
                    "result": f"Tool {tool.get('name', 'Unknown')} executed successfully"
                }
                tool_results.append(tool_result)
            except Exception as e:
                tool_results.append({
                    "tool_id": tool.get("id", "unknown"),
                    "tool_name": tool.get("name", "Unknown Tool"),
                    "success": False,
                    "error": str(e)
                })
        
        return tool_results
    
    async def _search_knowledgebases(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """연결된 지식베이스 검색"""
        kb_results = []
        
        for kb in self.knowledgebases:
            try:
                # 지식베이스 검색 로직 (실제 구현에서는 KB Service 사용)
                kb_result = {
                    "kb_id": kb.get("id", "unknown"),
                    "kb_name": kb.get("name", "Unknown KB"),
                    "results": [
                        {
                            "content": f"Sample result from {kb.get('name', 'KB')}",
                            "score": 0.85,
                            "metadata": {}
                        }
                    ]
                }
                kb_results.append(kb_result)
            except Exception as e:
                kb_results.append({
                    "kb_id": kb.get("id", "unknown"),
                    "kb_name": kb.get("name", "Unknown KB"),
                    "error": str(e)
                })
        
        return kb_results
    
    async def _generate_final_response(
        self, 
        llm_response: str, 
        tool_results: List[Dict[str, Any]], 
        kb_results: List[Dict[str, Any]], 
        context: Dict[str, Any]
    ) -> str:
        """최종 응답 생성"""
        # 기본적으로는 LLM 응답을 반환
        # 필요시 도구 결과나 KB 결과를 통합
        
        if tool_results or kb_results:
            # 추가 정보가 있으면 통합된 응답 생성
            additional_info = []
            
            if tool_results:
                successful_tools = [t for t in tool_results if t.get("success")]
                if successful_tools:
                    additional_info.append(f"도구 실행 결과: {len(successful_tools)}개 도구 성공")
            
            if kb_results:
                total_kb_results = sum(len(kb.get("results", [])) for kb in kb_results if "results" in kb)
                if total_kb_results > 0:
                    additional_info.append(f"지식베이스 검색: {total_kb_results}개 결과 발견")
            
            if additional_info:
                return f"{llm_response}\n\n[추가 정보: {', '.join(additional_info)}]"
        
        return llm_response
    
    def get_health_status(self) -> Dict[str, Any]:
        """Agent 상태 확인"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "status": "healthy",
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "tools_count": len(self.tools),
            "knowledgebases_count": len(self.knowledgebases),
            "last_check": datetime.now().isoformat()
        }


class CustomAgentPlugin(BaseAgentPlugin):
    """Custom Agent Plugin 구현"""
    
    def __init__(self, agent_data: AgentResponse, config: Dict[str, Any] = None):
        super().__init__(config)
        self.agent_data = agent_data
        self.llm_manager = LLMManager()  # 실제로는 DI로 주입
    
    def get_manifest(self) -> PluginManifest:
        """플러그인 매니페스트 반환"""
        return PluginManifest(
            name=f"custom-agent-{self.agent_data.id}",
            version="1.0.0",
            description=f"Custom Agent: {self.agent_data.description or self.agent_data.name}",
            author=f"User {self.agent_data.user_id}",
            category="orchestration",
            dependencies=self._get_dependencies(),
            permissions=self._get_required_permissions(),
            configuration_schema=self._get_configuration_schema()
        )
    
    def get_agent_type(self) -> str:
        """Agent 타입 반환"""
        return f"custom_{self.agent_data.id}"
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Agent 능력 반환"""
        capabilities = [
            AgentCapability(
                name="custom_agent_execution",
                description=f"Execute custom agent: {self.agent_data.name}",
                input_schema={
                    "type": "object",
                    "properties": {
                        "input": {
                            "type": "string",
                            "description": "User input for the agent"
                        },
                        "context": {
                            "type": "object",
                            "description": "Additional context data"
                        }
                    },
                    "required": ["input"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "response": {"type": "string"},
                        "agent_id": {"type": "string"},
                        "agent_name": {"type": "string"},
                        "tool_results": {"type": "array"},
                        "kb_results": {"type": "array"}
                    }
                },
                required_permissions=["custom_agent_execution", "llm_access"]
            )
        ]
        
        # 도구별 능력 추가
        for tool in self.agent_data.tools:
            capabilities.append(
                AgentCapability(
                    name=f"tool_{tool.get('id', 'unknown')}",
                    description=f"Use tool: {tool.get('name', 'Unknown Tool')}",
                    input_schema=tool.get("input_schema", {}),
                    output_schema=tool.get("output_schema", {}),
                    required_permissions=[f"tool_{tool.get('id', 'unknown')}"]
                )
            )
        
        # 지식베이스별 능력 추가
        for kb in self.agent_data.knowledgebases:
            capabilities.append(
                AgentCapability(
                    name=f"kb_search_{kb.get('id', 'unknown')}",
                    description=f"Search knowledgebase: {kb.get('name', 'Unknown KB')}",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"}
                        },
                        "required": ["query"]
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "results": {"type": "array"}
                        }
                    },
                    required_permissions=[f"kb_access_{kb.get('id', 'unknown')}"]
                )
            )
        
        return capabilities
    
    def execute_agent(
        self, 
        input_data: Dict[str, Any], 
        context: AgentExecutionContext
    ) -> Dict[str, Any]:
        """Agent 실행"""
        try:
            agent_instance = self.get_agent_instance()
            
            # 실행 컨텍스트 설정
            execution_context = {
                "user_id": context.user_id,
                "session_id": context.session_id,
                "workflow_id": context.workflow_id,
                "agent_id": self.agent_data.id,
                **context.execution_metadata
            }
            
            # 비동기 실행을 동기로 래핑 (실제로는 async/await 사용)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                agent_instance.execute(input_data, execution_context)
            )
            
            return {
                "success": True,
                "result": result,
                "agent_type": self.get_agent_type(),
                "agent_name": self.agent_data.name,
                "execution_context": execution_context
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent_type": self.get_agent_type(),
                "agent_name": self.agent_data.name,
                "input_data": input_data
            }
    
    def _create_agent_instance(self) -> BaseAgent:
        """Custom Agent 인스턴스 생성"""
        return CustomAgentInstance(self.agent_data, self.llm_manager)
    
    def _get_dependencies(self) -> List[str]:
        """의존성 목록 반환"""
        dependencies = [f"llm-{self.agent_data.llm_provider}@>=1.0.0"]
        
        # 도구 의존성 추가
        for tool in self.agent_data.tools:
            tool_id = tool.get("id", "")
            if tool_id:
                dependencies.append(f"tool-{tool_id}@>=1.0.0")
        
        # 지식베이스 의존성 추가
        if self.agent_data.knowledgebases:
            dependencies.append("knowledgebase-service@>=1.0.0")
        
        return dependencies
    
    def _get_required_permissions(self) -> List[str]:
        """필수 권한 목록 반환"""
        permissions = [
            "custom_agent_execution",
            "llm_access",
            f"llm_{self.agent_data.llm_provider}_access"
        ]
        
        # 도구별 권한 추가
        for tool in self.agent_data.tools:
            tool_id = tool.get("id", "")
            if tool_id:
                permissions.append(f"tool_{tool_id}")
        
        # 지식베이스별 권한 추가
        for kb in self.agent_data.knowledgebases:
            kb_id = kb.get("id", "")
            if kb_id:
                permissions.append(f"kb_access_{kb_id}")
        
        return permissions
    
    def _get_configuration_schema(self) -> Dict[str, Any]:
        """설정 스키마 반환"""
        return {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "default": self.agent_data.id,
                    "description": "Custom Agent ID"
                },
                "llm_provider": {
                    "type": "string",
                    "default": self.agent_data.llm_provider,
                    "description": "LLM Provider"
                },
                "llm_model": {
                    "type": "string",
                    "default": self.agent_data.llm_model,
                    "description": "LLM Model"
                },
                "timeout_seconds": {
                    "type": "integer",
                    "default": 60,
                    "minimum": 10,
                    "maximum": 300,
                    "description": "Execution timeout in seconds"
                },
                "enable_tools": {
                    "type": "boolean",
                    "default": True,
                    "description": "Enable tool execution"
                },
                "enable_knowledgebase": {
                    "type": "boolean",
                    "default": True,
                    "description": "Enable knowledgebase search"
                }
            },
            "required": ["agent_id", "llm_provider", "llm_model"]
        }
    
    def _get_required_config_fields(self) -> List[str]:
        """필수 설정 필드"""
        return ["agent_id", "llm_provider", "llm_model"]
    
    def _validate_agent_specific_config(self, config: Dict[str, Any]) -> List[str]:
        """Custom Agent 특화 설정 검증"""
        errors = []
        
        # Agent ID 검증
        if "agent_id" in config:
            agent_id = config["agent_id"]
            if agent_id != self.agent_data.id:
                errors.append(f"Agent ID mismatch: expected {self.agent_data.id}, got {agent_id}")
        
        # LLM 설정 검증
        if "llm_provider" in config:
            provider = config["llm_provider"]
            valid_providers = ["ollama", "openai", "claude", "gemini"]
            if provider not in valid_providers:
                errors.append(f"Invalid LLM provider: {provider}")
        
        # 타임아웃 검증
        if "timeout_seconds" in config:
            timeout = config["timeout_seconds"]
            if not isinstance(timeout, int) or timeout < 10 or timeout > 300:
                errors.append("timeout_seconds must be an integer between 10 and 300")
        
        return errors
    
    def get_health_status(self) -> Dict[str, Any]:
        """Custom Agent 상태 확인"""
        base_status = super().get_health_status()
        
        if self._initialized and self._agent_instance:
            try:
                agent_health = self._agent_instance.get_health_status()
                base_status.update({
                    "custom_agent_health": agent_health,
                    "agent_id": self.agent_data.id,
                    "agent_name": self.agent_data.name,
                    "llm_provider": self.agent_data.llm_provider,
                    "llm_model": self.agent_data.llm_model,
                    "tools_available": len(self.agent_data.tools),
                    "knowledgebases_available": len(self.agent_data.knowledgebases)
                })
            except Exception as e:
                base_status["error"] = str(e)
                base_status["status"] = "unhealthy"
        
        return base_status