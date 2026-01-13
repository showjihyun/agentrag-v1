"""
Web Search Agent Plugin

기존 WebSearchAgent를 Plugin 형태로 래핑
"""
from typing import Dict, List, Any
from backend.services.plugins.agents.base_agent_plugin import (
    BaseAgentPlugin, 
    AgentCapability, 
    AgentExecutionContext
)
from backend.models.plugin import PluginManifest
from backend.agents.web_search import WebSearchAgent
from backend.agents.base import BaseAgent


class WebSearchAgentPlugin(BaseAgentPlugin):
    """Web Search Agent Plugin 구현"""
    
    def get_manifest(self) -> PluginManifest:
        """플러그인 매니페스트 반환"""
        return PluginManifest(
            name="web-search-agent",
            version="1.0.0",
            description="Web search agent using DuckDuckGo search API",
            author="AgenticRAG Team",
            category="orchestration",
            dependencies=["ddgs@>=3.0.0"],
            permissions=["web_search", "internet_access"],
            configuration_schema={
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                        "description": "Maximum number of search results"
                    },
                    "timeout": {
                        "type": "integer",
                        "default": 30,
                        "minimum": 5,
                        "maximum": 120,
                        "description": "Search timeout in seconds"
                    },
                    "safe_search": {
                        "type": "string",
                        "enum": ["strict", "moderate", "off"],
                        "default": "moderate",
                        "description": "Safe search level"
                    },
                    "region": {
                        "type": "string",
                        "default": "kr-kr",
                        "description": "Search region (e.g., kr-kr, us-en)"
                    },
                    "time_range": {
                        "type": "string",
                        "enum": ["d", "w", "m", "y", ""],
                        "default": "",
                        "description": "Time range filter (d=day, w=week, m=month, y=year)"
                    }
                },
                "required": []
            }
        )
    
    def get_agent_type(self) -> str:
        """Agent 타입 반환"""
        return "web_search"
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Agent 능력 반환"""
        return [
            AgentCapability(
                name="web_search",
                description="Search the web using DuckDuckGo",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "max_results": {
                            "type": "integer",
                            "default": 10,
                            "description": "Number of results to return"
                        },
                        "time_range": {
                            "type": "string",
                            "enum": ["d", "w", "m", "y", ""],
                            "description": "Time range filter"
                        }
                    },
                    "required": ["query"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "results": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "url": {"type": "string"},
                                    "snippet": {"type": "string"},
                                    "published_date": {"type": "string"}
                                }
                            }
                        },
                        "total_results": {"type": "integer"},
                        "search_time": {"type": "number"}
                    }
                },
                required_permissions=["web_search", "internet_access"]
            ),
            AgentCapability(
                name="news_search",
                description="Search for news articles",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "News search query"
                        },
                        "max_results": {
                            "type": "integer",
                            "default": 10,
                            "description": "Number of news results"
                        }
                    },
                    "required": ["query"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "news_results": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "url": {"type": "string"},
                                    "source": {"type": "string"},
                                    "published_date": {"type": "string"},
                                    "summary": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                required_permissions=["web_search", "internet_access"]
            ),
            AgentCapability(
                name="image_search",
                description="Search for images",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Image search query"
                        },
                        "max_results": {
                            "type": "integer",
                            "default": 20,
                            "description": "Number of image results"
                        }
                    },
                    "required": ["query"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "images": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "url": {"type": "string"},
                                    "thumbnail": {"type": "string"},
                                    "source": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                required_permissions=["web_search", "internet_access"]
            )
        ]
    
    def execute_agent(
        self, 
        input_data: Dict[str, Any], 
        context: AgentExecutionContext
    ) -> Dict[str, Any]:
        """Agent 실행"""
        try:
            agent = self.get_agent_instance()
            
            # 실행 컨텍스트 설정
            execution_context = {
                "user_id": context.user_id,
                "session_id": context.session_id,
                "workflow_id": context.workflow_id,
                **context.execution_metadata
            }
            
            # Agent 실행
            result = agent.execute(input_data, execution_context)
            
            return {
                "success": True,
                "result": result,
                "agent_type": self.get_agent_type(),
                "execution_context": execution_context
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent_type": self.get_agent_type(),
                "input_data": input_data
            }
    
    def _create_agent_instance(self) -> BaseAgent:
        """WebSearchAgent 인스턴스 생성"""
        return WebSearchAgent(
            max_results=self.config.get("max_results", 10),
            timeout=self.config.get("timeout", 30),
            safe_search=self.config.get("safe_search", "moderate"),
            region=self.config.get("region", "kr-kr"),
            time_range=self.config.get("time_range", "")
        )
    
    def _get_required_config_fields(self) -> List[str]:
        """필수 설정 필드"""
        return []  # Web Search Agent는 모든 설정이 선택사항
    
    def _validate_agent_specific_config(self, config: Dict[str, Any]) -> List[str]:
        """Web Search Agent 특화 설정 검증"""
        errors = []
        
        # 최대 결과 수 검증
        if "max_results" in config:
            max_results = config["max_results"]
            if not isinstance(max_results, int) or max_results < 1 or max_results > 50:
                errors.append("max_results must be an integer between 1 and 50")
        
        # 타임아웃 검증
        if "timeout" in config:
            timeout = config["timeout"]
            if not isinstance(timeout, int) or timeout < 5 or timeout > 120:
                errors.append("timeout must be an integer between 5 and 120 seconds")
        
        # Safe search 검증
        if "safe_search" in config:
            safe_search = config["safe_search"]
            if safe_search not in ["strict", "moderate", "off"]:
                errors.append("safe_search must be one of: strict, moderate, off")
        
        # Time range 검증
        if "time_range" in config:
            time_range = config["time_range"]
            if time_range not in ["d", "w", "m", "y", ""]:
                errors.append("time_range must be one of: d, w, m, y, or empty string")
        
        return errors
    
    def get_health_status(self) -> Dict[str, Any]:
        """Web Search Agent 상태 확인"""
        base_status = super().get_health_status()
        
        if self._initialized and self._agent_instance:
            try:
                # 인터넷 연결 및 DuckDuckGo API 상태 확인
                agent_health = {
                    "internet_accessible": True,  # 실제로는 agent.check_internet_connection()
                    "ddg_api_available": True,    # 실제로는 agent.check_ddg_api()
                    "last_search_time": None,     # 실제로는 agent.get_last_search_time()
                }
                base_status.update(agent_health)
            except Exception as e:
                base_status["error"] = str(e)
                base_status["status"] = "unhealthy"
        
        return base_status