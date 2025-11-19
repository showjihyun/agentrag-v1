"""Agent Executor for running agents with full context."""

import logging
import uuid
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from backend.db.models.agent_builder import (
    Agent,
    AgentExecution,
    ExecutionStep,
    ExecutionMetrics,
    AgentKnowledgebase
)
from backend.services.agent_builder.agent_service import AgentService
from backend.services.agent_builder.variable_resolver import VariableResolver
from backend.services.agent_builder.knowledgebase_service import KnowledgebaseService
from backend.models.agent_builder import ExecutionContext
from backend.core.retry_handler import retry_async, RetryConfig, CircuitBreaker

logger = logging.getLogger(__name__)


class AgentExecutor:
    """Service for executing agents with full context and resilience."""
    
    def __init__(self, db: Session):
        self.db = db
        self.agent_service = AgentService(db)
        self.variable_resolver = VariableResolver(db)
        self.kb_service = KnowledgebaseService(db)
        
        # Circuit breakers for external services
        self.milvus_circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0
        )
        self.llm_circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30.0
        )
        
        # Retry configurations
        self.llm_retry_config = RetryConfig(
            max_attempts=3,
            initial_delay=1.0,
            max_delay=10.0,
            timeout=60.0
        )
        self.db_retry_config = RetryConfig(
            max_attempts=2,
            initial_delay=0.5,
            max_delay=5.0
        )
    
    async def execute_agent(
        self,
        agent_id: str,
        user_id: str,
        input_data: Dict[str, Any],
        session_id: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> AgentExecution:
        """
        Execute an agent with full context.
        
        Args:
            agent_id: Agent ID to execute
            user_id: User ID executing the agent
            input_data: Input data for the agent
            session_id: Optional session ID for context
            variables: Optional runtime variables
            
        Returns:
            AgentExecution record with results
        """
        execution_id = str(uuid.uuid4())
        
        try:
            # Get agent
            agent = await self.agent_service.get_agent(agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            # Create execution record
            execution = AgentExecution(
                id=execution_id,
                agent_id=agent_id,
                user_id=user_id,
                session_id=session_id or f"exec_{execution_id}",
                input_data=input_data,
                execution_context={
                    "agent_name": agent.name,
                    "llm_provider": agent.llm_provider,
                    "llm_model": agent.llm_model
                },
                status="running",
                started_at=datetime.utcnow()
            )
            self.db.add(execution)
            self.db.flush()
            
            # Create execution context
            context = ExecutionContext(
                execution_id=execution_id,
                user_id=user_id,
                agent_id=agent_id,
                session_id=execution.session_id,
                input_data=input_data,
                variables=variables or {}
            )
            
            # Resolve variables
            resolved_input = await self._resolve_input_variables(input_data, context)
            
            # Load knowledgebases
            kb_ids = await self._load_agent_knowledgebases(agent)
            context.knowledgebases = kb_ids
            
            # Execute agent using AggregatorAgent with retry and circuit breaker
            result = await self._execute_agent_with_resilience(
                agent=agent,
                resolved_input=resolved_input,
                context=context
            )
            
            # Update execution record
            execution.output_data = result
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            execution.duration_ms = int(
                (execution.completed_at - execution.started_at).total_seconds() * 1000
            )
            
            # Create metrics
            metrics = ExecutionMetrics(
                id=str(uuid.uuid4()),
                execution_id=execution_id,
                llm_call_count=result.get("llm_calls", 0),
                llm_total_tokens=result.get("total_tokens", 0),
                tool_call_count=result.get("tool_calls", 0)
            )
            self.db.add(metrics)
            
            self.db.commit()
            self.db.refresh(execution)
            
            logger.info(f"Agent execution completed: {execution_id}")
            return execution
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}", exc_info=True)
            
            # Update execution as failed
            if 'execution' in locals():
                execution.status = "failed"
                execution.error_message = str(e)
                execution.completed_at = datetime.utcnow()
                if execution.started_at:
                    execution.duration_ms = int(
                        (execution.completed_at - execution.started_at).total_seconds() * 1000
                    )
                self.db.commit()
            
            raise
    
    async def _resolve_input_variables(
        self,
        input_data: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Resolve variables in input data."""
        resolved = {}
        
        for key, value in input_data.items():
            if isinstance(value, str) and "${" in value:
                resolved[key] = await self.variable_resolver.resolve_variables(
                    template=value,
                    context=context
                )
            else:
                resolved[key] = value
        
        return resolved
    
    async def _load_agent_knowledgebases(self, agent: Agent) -> List[str]:
        """Load knowledgebases for agent."""
        agent_kbs = self.db.query(AgentKnowledgebase).filter(
            AgentKnowledgebase.agent_id == agent.id
        ).order_by(AgentKnowledgebase.priority).all()
        
        return [str(kb.knowledgebase_id) for kb in agent_kbs]
    
    @retry_async(RetryConfig(max_attempts=3, initial_delay=1.0, timeout=90.0))
    async def _execute_agent_with_resilience(
        self,
        agent: Agent,
        resolved_input: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """
        Execute agent with retry logic and circuit breakers.
        
        Args:
            agent: Agent to execute
            resolved_input: Resolved input data
            context: Execution context
            
        Returns:
            Execution result
        """
        from backend.agents.aggregator import AggregatorAgent
        from backend.services.llm_manager import LLMManager
        from backend.services.embedding import EmbeddingService
        from backend.services.milvus import MilvusManager
        from backend.config import settings
        
        try:
            # Initialize services with circuit breakers
            llm_manager = await self._init_llm_manager_with_circuit_breaker()
            embedding_service = EmbeddingService()
            milvus_manager = await self._init_milvus_with_circuit_breaker(
                embedding_service
            )
            
            # Initialize memory manager
            from backend.memory.manager import MemoryManager
            from backend.memory.stm import ShortTermMemory
            from backend.memory.ltm import LongTermMemory
            from backend.config import settings
            
            stm = ShortTermMemory(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                ttl=3600
            )
            
            ltm = LongTermMemory(
                milvus_manager=milvus_manager,
                embedding_service=embedding_service
            )
            
            memory_manager = MemoryManager(
                stm=stm,
                ltm=ltm,
                max_history_length=20,
                ltm_similarity_threshold=0.7
            )
            
            # Initialize specialized agents
            from backend.agents.vector_search import VectorSearchAgent
            from backend.agents.local_data import LocalDataAgent
            from backend.agents.web_search import WebSearchAgent
            
            # VectorSearchAgent can work with direct Milvus (no MCP required)
            vector_agent = VectorSearchAgent(
                milvus_manager=milvus_manager,
                embedding_service=embedding_service,
                enable_cross_encoder=True
            )
            
            # LocalDataAgent and WebSearchAgent need MCP manager
            from backend.mcp.manager import MCPServerManager
            mcp_manager = MCPServerManager()
            
            local_agent = LocalDataAgent(
                mcp_manager=mcp_manager,
                server_name="local_data_server"
            )
            
            search_agent = WebSearchAgent(
                mcp_manager=mcp_manager,
                server_name="search_server"
            )
            
            # Create aggregator
            aggregator = AggregatorAgent(
                llm_manager=llm_manager,
                memory_manager=memory_manager,
                vector_agent=vector_agent,
                local_agent=local_agent,
                search_agent=search_agent,
                max_iterations=10
            )
            
            # Execute with timeout
            query = resolved_input.get("query") or resolved_input.get("input") or str(resolved_input)
            session_id = context.session_id
            
            # Collect all steps from the async generator
            steps = []
            final_answer = None
            
            async def collect_steps():
                async for step in aggregator.process_query(
                    query=query,
                    session_id=session_id,
                    top_k=10
                ):
                    steps.append(step)
                    if step.type == "response":
                        return step.content
                return None
            
            final_answer = await asyncio.wait_for(
                collect_steps(),
                timeout=60.0  # 60 second timeout
            )
            
            return {
                "output": final_answer or "No answer generated",
                "steps": [{"type": s.type, "content": s.content} for s in steps],
                "tokens_used": 0
            }
            
        except asyncio.TimeoutError:
            logger.error(f"Agent execution timed out for agent {agent.id}")
            raise TimeoutError("Agent execution exceeded timeout limit")
        except Exception as e:
            logger.error(f"Agent execution failed: {e}", exc_info=True)
            raise
    
    async def _init_llm_manager_with_circuit_breaker(self):
        """Initialize LLM manager with circuit breaker."""
        from backend.services.llm_manager import LLMManager
        
        def init_llm():
            return LLMManager()
        
        return await self.llm_circuit_breaker.call_async(
            lambda: asyncio.to_thread(init_llm)
        )
    
    async def _init_milvus_with_circuit_breaker(self, embedding_service):
        """Initialize Milvus manager with circuit breaker."""
        from backend.services.milvus import MilvusManager
        from backend.config import settings
        
        def init_milvus():
            return MilvusManager(
                collection_name=settings.MILVUS_COLLECTION_NAME,
                embedding_dim=embedding_service.dimension
            )
        
        return await self.milvus_circuit_breaker.call_async(
            lambda: asyncio.to_thread(init_milvus)
        )
