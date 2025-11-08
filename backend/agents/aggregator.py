"""
Aggregator Agent with ReAct and Chain of Thought reasoning.

This agent coordinates specialized agents using LangGraph to implement
advanced reasoning patterns including ReAct (Reasoning + Acting) and
Chain of Thought (CoT) planning.
"""

import logging
import json
import uuid
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from backend.models.agent import AgentState, AgentStep
from backend.services.llm_manager import LLMManager
from backend.memory.manager import MemoryManager
from backend.services.observation_processor import ObservationProcessor
from backend.services.retry_handler import RetryableActionExecutor, RetryHandler
from backend.services.episodic_memory import EpisodicMemory
from backend.agents.vector_search import VectorSearchAgent
from backend.agents.local_data import LocalDataAgent
from backend.agents.web_search import WebSearchAgent
from backend.agents.router import AgentRouter
from backend.agents.parallel_executor import ParallelAgentExecutor
from backend.agents.error_recovery import AgentErrorRecovery

logger = logging.getLogger(__name__)


class AggregatorAgent:
    """
    Master agent that coordinates specialized agents using ReAct and CoT patterns.

    Features:
    - Chain of Thought (CoT) planning for complex queries
    - ReAct (Reasoning + Acting) pattern for decision making
    - Memory management (STM + LTM)
    - Specialized agent coordination
    - Streaming support for real-time updates
    """

    def __init__(
        self,
        llm_manager: LLMManager,
        memory_manager: MemoryManager,
        vector_agent: VectorSearchAgent,
        local_agent: LocalDataAgent,
        search_agent: WebSearchAgent,
        max_iterations: int = 10,
    ):
        """
        Initialize the Aggregator Agent.

        Args:
            llm_manager: LLM manager for text generation
            memory_manager: Memory manager for STM and LTM
            vector_agent: Vector search agent
            local_agent: Local data agent
            search_agent: Web search agent
            max_iterations: Maximum reasoning iterations
        """
        self.llm = llm_manager
        self.memory = memory_manager
        self.vector_agent = vector_agent
        self.local_agent = local_agent
        self.search_agent = search_agent
        self.max_iterations = max_iterations

        # Initialize new components (Phase 1 improvements)
        self.router = AgentRouter(llm_manager=llm_manager)
        self.parallel_executor = ParallelAgentExecutor(max_concurrent=3)
        self.error_recovery = AgentErrorRecovery()

        # Initialize observation processor (HIGH PRIORITY improvement #1)
        from backend.services.embedding import EmbeddingService

        embedding_service = EmbeddingService()
        self.observation_processor = ObservationProcessor(embedding_service)

        # Initialize retry handler (HIGH PRIORITY improvement #2)
        self.retry_handler = RetryHandler(
            max_retries=3,
            base_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
            jitter=True,
        )
        self.retryable_executor = RetryableActionExecutor(
            retry_handler=self.retry_handler
        )

        # Initialize episodic memory (HIGH PRIORITY improvement #3)
        self.episodic_memory = EpisodicMemory(
            embedding_service=embedding_service,
            ltm_manager=memory_manager.ltm,
            max_episodes=1000,
            similarity_threshold=0.85,
            min_confidence=0.7,
            retention_days=30,
        )

        # Agent registry for parallel execution
        self.agents = {
            "vector_agent": vector_agent,
            "search_agent": search_agent,
            "local_agent": local_agent,
        }

        # Create agent graph
        self.agent_graph = self._create_agent_graph()

        logger.info(
            f"AggregatorAgent initialized with max_iterations={max_iterations}, "
            f"parallel_execution=enabled, smart_routing=enabled"
        )

    def _analyze_query_complexity(self, query: str) -> str:
        """
        Analyze query complexity to determine processing path.

        Args:
            query: User query

        Returns:
            str: "simple", "medium", or "complex"
        """
        query_lower = query.lower()
        words = query.split()

        # Simple query indicators
        simple_indicators = [
            len(words) <= 10,
            query.endswith("?"),
            not any(
                word in query_lower
                for word in ["compare", "analyze", "explain why", "how does", "what if"]
            ),
        ]

        # Complex query indicators
        complex_indicators = [
            len(words) > 30,
            any(
                word in query_lower
                for word in [
                    "compare",
                    "contrast",
                    "analyze",
                    "evaluate",
                    "explain why",
                ]
            ),
            query_lower.count("and") > 2,
            query_lower.count("or") > 2,
        ]

        if sum(complex_indicators) >= 2:
            return "complex"
        elif sum(simple_indicators) >= 2:
            return "simple"
        else:
            return "medium"

    async def _fast_path_query(
        self, query: str, session_id: str, top_k: int = 10
    ) -> AsyncGenerator[AgentStep, None]:
        """
        Fast path for simple queries - skip full ReAct cycle.

        Workflow:
        1. Load memory context
        2. Vector search
        3. Direct synthesis

        Args:
            query: User query
            session_id: Session identifier
            top_k: Number of results to retrieve

        Yields:
            AgentStep objects
        """
        try:
            # Step 1: Load memory context
            yield AgentStep(
                step_id=f"memory_{uuid.uuid4().hex[:8]}",
                type="memory",
                content="Loading conversation context...",
                timestamp=datetime.now(),
                metadata={"step": "load_memory", "path": "fast"},
            )

            memory_context = await self.memory.get_context_for_query(
                session_id=session_id, query=query
            )

            # Step 2: Vector search
            yield AgentStep(
                step_id=f"action_{uuid.uuid4().hex[:8]}",
                type="action",
                content=f"Searching knowledge base for: {query}",
                timestamp=datetime.now(),
                metadata={"step": "vector_search", "path": "fast"},
            )

            search_results = await self.vector_agent.search(query=query, top_k=top_k)

            yield AgentStep(
                step_id=f"observation_{uuid.uuid4().hex[:8]}",
                type="observation",
                content=f"Found {len(search_results)} relevant documents",
                timestamp=datetime.now(),
                metadata={"step": "search_results", "count": len(search_results)},
            )

            # Step 3: Synthesize response
            yield AgentStep(
                step_id=f"synthesis_{uuid.uuid4().hex[:8]}",
                type="thought",
                content="Generating response from retrieved documents...",
                timestamp=datetime.now(),
                metadata={"step": "synthesize", "path": "fast"},
            )

            # Prepare context for synthesis
            context_docs = "\n\n".join(
                [
                    f"Document {i+1} ({result.get('document_name', result.document_name if hasattr(result, 'document_name') else 'Unknown')}):\n{result.get('text', result.text if hasattr(result, 'text') else '')}"
                    for i, result in enumerate(search_results[:5])
                ]
            )

            synthesis_prompt = f"""Based on the following documents, answer the user's question concisely.

Question: {query}

Documents:
{context_docs}

Provide a clear, direct answer based on the information above. If the documents don't contain relevant information, say so."""

            response = await self.llm.generate(
                [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that answers questions based on provided documents.",
                    },
                    {"role": "user", "content": synthesis_prompt},
                ]
            )

            # Yield final response
            yield AgentStep(
                step_id=f"response_{uuid.uuid4().hex[:8]}",
                type="response",
                content=response,
                timestamp=datetime.now(),
                metadata={
                    "step": "final_response",
                    "path": "fast",
                    "sources": [
                        {
                            "document_id": result.get(
                                "document_id",
                                (
                                    result.document_id
                                    if hasattr(result, "document_id")
                                    else ""
                                ),
                            ),
                            "document_name": result.get(
                                "document_name",
                                (
                                    result.document_name
                                    if hasattr(result, "document_name")
                                    else "Unknown"
                                ),
                            ),
                            "chunk_id": result.get(
                                "chunk_id",
                                result.chunk_id if hasattr(result, "chunk_id") else "",
                            ),
                            "score": result.get(
                                "score",
                                result.score if hasattr(result, "score") else 0.0,
                            ),
                        }
                        for result in search_results[:5]
                    ],
                },
            )

            # Save to memory
            await self.memory.consolidate_memory(
                session_id=session_id,
                query=query,
                response=response,
                success=True,
                metadata={
                    "source_count": len(search_results),
                    "action_count": 1,
                    "path": "fast",
                },
            )

        except Exception as e:
            logger.error(f"Error in fast path query: {e}")
            yield AgentStep(
                step_id=f"error_{uuid.uuid4().hex[:8]}",
                type="error",
                content=f"Error processing query: {str(e)}",
                timestamp=datetime.now(),
                metadata={"error": str(e), "path": "fast"},
            )

    def _create_agent_graph(self) -> StateGraph:
        """
        Create LangGraph StateGraph with all nodes and edges.

        Returns:
            Compiled StateGraph
        """
        # Create workflow
        workflow = StateGraph(dict)

        # Add nodes
        workflow.add_node("load_memory", self._load_memory_context)
        workflow.add_node("cot_planning", self._chain_of_thought_planning)
        workflow.add_node("react_reasoning", self._react_reasoning)
        workflow.add_node("execute_action", self._execute_action)
        workflow.add_node("reflect", self._reflect_on_results)
        workflow.add_node("synthesize", self._synthesize_response)
        workflow.add_node("save_memory", self._save_to_memory)

        # Define edges
        workflow.set_entry_point("load_memory")
        workflow.add_edge("load_memory", "cot_planning")
        workflow.add_edge("cot_planning", "react_reasoning")
        workflow.add_edge("react_reasoning", "execute_action")
        workflow.add_edge("execute_action", "reflect")

        # Conditional edge from reflect
        workflow.add_conditional_edges(
            "reflect",
            self._should_continue,
            {"continue": "react_reasoning", "synthesize": "synthesize", "end": END},
        )

        workflow.add_edge("synthesize", "save_memory")
        workflow.add_edge("save_memory", END)

        return workflow.compile()

    async def _save_episode_if_successful(
        self,
        query: str,
        actions: List[Dict[str, Any]],
        success: bool,
        confidence: float,
        total_iterations: int,
        elapsed_time: float,
        retrieved_docs_count: int,
    ):
        """Save episode to episodic memory if successful."""
        try:
            await self.episodic_memory.store_episode(
                query=query,
                actions=actions,
                success=success,
                confidence=confidence,
                total_iterations=total_iterations,
                elapsed_time=elapsed_time,
                retrieved_docs_count=retrieved_docs_count,
                metadata={"timestamp": datetime.now().isoformat()},
            )
        except Exception as e:
            logger.error(f"Error saving episode: {e}")

    async def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        top_k: int = 10,
        speculative_results: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[AgentStep, None]:
        """
        Process a query using the agent graph with streaming support.

        Args:
            query: User query
            session_id: Optional session ID for context
            top_k: Number of results to retrieve
            speculative_results: Optional speculative findings to incorporate

        Yields:
            AgentStep objects for real-time updates

        Raises:
            ValueError: If query is empty

        Requirements: 9.3, 9.4
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Generate session ID if not provided
        if not session_id:
            session_id = f"session_{uuid.uuid4().hex[:8]}"

        logger.info(f"Processing query for session {session_id}: {query[:100]}...")

        # Check episodic memory for similar successful patterns (HIGH PRIORITY improvement #3)
        import time

        start_time = time.time()

        similar_episode = await self.episodic_memory.retrieve_similar_episode(query)
        if similar_episode:
            episode, similarity = similar_episode
            logger.info(
                f"🎯 Reusing successful pattern: similarity={similarity:.3f}, "
                f"original_iterations={episode.total_iterations}, "
                f"reuse_count={episode.reuse_count}"
            )

            # Yield episode reuse notification
            yield AgentStep(
                step_id=f"episode_reuse_{uuid.uuid4().hex[:8]}",
                type="info",
                content=f"Found similar successful pattern (similarity: {similarity:.1%}). Reusing proven approach.",
                timestamp=datetime.now(),
                metadata={
                    "episode_similarity": similarity,
                    "episode_confidence": episode.confidence,
                    "episode_iterations": episode.total_iterations,
                    "episode_reuse_count": episode.reuse_count,
                },
            )

        # Log if speculative results are provided
        if speculative_results:
            logger.info(
                f"Incorporating speculative results: "
                f"confidence={speculative_results.get('confidence_score', 0):.3f}, "
                f"sources={len(speculative_results.get('sources', []))}"
            )

        # Analyze query complexity and choose path
        complexity = self._analyze_query_complexity(query)
        logger.info(f"Query complexity: {complexity}")

        # Use fast path for simple queries
        if complexity == "simple":
            async for step in self._fast_path_query(query, session_id, top_k):
                yield step
            return

        # Initialize state
        initial_state = {
            "query": query,
            "session_id": session_id,
            "planning_steps": [],
            "action_history": [],
            "retrieved_docs": [],
            "reasoning_steps": [],
            "final_response": None,
            "memory_context": {},
            "current_action": None,
            "reflection_decision": None,
            "error": None,
            "speculative_results": speculative_results,  # Add speculative results to state
        }

        final_state = None
        success = False

        try:
            # Execute graph and stream steps
            async for state in self._stream_graph_execution(initial_state):
                final_state = state
                # Yield new reasoning steps
                reasoning_steps = state.get("reasoning_steps", [])
                for step in reasoning_steps:
                    if isinstance(step, dict):
                        # Convert dict to AgentStep
                        yield AgentStep(**step)
                    elif isinstance(step, AgentStep):
                        yield step

            # Mark as successful if we completed without errors
            success = True

        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            logger.error(error_msg)

            # Yield error step
            yield AgentStep(
                step_id=f"error_{uuid.uuid4().hex[:8]}",
                type="error",
                content=error_msg,
                timestamp=datetime.now(),
                metadata={"error": str(e)},
            )

        finally:
            # Save episode to episodic memory if successful
            if success and final_state:
                elapsed_time = time.time() - start_time
                actions = final_state.get("action_history", [])
                retrieved_docs = final_state.get("retrieved_docs", [])

                # Calculate confidence based on results
                confidence = min(1.0, len(retrieved_docs) / max(top_k, 1))

                # Save episode asynchronously (don't block)
                import asyncio

                asyncio.create_task(
                    self._save_episode_if_successful(
                        query=query,
                        actions=actions,
                        success=True,
                        confidence=confidence,
                        total_iterations=len(actions),
                        elapsed_time=elapsed_time,
                        retrieved_docs_count=len(retrieved_docs),
                    )
                )

    async def _stream_graph_execution(
        self, initial_state: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute graph and stream state updates.

        Args:
            initial_state: Initial state dictionary

        Yields:
            State dictionaries after each node execution
        """
        # Track last yielded step count
        last_step_count = 0

        # Execute graph
        async for state in self.agent_graph.astream(initial_state):
            # Get current reasoning steps
            current_steps = state.get("reasoning_steps", [])

            # Only yield if new steps were added
            if len(current_steps) > last_step_count:
                # Create a state with only new steps
                new_state = state.copy()
                new_state["reasoning_steps"] = current_steps[last_step_count:]
                last_step_count = len(current_steps)

                yield new_state

    async def _load_memory_context(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load relevant context from STM and LTM, and incorporate speculative results.

        Args:
            state: Current agent state

        Returns:
            Updated state with memory context and speculative findings

        Requirements: 9.3, 9.4
        """
        session_id = state.get("session_id", "default")
        query = state["query"]
        speculative_results = state.get("speculative_results")

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Loading memory context for session {session_id}")

        # Get memory context
        memory_context = await self.memory.get_context_for_query(
            session_id=session_id, query=query
        )

        state["memory_context"] = memory_context.to_dict()

        # Incorporate speculative results if available
        if speculative_results:
            # Add speculative sources to retrieved_docs
            speculative_sources = speculative_results.get("sources", [])
            for source in speculative_sources:
                state["retrieved_docs"].append(
                    {
                        "chunk_id": source.get("chunk_id"),
                        "document_id": source.get("document_id"),
                        "document_name": source.get("document_name"),
                        "text": source.get("text"),
                        "score": source.get("score"),
                        "metadata": {
                            **source.get("metadata", {}),
                            "path": "speculative",  # Mark as from speculative path
                        },
                    }
                )

            # Add speculative findings to memory context
            state["memory_context"]["speculative_findings"] = {
                "response": speculative_results.get("response"),
                "confidence_score": speculative_results.get("confidence_score"),
                "source_count": len(speculative_sources),
            }

            # Add reasoning step about speculative results
            step = {
                "step_id": f"speculative_{uuid.uuid4().hex[:8]}",
                "type": "thought",
                "content": (
                    f"Incorporating speculative findings: "
                    f"{len(speculative_sources)} sources, "
                    f"confidence={speculative_results.get('confidence_score', 0):.3f}. "
                    f"Will validate and expand on these results."
                ),
                "timestamp": datetime.now(),
                "metadata": {
                    "step": "incorporate_speculative",
                    "confidence": speculative_results.get("confidence_score"),
                    "source_count": len(speculative_sources),
                },
            }
            state["reasoning_steps"].append(step)

        # Add memory loading step
        step = {
            "step_id": f"memory_{uuid.uuid4().hex[:8]}",
            "type": "memory",
            "content": (
                f"Loaded context: {len(memory_context.recent_history)} recent messages, "
                f"{len(memory_context.similar_interactions)} similar past interactions"
            ),
            "timestamp": datetime.now(),
            "metadata": {"step": "load_memory"},
        }

        state["reasoning_steps"].append(step)

        return state

    async def _chain_of_thought_planning(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use Chain of Thought to create a step-by-step plan.

        Args:
            state: Current agent state

        Returns:
            Updated state with planning steps
        """
        query = state["query"]
        memory_context = state.get("memory_context", {})

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Creating Chain of Thought plan")

        # Summarize memory context
        memory_summary = self._summarize_memory_context(memory_context)

        # Create CoT planning prompt
        cot_prompt = f"""Let's think step by step to answer this query effectively.

Query: {query}

Context from memory:
{memory_summary}

Create a detailed plan with 3-5 steps. For each step, explain:
1. What information we need
2. Which agent/tool to use (vector_search, local_data, web_search)
3. Why this step is necessary

Format as:
Step 1: [Description]
- Information needed: [...]
- Tool: [...]
- Reasoning: [...]

Step 2: ...
"""

        try:
            # Generate planning response
            planning_response = await self.llm.generate(
                [
                    {
                        "role": "system",
                        "content": "You are an expert at breaking down complex queries into actionable steps.",
                    },
                    {"role": "user", "content": cot_prompt},
                ]
            )

            # Parse planning steps
            planning_steps = self._parse_planning_steps(planning_response)
            state["planning_steps"] = planning_steps

            # Add reasoning step
            step = {
                "step_id": f"planning_{uuid.uuid4().hex[:8]}",
                "type": "planning",
                "content": f"Created {len(planning_steps)}-step plan:\n{planning_response}",
                "timestamp": datetime.now(),
                "metadata": {"step": "cot_planning", "num_steps": len(planning_steps)},
            }

            state["reasoning_steps"].append(step)

        except Exception as e:
            logger.error(f"Error in CoT planning: {e}")
            # Add error step but continue
            step = {
                "step_id": f"error_{uuid.uuid4().hex[:8]}",
                "type": "error",
                "content": f"Planning error: {str(e)}. Proceeding with default plan.",
                "timestamp": datetime.now(),
                "metadata": {"error": str(e)},
            }
            state["reasoning_steps"].append(step)
            state["planning_steps"] = [
                "Search vector database for relevant information"
            ]

        return state

    def _summarize_memory_context(self, memory_context: Dict[str, Any]) -> str:
        """
        Summarize memory context for prompts.

        Args:
            memory_context: Memory context dictionary

        Returns:
            Formatted summary string
        """
        parts = []

        # Recent history
        recent_history = memory_context.get("recent_history", [])
        if recent_history:
            parts.append(f"Recent conversation ({len(recent_history)} messages):")
            for msg in recent_history[-3:]:  # Last 3 messages
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:100]
                parts.append(f"  {role}: {content}...")

        # Similar interactions
        similar = memory_context.get("similar_interactions", [])
        if similar:
            parts.append(f"\nSimilar past interactions ({len(similar)}):")
            for interaction in similar[:2]:  # Top 2
                query = interaction.get("query", "")[:80]
                parts.append(f"  - {query}...")

        # Working memory
        working = memory_context.get("working_memory", {})
        if working:
            parts.append(f"\nWorking memory: {len(working)} items")

        return "\n".join(parts) if parts else "No prior context available"

    def _parse_planning_steps(self, planning_response: str) -> List[str]:
        """
        Parse planning steps from LLM response.

        Args:
            planning_response: Raw planning text

        Returns:
            List of planning step strings
        """
        steps = []
        lines = planning_response.split("\n")

        current_step = []
        for line in lines:
            line = line.strip()

            # Check if this is a step header
            if line.startswith("Step ") and ":" in line:
                # Save previous step
                if current_step:
                    steps.append("\n".join(current_step))
                    current_step = []

                # Start new step
                current_step.append(line)
            elif line and current_step:
                # Add to current step
                current_step.append(line)

        # Add last step
        if current_step:
            steps.append("\n".join(current_step))

        # If no steps found, return the whole response as one step
        if not steps:
            steps = [planning_response]

        return steps

    async def _react_reasoning(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        ReAct: Reason about next action based on current state.

        Args:
            state: Current agent state

        Returns:
            Updated state with current action
        """
        query = state["query"]
        completed_actions = len(state["action_history"])
        total_planned = len(state["planning_steps"])

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"ReAct reasoning: {completed_actions}/{total_planned} actions completed"
            )

        # Check if all planned steps completed
        if completed_actions >= total_planned:
            step = {
                "step_id": f"thought_{uuid.uuid4().hex[:8]}",
                "type": "thought",
                "content": "All planned steps completed. Ready to synthesize response.",
                "timestamp": datetime.now(),
                "metadata": {"step": "react_reasoning", "decision": "synthesize"},
            }
            state["reasoning_steps"].append(step)
            return state

        # Get next planned step
        next_step = state["planning_steps"][completed_actions]

        # Format action history
        action_history_text = self._format_action_history(state["action_history"])

        # Create ReAct prompt
        react_prompt = f"""Based on the plan and current progress, determine the next action.

Original Query: {query}

Plan Step {completed_actions + 1}: {next_step}

Previous Actions:
{action_history_text}

Current Retrieved Documents: {len(state['retrieved_docs'])}

Thought: What should we do next?
Action: Which tool should we use? (vector_search/local_data/web_search)
Action Input: What parameters should we pass?

Respond in this exact format:
Thought: [your reasoning]
Action: [tool_name]
Action Input: [json parameters]
"""

        try:
            # Generate ReAct response with retry logic
            success, react_response, error_msg = (
                await self.retryable_executor.execute_llm_call_with_retry(
                    self.llm,
                    [
                        {
                            "role": "system",
                            "content": "You are using the ReAct framework. Think carefully about each action.",
                        },
                        {"role": "user", "content": react_prompt},
                    ],
                )
            )

            if not success:
                raise Exception(f"LLM call failed: {error_msg}")

            # Parse ReAct response
            thought, action, action_input = self._parse_react_response(react_response)

            # Add thought step
            step = {
                "step_id": f"thought_{uuid.uuid4().hex[:8]}",
                "type": "thought",
                "content": thought,
                "timestamp": datetime.now(),
                "metadata": {"step": "react_reasoning", "action": action},
            }
            state["reasoning_steps"].append(step)

            # Store action for execution
            state["current_action"] = {
                "action": action,
                "input": action_input,
                "thought": thought,
            }

        except Exception as e:
            logger.error(f"Error in ReAct reasoning: {e}")
            # Default to vector search
            step = {
                "step_id": f"error_{uuid.uuid4().hex[:8]}",
                "type": "error",
                "content": f"ReAct reasoning error: {str(e)}. Defaulting to vector search.",
                "timestamp": datetime.now(),
                "metadata": {"error": str(e)},
            }
            state["reasoning_steps"].append(step)

            state["current_action"] = {
                "action": "vector_search",
                "input": {"query": query, "top_k": 10},
                "thought": "Defaulting to vector search due to reasoning error",
            }

        return state

    def _format_action_history(self, action_history: List[Dict[str, Any]]) -> str:
        """
        Format action history for prompts.

        Args:
            action_history: List of action dictionaries

        Returns:
            Formatted string
        """
        if not action_history:
            return "No previous actions"

        formatted = []
        for i, action in enumerate(action_history, 1):
            formatted.append(
                f"{i}. Action: {action['action']}\n"
                f"   Input: {json.dumps(action['input'])}\n"
                f"   Observation: {action['observation']}"
            )

        return "\n".join(formatted)

    def _parse_react_response(
        self, react_response: str
    ) -> tuple[str, str, Dict[str, Any]]:
        """
        Parse ReAct response to extract thought, action, and input.

        Args:
            react_response: Raw ReAct text

        Returns:
            Tuple of (thought, action, action_input)
        """
        thought = ""
        action = "vector_search"  # Default
        action_input = {}

        lines = react_response.split("\n")

        for line in lines:
            line = line.strip()

            if line.startswith("Thought:"):
                thought = line.replace("Thought:", "").strip()
            elif line.startswith("Action:"):
                action = line.replace("Action:", "").strip().lower()
                # Clean up action name
                action = action.replace(" ", "_")
            elif line.startswith("Action Input:"):
                input_str = line.replace("Action Input:", "").strip()
                # Try to parse as JSON
                try:
                    action_input = json.loads(input_str)
                except json.JSONDecodeError:
                    # If not JSON, treat as query string
                    action_input = {"query": input_str}

        # Validate action
        valid_actions = ["vector_search", "local_data", "web_search"]
        if action not in valid_actions:
            logger.warning(f"Invalid action '{action}', defaulting to vector_search")
            action = "vector_search"

        return thought, action, action_input

    async def _execute_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the action determined by ReAct reasoning.

        Args:
            state: Current agent state

        Returns:
            Updated state with action results
        """
        current_action = state.get("current_action")
        if not current_action:
            return state

        action = current_action["action"]
        action_input = current_action["input"]
        query = state["query"]

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Executing action: {action}")

        observation = ""

        try:
            # Execute based on action type
            if action == "vector_search":
                # Execute with retry logic
                success, results, error_msg = (
                    await self.retryable_executor.execute_vector_search_with_retry(
                        self.vector_agent,
                        query=action_input.get("query", query),
                        top_k=action_input.get("top_k", 10),
                    )
                )

                if not success:
                    observation = f"Vector search failed: {error_msg}"
                    logger.error(observation)
                    # Continue with empty results
                    results = []

                # Convert results to dict format for processing
                result_dicts = []
                for result in results:
                    result_dicts.append(
                        {
                            "chunk_id": result.get(
                                "chunk_id",
                                result.chunk_id if hasattr(result, "chunk_id") else "",
                            ),
                            "document_id": result.get(
                                "document_id",
                                (
                                    result.document_id
                                    if hasattr(result, "document_id")
                                    else ""
                                ),
                            ),
                            "document_name": result.get(
                                "document_name",
                                (
                                    result.document_name
                                    if hasattr(result, "document_name")
                                    else "Unknown"
                                ),
                            ),
                            "text": result.get(
                                "text", result.text if hasattr(result, "text") else ""
                            ),
                            "content": result.get(
                                "text", result.text if hasattr(result, "text") else ""
                            ),
                            "score": result.get(
                                "score",
                                result.score if hasattr(result, "score") else 0.0,
                            ),
                            "metadata": result.get(
                                "metadata",
                                result.metadata if hasattr(result, "metadata") else {},
                            ),
                        }
                    )

                # Process observations: score relevance and filter
                processed_results = (
                    await self.observation_processor.process_observations(
                        query=query,
                        observations=result_dicts,
                        context=state,
                        filter_threshold=0.6,
                        summarize=True,
                        max_summary_length=200,
                    )
                )

                observation = (
                    f"Found {len(results)} documents, "
                    f"{len(processed_results)} relevant after filtering "
                    f"(avg relevance: {sum(r['relevance_score'] for r in processed_results) / len(processed_results):.2f})"
                    if processed_results
                    else f"Found {len(results)} documents, none met relevance threshold"
                )

                # Add processed results to retrieved_docs
                state["retrieved_docs"].extend(processed_results)

            elif action == "local_data":
                if "file_path" in action_input:
                    content = await self.local_agent.read_file(
                        action_input["file_path"]
                    )
                    observation = f"Read file: {action_input['file_path']} ({len(content)} characters)"

                    # Store content in working memory
                    await self.memory.add_working_memory(
                        session_id=state["session_id"],
                        key=f"file_{action_input['file_path']}",
                        value=content,
                    )

                elif "database_query" in action_input:
                    rows = await self.local_agent.query_database(
                        query=action_input["database_query"],
                        db_name=action_input.get("database", "default"),
                    )
                    observation = f"Query returned {len(rows)} rows"

                    # Store results in working memory
                    await self.memory.add_working_memory(
                        session_id=state["session_id"],
                        key="db_query_results",
                        value=rows,
                    )

                else:
                    observation = "No valid local data action specified"

            elif action == "web_search":
                # Execute with retry logic
                success, results, error_msg = (
                    await self.retryable_executor.execute_web_search_with_retry(
                        self.search_agent,
                        query=action_input.get("query", query),
                        num_results=action_input.get("num_results", 5),
                    )
                )

                if not success:
                    observation = f"Web search failed: {error_msg}"
                    logger.error(observation)
                    # Continue with empty results
                    results = []

                # Convert results to dict format for processing
                result_dicts = []
                for result in results:
                    result_dicts.append(
                        {
                            "source": "web",
                            "title": result.title,
                            "url": result.url,
                            "text": result.snippet,
                            "content": result.snippet,
                            "score": result.score,
                            "metadata": result.metadata,
                        }
                    )

                # Process observations: score relevance and filter
                processed_results = (
                    await self.observation_processor.process_observations(
                        query=query,
                        observations=result_dicts,
                        context=state,
                        filter_threshold=0.6,
                        summarize=True,
                        max_summary_length=200,
                    )
                )

                observation = (
                    f"Found {len(results)} web results, "
                    f"{len(processed_results)} relevant after filtering "
                    f"(avg relevance: {sum(r['relevance_score'] for r in processed_results) / len(processed_results):.2f})"
                    if processed_results
                    else f"Found {len(results)} web results, none met relevance threshold"
                )

                # Add processed results to retrieved_docs
                state["retrieved_docs"].extend(processed_results)

            else:
                observation = f"Unknown action: {action}"

            # Record action in history
            state["action_history"].append(
                {
                    "action": action,
                    "input": action_input,
                    "observation": observation,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Add action step
            step = {
                "step_id": f"action_{uuid.uuid4().hex[:8]}",
                "type": "action",
                "content": f"Action: {action}\nObservation: {observation}",
                "timestamp": datetime.now(),
                "metadata": {"step": "execute_action", "action": action},
            }
            state["reasoning_steps"].append(step)

        except Exception as e:
            observation = f"Error executing {action}: {str(e)}"
            logger.error(observation)

            # Add error step
            step = {
                "step_id": f"error_{uuid.uuid4().hex[:8]}",
                "type": "error",
                "content": observation,
                "timestamp": datetime.now(),
                "metadata": {"step": "execute_action", "error": str(e)},
            }
            state["reasoning_steps"].append(step)

            # Still record in history
            state["action_history"].append(
                {
                    "action": action,
                    "input": action_input,
                    "observation": observation,
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                }
            )

        return state

    async def _reflect_on_results(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reflect on whether we have enough information.

        Args:
            state: Current agent state

        Returns:
            Updated state with reflection decision
        """
        query = state["query"]
        completed_actions = len(state["action_history"])
        planned_steps = len(state["planning_steps"])
        retrieved_docs = len(state["retrieved_docs"])

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"Reflecting on results: {completed_actions} actions, {retrieved_docs} docs"
            )

        # Get recent observation
        recent_observation = "None"
        if state["action_history"]:
            recent_observation = state["action_history"][-1]["observation"]

        # Create reflection prompt
        reflection_prompt = f"""Reflect on the progress so far.

Original Query: {query}

Completed Actions: {completed_actions}
Planned Steps: {planned_steps}
Retrieved Documents: {retrieved_docs}

Recent Observation: {recent_observation}

Question: Do we have enough information to answer the query comprehensively?

Respond with ONE of these decisions:
- "continue" if we need more information
- "synthesize" if we have enough to answer
- "end" if the query cannot be answered

Also provide brief reasoning (1-2 sentences).

Format:
Decision: [continue/synthesize/end]
Reasoning: [your reasoning]
"""

        try:
            # Generate reflection
            reflection = await self.llm.generate(
                [{"role": "user", "content": reflection_prompt}]
            )

            # Parse decision
            decision = self._parse_reflection_decision(reflection)

            # Add reflection step
            step = {
                "step_id": f"reflection_{uuid.uuid4().hex[:8]}",
                "type": "reflection",
                "content": reflection,
                "timestamp": datetime.now(),
                "metadata": {"step": "reflect", "decision": decision},
            }
            state["reasoning_steps"].append(step)

            state["reflection_decision"] = decision

        except Exception as e:
            logger.error(f"Error in reflection: {e}")
            # Default to synthesize if we have any docs
            decision = "synthesize" if retrieved_docs > 0 else "continue"

            step = {
                "step_id": f"error_{uuid.uuid4().hex[:8]}",
                "type": "error",
                "content": f"Reflection error: {str(e)}. Defaulting to '{decision}'.",
                "timestamp": datetime.now(),
                "metadata": {"error": str(e)},
            }
            state["reasoning_steps"].append(step)

            state["reflection_decision"] = decision

        return state

    def _parse_reflection_decision(self, reflection: str) -> str:
        """
        Parse reflection decision from LLM response.

        Args:
            reflection: Raw reflection text

        Returns:
            Decision string: "continue", "synthesize", or "end"
        """
        reflection_lower = reflection.lower()

        # Look for decision line
        for line in reflection.split("\n"):
            line = line.strip().lower()

            if "decision:" in line:
                if "continue" in line:
                    return "continue"
                elif "synthesize" in line:
                    return "synthesize"
                elif "end" in line:
                    return "end"

        # Fallback: check entire text
        if "continue" in reflection_lower:
            return "continue"
        elif "synthesize" in reflection_lower:
            return "synthesize"
        elif "end" in reflection_lower:
            return "end"

        # Default to synthesize
        return "synthesize"

    def _should_continue(self, state: Dict[str, Any]) -> str:
        """
        Determine next node based on reflection.

        Args:
            state: Current agent state

        Returns:
            Next node name: "continue", "synthesize", or "end"
        """
        decision = state.get("reflection_decision", "synthesize")
        completed = len(state["action_history"])
        planned = len(state["planning_steps"])

        # Check if we've exceeded max iterations
        if completed >= self.max_iterations:
            logger.warning(
                f"Max iterations ({self.max_iterations}) reached, forcing synthesize"
            )
            return "synthesize"

        # Check if all planned steps are done
        if completed >= planned and decision == "continue":
            logger.info("All planned steps completed, forcing synthesize")
            return "synthesize"

        # Check if we have no documents and decision is end
        if decision == "end" and len(state["retrieved_docs"]) == 0:
            logger.info("No documents retrieved and decision is end")
            return "end"

        return decision

    async def _synthesize_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate final response using all gathered information, merging speculative and agentic results.

        Args:
            state: Current agent state

        Returns:
            Updated state with final response

        Requirements: 9.3, 9.4
        """
        query = state["query"]
        retrieved_docs = state["retrieved_docs"]
        action_history = state["action_history"]
        memory_context = state.get("memory_context", {})
        speculative_findings = memory_context.get("speculative_findings")

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Synthesizing response with {len(retrieved_docs)} documents")

        # Prepare context from all sources
        context_parts = []

        # Add speculative findings if available
        speculative_context = ""
        if speculative_findings:
            speculative_context = f"""
=== Initial Speculative Response ===
Confidence: {speculative_findings.get('confidence_score', 0):.2f}
Response: {speculative_findings.get('response', '')}

Note: The above was a quick initial response. Use it as a starting point but validate and expand with the detailed information below.
"""

        # Add retrieved documents (top 10)
        if retrieved_docs:
            context_parts.append("=== Retrieved Documents ===")
            for i, doc in enumerate(retrieved_docs[:10], 1):
                doc_name = doc.get("document_name") or doc.get("title", f"Document {i}")
                text = doc.get("text", "")
                score = doc.get("score", 0.0)
                source_type = doc.get("metadata", {}).get("source_type", "text")
                search_method = doc.get("metadata", {}).get("search_method", "vector")
                
                # 이미지 소스인 경우 더 자세한 설명 추가
                if source_type == "image":
                    image_info = f" [IMAGE SOURCE - {search_method.upper()}]"
                    # 이미지는 전체 텍스트 사용 (ColPali 메타데이터 포함 가능)
                    text_to_use = text
                else:
                    image_info = ""
                    # 텍스트는 1000자로 제한 (기존 500자에서 증가)
                    text_to_use = text[:1000] if len(text) > 1000 else text

                context_parts.append(
                    f"\n[Document {i}: {doc_name}]{image_info} (Score: {score:.2f})\n{text_to_use}\n"
                )

        # Add action summary
        action_summary = "\n".join(
            [
                f"- {action['action']}: {action['observation']}"
                for action in action_history
            ]
        )

        # Create synthesis prompt
        synthesis_prompt = f"""Based on all the information gathered, provide a comprehensive answer.

Original Query: {query}

{speculative_context}

Actions Taken:
{action_summary}

Retrieved Context:
{chr(10).join(context_parts[:10])}

Memory Context:
{self._summarize_memory_context(memory_context)}

Provide a detailed, well-structured answer that:
1. Directly addresses the query using information from the retrieved documents
2. Cites specific sources (use [Document N] format)
3. For IMAGE SOURCE documents, extract and use the visual information they contain
4. Builds upon and refines the initial speculative response (if provided)
5. Acknowledges any limitations or gaps
6. Is clear and actionable

IMPORTANT: If the answer is found in the retrieved documents (especially IMAGE SOURCE documents), 
you MUST provide the answer. Do not say "I cannot find" if the information is clearly present in the context.

Answer:"""

        try:
            # Generate final response
            final_response = await self.llm.generate(
                [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant providing accurate, well-cited answers. When an initial response is provided, validate and expand on it with detailed information.",
                    },
                    {"role": "user", "content": synthesis_prompt},
                ]
            )

            state["final_response"] = final_response

            # Add response step
            step = {
                "step_id": f"response_{uuid.uuid4().hex[:8]}",
                "type": "response",
                "content": final_response,
                "timestamp": datetime.now(),
                "metadata": {
                    "step": "synthesize",
                    "source_count": len(retrieved_docs),
                    "action_count": len(action_history),
                    "has_speculative": speculative_findings is not None,
                },
            }
            state["reasoning_steps"].append(step)

        except Exception as e:
            error_msg = f"Error synthesizing response: {str(e)}"
            logger.error(error_msg)

            # Provide fallback response
            fallback_response = (
                f"I encountered an error while synthesizing the response. "
                f"However, I found {len(retrieved_docs)} relevant documents. "
                f"Error: {str(e)}"
            )

            state["final_response"] = fallback_response
            state["error"] = str(e)

            step = {
                "step_id": f"error_{uuid.uuid4().hex[:8]}",
                "type": "error",
                "content": error_msg,
                "timestamp": datetime.now(),
                "metadata": {"error": str(e)},
            }
            state["reasoning_steps"].append(step)

        return state

    async def _save_to_memory(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save interaction to memory systems, marking contributing paths.

        Args:
            state: Current agent state

        Returns:
            Updated state (unchanged)

        Requirements: 9.4, 9.6
        """
        session_id = state.get("session_id", "default")
        query = state["query"]
        final_response = state.get("final_response", "")
        memory_context = state.get("memory_context", {})
        speculative_findings = memory_context.get("speculative_findings")

        # Determine if interaction was successful
        success = bool(final_response and not state.get("error"))

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Saving to memory: session={session_id}, success={success}")

        try:
            # Determine contributing paths
            contributing_paths = ["agentic"]
            if speculative_findings:
                contributing_paths.insert(0, "speculative")

            # Count sources by path
            speculative_sources = sum(
                1
                for doc in state["retrieved_docs"]
                if doc.get("metadata", {}).get("path") == "speculative"
            )
            agentic_sources = len(state["retrieved_docs"]) - speculative_sources

            # Prepare metadata
            metadata = {
                "source_count": len(state["retrieved_docs"]),
                "action_count": len(state["action_history"]),
                "has_citations": "[Document" in final_response,
                "planning_steps": len(state["planning_steps"]),
                "contributing_paths": contributing_paths,
                "path": (
                    "hybrid" if len(contributing_paths) > 1 else contributing_paths[0]
                ),
                "speculative_sources": speculative_sources,
                "agentic_sources": agentic_sources,
            }

            # Add speculative confidence if available
            if speculative_findings:
                metadata["speculative_confidence"] = speculative_findings.get(
                    "confidence_score", 0.0
                )

            # Consolidate memory
            interaction_id = await self.memory.consolidate_memory(
                session_id=session_id,
                query=query,
                response=final_response,
                success=success,
                metadata=metadata,
            )

            if interaction_id:
                logger.info(
                    f"Saved interaction to LTM: {interaction_id}, "
                    f"paths={contributing_paths}"
                )

            # Add memory save step
            step = {
                "step_id": f"memory_{uuid.uuid4().hex[:8]}",
                "type": "memory",
                "content": (
                    f"Saved interaction to memory (success={success}, "
                    f"paths={', '.join(contributing_paths)})"
                ),
                "timestamp": datetime.now(),
                "metadata": {
                    "step": "save_memory",
                    "interaction_id": interaction_id,
                    "success": success,
                    "contributing_paths": contributing_paths,
                },
            }
            state["reasoning_steps"].append(step)

        except Exception as e:
            logger.error(f"Error saving to memory: {e}")
            # Don't fail the entire process if memory save fails
            step = {
                "step_id": f"error_{uuid.uuid4().hex[:8]}",
                "type": "error",
                "content": f"Memory save error: {str(e)}",
                "timestamp": datetime.now(),
                "metadata": {"error": str(e)},
            }
            state["reasoning_steps"].append(step)

        return state

    def __repr__(self) -> str:
        return f"AggregatorAgent(max_iterations={self.max_iterations})"
