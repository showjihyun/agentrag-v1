"""
Refactored Agent Executor with improved code quality.
"""
import logging
import uuid
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from backend.db.models.agent_builder import (
    Agent,
    AgentExecution,
    ExecutionMetrics,
    AgentKnowledgebase
)
from backend.services.agent_builder.agent_service import AgentService
from backend.services.agent_builder.variable_resolver import VariableResolver
from backend.services.agent_builder.knowledgebase_service import KnowledgebaseService
from backend.models.agent_builder import ExecutionContext
from backend.core.retry_handler import retry_async, RetryConfig, CircuitBreaker
from backend.services.base_service import ServiceError

logger = logging.getLogger(__name__)


class AgentExecutionError(ServiceError):
    """Agent execution specific error."""
    
    def __init__(self, message: str, agent_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AgentExecutor", details)
        self.agent_id = agent_id


class AgentExecutor:
    """
    Refactored service for executing agents with improved code quality.
    
    Key improvements:
    - Broken down long functions into smaller, focused methods
    - Better separation of concerns
    - Improved error handling
    - Enhanced type hints
    - Reduced code duplication
    """
    
    # Configuration constants
    DEFAULT_TIMEOUT = 60.0
    MAX_ITERATIONS = 10
    MAX_HISTORY_LENGTH = 20
    LTM_SIMILARITY_THRESHOLD = 0.7
    
    def __init__(self, db: Session):
        """
        Initialize Agent Executor.
        
        Args:
            db: Database session
        """
        self.db = db
        self.agent_service = AgentService(db)
        self.variable_resolver = VariableResolver(db)
        self.kb_service = KnowledgebaseService(db)
        
        # Initialize circuit breakers
        self._init_circuit_breakers()
        
        # Initialize retry configurations
        self._init_retry_configs()
    
    def _init_circuit_breakers(self) -> None:
        """Initialize circuit breakers for external services."""
        self.milvus_circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0
        )
        self.llm_circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30.0
        )
    
    def _init_retry_configs(self) -> None:
        """Initialize retry configurations."""
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
            
        Raises:
            AgentExecutionError: If execution fails
        """
        execution_id = str(uuid.uuid4())
        execution = None
        
        try:
            # Validate and get agent
            agent = await self._get_and_validate_agent(agent_id)
            
            # Create execution record
            execution = self._create_execution_record(
                execution_id, agent_id, user_id, input_data, session_id, agent
            )
            
            # Build execution context
            context = self._build_execution_context(
                execution_id, user_id, agent_id, execution.session_id,
                input_data, variables
            )
            
            # Prepare execution
            resolved_input, kb_ids = await self._prepare_execution(
                agent, input_data, context
            )
            context.knowledgebases = kb_ids
            
            # Execute agent
            result = await self._execute_with_retry(
                agent, resolved_input, context
            )
            
            # Finalize execution
            self._finalize_execution(execution, result)
            
            logger.info(
                "Agent execution completed",
                extra={"execution_id": execution_id, "agent_id": agent_id}
            )
            
            return execution
            
        except Exception as e:
            self._handle_execution_failure(execution, e, agent_id)
            raise
    
    async def _get_and_validate_agent(self, agent_id: str) -> Agent:
        """
        Get and validate agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent model
            
        Raises:
            AgentExecutionError: If agent not found
        """
        agent = await self.agent_service.get_agent(agent_id)
        if not agent:
            raise AgentExecutionError(
                f"Agent not found: {agent_id}",
                agent_id=agent_id
            )
        return agent
    
    def _create_execution_record(
        self,
        execution_id: str,
        agent_id: str,
        user_id: str,
        input_data: Dict[str, Any],
        session_id: Optional[str],
        agent: Agent
    ) -> AgentExecution:
        """
        Create execution record in database.
        
        Args:
            execution_id: Execution ID
            agent_id: Agent ID
            user_id: User ID
            input_data: Input data
            session_id: Session ID
            agent: Agent model
            
        Returns:
            Created AgentExecution
        """
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
        return execution
    
    def _build_execution_context(
        self,
        execution_id: str,
        user_id: str,
        agent_id: str,
        session_id: str,
        input_data: Dict[str, Any],
        variables: Optional[Dict[str, Any]]
    ) -> ExecutionContext:
        """
        Build execution context.
        
        Args:
            execution_id: Execution ID
            user_id: User ID
            agent_id: Agent ID
            session_id: Session ID
            input_data: Input data
            variables: Runtime variables
            
        Returns:
            ExecutionContext
        """
        return ExecutionContext(
            execution_id=execution_id,
            user_id=user_id,
            agent_id=agent_id,
            session_id=session_id,
            input_data=input_data,
            variables=variables or {}
        )
    
    async def _prepare_execution(
        self,
        agent: Agent,
        input_data: Dict[str, Any],
        context: ExecutionContext
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Prepare execution by resolving variables and loading knowledgebases.
        
        Args:
            agent: Agent model
            input_data: Input data
            context: Execution context
            
        Returns:
            Tuple of (resolved_input, knowledgebase_ids)
        """
        # Resolve variables
        resolved_input = await self._resolve_input_variables(input_data, context)
        
        # Load knowledgebases
        kb_ids = await self._load_agent_knowledgebases(agent)
        
        return resolved_input, kb_ids
    
    async def _resolve_input_variables(
        self,
        input_data: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """
        Resolve variables in input data.
        
        Args:
            input_data: Input data with potential variables
            context: Execution context
            
        Returns:
            Resolved input data
        """
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
        """
        Load knowledgebases for agent.
        
        Args:
            agent: Agent model
            
        Returns:
            List of knowledgebase IDs
        """
        agent_kbs = self.db.query(AgentKnowledgebase).filter(
            AgentKnowledgebase.agent_id == agent.id
        ).order_by(AgentKnowledgebase.priority).all()
        
        return [str(kb.knowledgebase_id) for kb in agent_kbs]
    
    @retry_async(RetryConfig(max_attempts=3, initial_delay=1.0, timeout=90.0))
    async def _execute_with_retry(
        self,
        agent: Agent,
        resolved_input: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """
        Execute agent with retry logic.
        
        Args:
            agent: Agent to execute
            resolved_input: Resolved input data
            context: Execution context
            
        Returns:
            Execution result
        """
        # Initialize services
        services = await self._initialize_services()
        
        # Create aggregator
        aggregator = self._create_aggregator(services)
        
        # Execute with timeout
        result = await self._execute_with_timeout(
            aggregator,
            resolved_input,
            context
        )
        
        return result
    
    async def _initialize_services(self) -> Dict[str, Any]:
        """
        Initialize all required services with circuit breakers.
        
        Returns:
            Dictionary of initialized services
        """
        # Initialize LLM manager
        llm_manager = await self._init_llm_manager_with_circuit_breaker()
        
        # Initialize embedding service
        from backend.services.embedding import EmbeddingService
        embedding_service = EmbeddingService()
        
        # Initialize Milvus manager
        milvus_manager = await self._init_milvus_with_circuit_breaker(
            embedding_service
        )
        
        # Initialize memory manager
        memory_manager = await self._init_memory_manager(
            milvus_manager,
            embedding_service
        )
        
        # Initialize MCP manager
        from backend.mcp.manager import MCPServerManager
        mcp_manager = MCPServerManager()
        
        return {
            "llm_manager": llm_manager,
            "embedding_service": embedding_service,
            "milvus_manager": milvus_manager,
            "memory_manager": memory_manager,
            "mcp_manager": mcp_manager
        }
    
    async def _init_memory_manager(
        self,
        milvus_manager: Any,
        embedding_service: Any
    ) -> Any:
        """
        Initialize memory manager.
        
        Args:
            milvus_manager: Milvus manager instance
            embedding_service: Embedding service instance
            
        Returns:
            Memory manager instance
        """
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
        
        return MemoryManager(
            stm=stm,
            ltm=ltm,
            max_history_length=self.MAX_HISTORY_LENGTH,
            ltm_similarity_threshold=self.LTM_SIMILARITY_THRESHOLD
        )
    
    def _create_aggregator(self, services: Dict[str, Any]) -> Any:
        """
        Create aggregator agent with specialized agents.
        
        Args:
            services: Dictionary of initialized services
            
        Returns:
            Aggregator agent instance
        """
        from backend.agents.aggregator import AggregatorAgent
        from backend.agents.vector_search import VectorSearchAgent
        from backend.agents.local_data import LocalDataAgent
        from backend.agents.web_search import WebSearchAgent
        
        # Create specialized agents
        vector_agent = VectorSearchAgent(
            milvus_manager=services["milvus_manager"],
            embedding_service=services["embedding_service"],
            enable_cross_encoder=True
        )
        
        local_agent = LocalDataAgent(
            mcp_manager=services["mcp_manager"],
            server_name="local_data_server"
        )
        
        search_agent = WebSearchAgent(
            mcp_manager=services["mcp_manager"],
            server_name="search_server"
        )
        
        # Create aggregator
        return AggregatorAgent(
            llm_manager=services["llm_manager"],
            memory_manager=services["memory_manager"],
            vector_agent=vector_agent,
            local_agent=local_agent,
            search_agent=search_agent,
            max_iterations=self.MAX_ITERATIONS
        )
    
    async def _execute_with_timeout(
        self,
        aggregator: Any,
        resolved_input: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """
        Execute aggregator with timeout.
        
        Args:
            aggregator: Aggregator agent
            resolved_input: Resolved input data
            context: Execution context
            
        Returns:
            Execution result
            
        Raises:
            TimeoutError: If execution exceeds timeout
        """
        query = self._extract_query(resolved_input)
        
        try:
            # Collect steps from async generator
            steps = []
            final_answer = None
            
            async def collect_steps():
                async for step in aggregator.process_query(
                    query=query,
                    session_id=context.session_id,
                    top_k=10
                ):
                    steps.append(step)
                    if step.type == "response":
                        return step.content
                return None
            
            final_answer = await asyncio.wait_for(
                collect_steps(),
                timeout=self.DEFAULT_TIMEOUT
            )
            
            return {
                "output": final_answer or "No answer generated",
                "steps": [{"type": s.type, "content": s.content} for s in steps],
                "tokens_used": 0
            }
            
        except asyncio.TimeoutError:
            logger.error(
                "Agent execution timed out",
                extra={"timeout": self.DEFAULT_TIMEOUT}
            )
            raise TimeoutError(
                f"Agent execution exceeded timeout limit ({self.DEFAULT_TIMEOUT}s)"
            )
    
    def _extract_query(self, resolved_input: Dict[str, Any]) -> str:
        """
        Extract query from resolved input.
        
        Args:
            resolved_input: Resolved input data
            
        Returns:
            Query string
        """
        return (
            resolved_input.get("query") or
            resolved_input.get("input") or
            str(resolved_input)
        )
    
    def _finalize_execution(
        self,
        execution: AgentExecution,
        result: Dict[str, Any]
    ) -> None:
        """
        Finalize execution by updating record and creating metrics.
        
        Args:
            execution: Execution record
            result: Execution result
        """
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
            execution_id=execution.id,
            llm_call_count=result.get("llm_calls", 0),
            llm_total_tokens=result.get("total_tokens", 0),
            tool_call_count=result.get("tool_calls", 0)
        )
        self.db.add(metrics)
        
        self.db.commit()
        self.db.refresh(execution)
    
    def _handle_execution_failure(
        self,
        execution: Optional[AgentExecution],
        error: Exception,
        agent_id: str
    ) -> None:
        """
        Handle execution failure.
        
        Args:
            execution: Execution record (if created)
            error: Exception that occurred
            agent_id: Agent ID
        """
        logger.error(
            "Agent execution failed",
            extra={"agent_id": agent_id, "error": str(error)},
            exc_info=True
        )
        
        if execution:
            execution.status = "failed"
            execution.error_message = str(error)
            execution.completed_at = datetime.utcnow()
            if execution.started_at:
                execution.duration_ms = int(
                    (execution.completed_at - execution.started_at).total_seconds() * 1000
                )
            self.db.commit()
    
    async def _init_llm_manager_with_circuit_breaker(self) -> Any:
        """Initialize LLM manager with circuit breaker."""
        from backend.services.llm_manager import LLMManager
        
        def init_llm():
            return LLMManager()
        
        return await self.llm_circuit_breaker.call_async(
            lambda: asyncio.to_thread(init_llm)
        )
    
    async def _init_milvus_with_circuit_breaker(
        self,
        embedding_service: Any
    ) -> Any:
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
