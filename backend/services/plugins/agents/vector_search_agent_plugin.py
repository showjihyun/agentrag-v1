"""
Vector Search Agent Plugin

기존 VectorSearchAgent를 Plugin 형태로 래핑
"""
from typing import Dict, List, Any
from backend.services.plugins.agents.base_agent_plugin import (
    BaseAgentPlugin, 
    AgentCapability, 
    AgentExecutionContext
)
from backend.models.plugin import PluginManifest
from backend.agents.vector_search import VectorSearchAgent
from backend.agents.base import BaseAgent


class VectorSearchAgentPlugin(BaseAgentPlugin):
    """Vector Search Agent Plugin 구현"""
    
    def get_manifest(self) -> PluginManifest:
        """플러그인 매니페스트 반환"""
        return PluginManifest(
            name="vector-search-agent",
            version="1.0.0",
            description="Semantic search agent using vector embeddings",
            author="AgenticRAG Team",
            category="orchestration",
            dependencies=["embedding-service@>=1.0.0"],
            permissions=["vector_search", "embedding_access", "milvus_access"],
            configuration_schema={
                "type": "object",
                "properties": {
                    "embedding_model": {
                        "type": "string",
                        "default": "jhgan/ko-sroberta-multitask",
                        "description": "Embedding model to use"
                    },
                    "similarity_threshold": {
                        "type": "number",
                        "default": 0.7,
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Minimum similarity threshold"
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100,
                        "description": "Maximum number of results to return"
                    },
                    "collection_name": {
                        "type": "string",
                        "default": "documents",
                        "description": "Milvus collection name"
                    }
                },
                "required": ["embedding_model", "collection_name"]
            }
        )
    
    def get_agent_type(self) -> str:
        """Agent 타입 반환"""
        return "vector_search"
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Agent 능력 반환"""
        return [
            AgentCapability(
                name="semantic_search",
                description="Perform semantic search using vector embeddings",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query text"
                        },
                        "filters": {
                            "type": "object",
                            "description": "Optional filters for search"
                        },
                        "limit": {
                            "type": "integer",
                            "default": 10,
                            "description": "Number of results to return"
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
                                    "content": {"type": "string"},
                                    "score": {"type": "number"},
                                    "metadata": {"type": "object"}
                                }
                            }
                        },
                        "total_count": {"type": "integer"},
                        "execution_time": {"type": "number"}
                    }
                },
                required_permissions=["vector_search", "milvus_access"]
            ),
            AgentCapability(
                name="similarity_search",
                description="Find similar documents based on content",
                input_schema={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Content to find similar documents for"
                        },
                        "threshold": {
                            "type": "number",
                            "default": 0.7,
                            "description": "Similarity threshold"
                        }
                    },
                    "required": ["content"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "similar_documents": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "document_id": {"type": "string"},
                                    "similarity": {"type": "number"},
                                    "content_preview": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                required_permissions=["vector_search"]
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
        """VectorSearchAgent 인스턴스 생성"""
        return VectorSearchAgent(
            embedding_model=self.config.get("embedding_model", "jhgan/ko-sroberta-multitask"),
            similarity_threshold=self.config.get("similarity_threshold", 0.7),
            max_results=self.config.get("max_results", 10),
            collection_name=self.config.get("collection_name", "documents")
        )
    
    def _get_required_config_fields(self) -> List[str]:
        """필수 설정 필드"""
        return ["embedding_model", "collection_name"]
    
    def _validate_agent_specific_config(self, config: Dict[str, Any]) -> List[str]:
        """Vector Search Agent 특화 설정 검증"""
        errors = []
        
        # 임계값 검증
        if "similarity_threshold" in config:
            threshold = config["similarity_threshold"]
            if not isinstance(threshold, (int, float)) or not (0.0 <= threshold <= 1.0):
                errors.append("similarity_threshold must be a number between 0.0 and 1.0")
        
        # 최대 결과 수 검증
        if "max_results" in config:
            max_results = config["max_results"]
            if not isinstance(max_results, int) or max_results < 1 or max_results > 100:
                errors.append("max_results must be an integer between 1 and 100")
        
        return errors
    
    def get_health_status(self) -> Dict[str, Any]:
        """Vector Search Agent 상태 확인"""
        base_status = super().get_health_status()
        
        if self._initialized and self._agent_instance:
            try:
                # Milvus 연결 상태 확인 (실제 구현에서는 agent의 health check 메서드 호출)
                agent_health = {
                    "milvus_connected": True,  # 실제로는 agent.check_milvus_connection()
                    "embedding_service_available": True,  # 실제로는 agent.check_embedding_service()
                    "collection_exists": True,  # 실제로는 agent.check_collection()
                }
                base_status.update(agent_health)
            except Exception as e:
                base_status["error"] = str(e)
                base_status["status"] = "unhealthy"
        
        return base_status