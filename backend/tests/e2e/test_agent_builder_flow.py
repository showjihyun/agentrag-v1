"""
End-to-end integration tests for Agent Builder.

Tests complete user flows from agent creation to execution.

NOTE: Some services referenced here are not yet implemented.
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.services.agent_builder.agent_service import AgentService
from backend.services.agent_builder.workflow_service import WorkflowService
from backend.services.agent_builder.block_service import BlockService
from backend.services.agent_builder.knowledgebase_service import KnowledgebaseService
# VariableService not yet implemented - using VariableResolver instead
from backend.services.agent_builder.variable_resolver import VariableResolver as VariableService
# ExecutionService not yet implemented - tests will be skipped
try:
    from backend.services.agent_builder.execution_service import ExecutionService
except ImportError:
    ExecutionService = None
from backend.services.agent_builder.tool_registry import ToolRegistry
from backend.services.llm_manager import LLMManager
from backend.services.milvus import MilvusManager
from backend.services.embedding import EmbeddingService
from backend.memory.manager import MemoryManager
from backend.models.agent_builder import (
    AgentCreate,
    WorkflowCreate,
    BlockCreate,
    KnowledgebaseCreate,
    VariableCreate,
    ExecutionContext
)


class TestAgentBuilderE2E:
    """End-to-end tests for Agent Builder flows."""
    
    @pytest.fixture
    async def db_session(self):
        """Get database session."""
        db = next(get_db())
        try:
            yield db
        finally:
            db.close()
    
    @pytest.fixture
    async def services(self, db_session):
        """Get all required services."""
        llm_manager = LLMManager()
        embedding_service = EmbeddingService()
        milvus_manager = MilvusManager()
        memory_manager = MemoryManager()
        
        tool_registry = ToolRegistry(db=db_session)
        
        return {
            "agent": AgentService(
                db=db_session,
                tool_registry=tool_registry,
                llm_manager=llm_manager
            ),
            "workflow": WorkflowService(
                db=db_session,
                tool_registry=tool_registry,
                llm_manager=llm_manager
            ),
            "block": BlockService(
                db=db_session,
                tool_registry=tool_registry
            ),
            "knowledgebase": KnowledgebaseService(
                db=db_session,
                milvus_manager=milvus_manager,
                embedding_service=embedding_service
            ),
            "variable": VariableService(db=db_session),
            "execution": ExecutionService(
                db=db_session,
                tool_registry=tool_registry,
                llm_manager=llm_manager,
                memory_manager=memory_manager
            )
        }
    
    @pytest.mark.asyncio
    async def test_complete_agent_creation_and_execution_flow(self, services):
        """
        Test complete flow:
        1. Create agent
        2. Configure tools
        3. Test agent
        4. Execute agent
        5. View execution results
        """
        user_id = "test_user_e2e"
        
        # Step 1: Create agent
        agent_data = AgentCreate(
            name="E2E Test Agent",
            description="Agent for end-to-end testing",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.2:latest",
            prompt_template="You are a helpful assistant. Answer: {query}",
            tool_ids=[]
        )
        
        agent = await services["agent"].create_agent(
            user_id=user_id,
            agent_data=agent_data
        )
        
        assert agent is not None
        assert agent.name == "E2E Test Agent"
        
        # Step 2: Execute agent
        execution_context = ExecutionContext(
            user_id=user_id,
            session_id=f"e2e_session_{datetime.now().timestamp()}"
        )
        
        input_data = {
            "query": "What is 2+2?"
        }
        
        # Collect execution steps
        steps = []
        async for step in services["execution"].execute_agent(
            agent_id=agent.id,
            input_data=input_data,
            context=execution_context
        ):
            steps.append(step)
        
        # Verify execution completed
        assert len(steps) > 0
        
        # Step 3: Get execution details
        # Find execution ID from steps
        execution_id = None
        for step in steps:
            if hasattr(step, "execution_id"):
                execution_id = step.execution_id
                break
        
        if execution_id:
            execution = await services["execution"].get_execution(execution_id)
            assert execution is not None
            assert execution.agent_id == agent.id
        
        # Cleanup
        await services["agent"].delete_agent(agent.id)
    
    @pytest.mark.asyncio
    async def test_workflow_designer_and_execution(self, services):
        """
        Test workflow flow:
        1. Create blocks
        2. Create workflow
        3. Add nodes and edges
        4. Validate workflow
        5. Execute workflow
        """
        user_id = "test_user_workflow"
        
        # Step 1: Create a simple block
        block_data = BlockCreate(
            name="Test Block",
            description="Simple test block",
            block_type="llm",
            input_schema={"query": "string"},
            output_schema={"response": "string"},
            configuration={
                "prompt_template": "Answer: ${query}"
            }
        )
        
        block = await services["block"].create_block(
            user_id=user_id,
            block_data=block_data
        )
        
        assert block is not None
        
        # Step 2: Create workflow
        workflow_data = WorkflowCreate(
            name="Test Workflow",
            description="E2E test workflow",
            graph_definition={
                "nodes": [
                    {
                        "id": "start",
                        "type": "block",
                        "block_id": block.id
                    }
                ],
                "edges": [],
                "entry_point": "start"
            }
        )
        
        workflow = await services["workflow"].create_workflow(
            user_id=user_id,
            workflow_data=workflow_data
        )
        
        assert workflow is not None
        assert workflow.name == "Test Workflow"
        
        # Step 3: Validate workflow
        validation = await services["workflow"].validate_workflow(workflow.id)
        assert validation["valid"] is True
        
        # Step 4: Execute workflow
        execution_context = ExecutionContext(
            user_id=user_id,
            session_id=f"workflow_session_{datetime.now().timestamp()}"
        )
        
        input_data = {
            "query": "Test query"
        }
        
        steps = []
        async for step in services["execution"].execute_workflow(
            workflow_id=workflow.id,
            input_data=input_data,
            context=execution_context
        ):
            steps.append(step)
        
        assert len(steps) > 0
        
        # Cleanup
        await services["workflow"].delete_workflow(workflow.id)
        await services["block"].delete_block(block.id)
    
    @pytest.mark.asyncio
    async def test_knowledgebase_creation_and_search(self, services):
        """
        Test knowledgebase flow:
        1. Create knowledgebase
        2. Upload documents
        3. Search knowledgebase
        4. Attach to agent
        5. Execute agent with KB
        """
        user_id = "test_user_kb"
        
        # Step 1: Create knowledgebase
        kb_data = KnowledgebaseCreate(
            name="Test KB",
            description="Test knowledgebase",
            embedding_model="default",
            chunk_size=500,
            chunk_overlap=50
        )
        
        kb = await services["knowledgebase"].create_knowledgebase(
            user_id=user_id,
            kb_data=kb_data
        )
        
        assert kb is not None
        assert kb.name == "Test KB"
        
        # Step 2: Search knowledgebase (empty)
        results = await services["knowledgebase"].search_knowledgebase(
            kb_id=kb.id,
            query="test query",
            top_k=5
        )
        
        assert isinstance(results, list)
        
        # Cleanup
        await services["knowledgebase"].delete_knowledgebase(kb.id)
    
    @pytest.mark.asyncio
    async def test_permission_and_sharing(self, services):
        """
        Test sharing flow:
        1. Create agent
        2. Share agent
        3. Access shared agent
        4. Clone shared agent
        """
        user_id = "test_user_share"
        other_user_id = "test_user_other"
        
        # Step 1: Create agent
        agent_data = AgentCreate(
            name="Shared Agent",
            description="Agent for sharing test",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.2:latest",
            prompt_template="Answer: {query}"
        )
        
        agent = await services["agent"].create_agent(
            user_id=user_id,
            agent_data=agent_data
        )
        
        assert agent is not None
        
        # Step 2: Mark as public (simplified sharing)
        agent.is_public = True
        
        # Step 3: Clone agent as another user
        cloned_agent = await services["agent"].clone_agent(
            agent_id=agent.id,
            user_id=other_user_id
        )
        
        assert cloned_agent is not None
        assert cloned_agent.user_id == other_user_id
        assert cloned_agent.name == agent.name
        
        # Cleanup
        await services["agent"].delete_agent(agent.id)
        await services["agent"].delete_agent(cloned_agent.id)
    
    @pytest.mark.asyncio
    async def test_execution_monitoring_and_debugging(self, services):
        """
        Test monitoring flow:
        1. Execute agent
        2. View execution list
        3. View execution details
        4. Replay execution
        """
        user_id = "test_user_monitor"
        
        # Step 1: Create and execute agent
        agent_data = AgentCreate(
            name="Monitor Test Agent",
            description="Agent for monitoring test",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.2:latest",
            prompt_template="Answer: {query}"
        )
        
        agent = await services["agent"].create_agent(
            user_id=user_id,
            agent_data=agent_data
        )
        
        # Execute
        execution_context = ExecutionContext(
            user_id=user_id,
            session_id=f"monitor_session_{datetime.now().timestamp()}"
        )
        
        input_data = {"query": "Test"}
        
        steps = []
        async for step in services["execution"].execute_agent(
            agent_id=agent.id,
            input_data=input_data,
            context=execution_context
        ):
            steps.append(step)
        
        # Step 2: List executions
        executions = await services["execution"].list_executions(
            user_id=user_id,
            filters={"agent_id": agent.id}
        )
        
        assert len(executions) > 0
        
        # Step 3: Get execution details
        execution = executions[0]
        details = await services["execution"].get_execution(execution.id)
        
        assert details is not None
        assert details.agent_id == agent.id
        
        # Cleanup
        await services["agent"].delete_agent(agent.id)
    
    @pytest.mark.asyncio
    async def test_variable_scoping_and_resolution(self, services):
        """
        Test variable flow:
        1. Create variables at different scopes
        2. Test precedence
        3. Use in agent execution
        """
        user_id = "test_user_vars"
        
        # Step 1: Create global variable
        global_var = VariableCreate(
            name="test_var",
            scope="global",
            scope_id=None,
            value_type="string",
            value="global_value"
        )
        
        var1 = await services["variable"].create_variable(
            user_id=user_id,
            variable_data=global_var
        )
        
        assert var1 is not None
        
        # Step 2: Create user variable (should override global)
        user_var = VariableCreate(
            name="test_var",
            scope="user",
            scope_id=user_id,
            value_type="string",
            value="user_value"
        )
        
        var2 = await services["variable"].create_variable(
            user_id=user_id,
            variable_data=user_var
        )
        
        assert var2 is not None
        
        # Step 3: Resolve variable (should get user value)
        resolved = await services["variable"].get_variable(
            var_name="test_var",
            scope="user",
            context={"user_id": user_id}
        )
        
        assert resolved == "user_value"
        
        # Cleanup
        await services["variable"].delete_variable(var1.id)
        await services["variable"].delete_variable(var2.id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
