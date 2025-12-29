"""
Integration tests for AgentWorkflow, Agent, and Block relationships.
"""

import pytest
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from backend.db.models.flows import Agentflow, AgentflowAgent, AgentflowEdge
from backend.db.models.agent_builder import Agent, Block
from backend.services.agent_builder.integration_service import AgentWorkflowIntegrationService
from backend.services.agent_builder.shared.errors import NotFoundError, ValidationError


class TestAgentWorkflowIntegration:
    """Test AgentWorkflow integration with Agents and Blocks."""
    
    @pytest.fixture
    def integration_service(self, db_session: Session):
        """Create integration service instance."""
        return AgentWorkflowIntegrationService(db_session)
    
    @pytest.fixture
    def sample_agent(self, db_session: Session, test_user):
        """Create a sample agent for testing."""
        agent = Agent(
            user_id=test_user.id,
            name="Test Agent",
            description="A test agent",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1",
            configuration={"temperature": 0.7}
        )
        db_session.add(agent)
        db_session.commit()
        return agent
    
    @pytest.fixture
    def sample_block(self, db_session: Session, test_user):
        """Create a sample block for testing."""
        block = Block(
            user_id=test_user.id,
            name="Test Block",
            description="A test block",
            block_type="llm",
            input_schema={"type": "object", "properties": {"input": {"type": "string"}}},
            output_schema={"type": "object", "properties": {"output": {"type": "string"}}},
            configuration={"model": "llama3.1"}
        )
        db_session.add(block)
        db_session.commit()
        return block
    
    def test_create_agentflow_with_agents(
        self, 
        integration_service: AgentWorkflowIntegrationService,
        sample_agent: Agent,
        test_user
    ):
        """Test creating an Agentflow with associated agents."""
        agentflow_data = {
            "name": "Test Agentflow",
            "description": "A test agentflow",
            "orchestration_type": "sequential",
            "supervisor_config": {"enabled": True},
            "tags": ["test", "integration"]
        }
        
        agents_config = [
            {
                "agent_id": str(sample_agent.id),
                "name": "Primary Agent",
                "role": "worker",
                "description": "Main processing agent",
                "capabilities": ["text_processing", "analysis"],
                "priority": 1,
                "max_retries": 3,
                "timeout_seconds": 60,
                "dependencies": [],
                "create_block": True,
                "position_x": 100,
                "position_y": 200
            }
        ]
        
        # Create agentflow with agents
        agentflow = integration_service.create_agentflow_with_agents(
            user_id=str(test_user.id),
            agentflow_data=agentflow_data,
            agents_config=agents_config
        )
        
        # Verify agentflow creation
        assert agentflow.name == "Test Agentflow"
        assert agentflow.orchestration_type == "sequential"
        assert agentflow.supervisor_config["enabled"] is True
        assert "test" in agentflow.tags
        
        # Verify agent association
        assert len(agentflow.agents) == 1
        agentflow_agent = agentflow.agents[0]
        assert agentflow_agent.name == "Primary Agent"
        assert agentflow_agent.role == "worker"
        assert agentflow_agent.agent_id == sample_agent.id
        assert agentflow_agent.capabilities == ["text_processing", "analysis"]
        assert agentflow_agent.position_x == 100
        assert agentflow_agent.position_y == 200
        
        # Verify block creation
        assert agentflow_agent.block_id is not None
        
        # Verify graph definition update
        assert "nodes" in agentflow.graph_definition
        assert "edges" in agentflow.graph_definition
        assert len(agentflow.graph_definition["nodes"]) == 1
        
        node = agentflow.graph_definition["nodes"][0]
        assert node["type"] == "agent"
        assert node["data"]["name"] == "Primary Agent"
        assert node["position"]["x"] == 100
        assert node["position"]["y"] == 200
    
    def test_create_agentflow_with_edges(
        self,
        integration_service: AgentWorkflowIntegrationService,
        db_session: Session,
        test_user
    ):
        """Test creating an Agentflow with agent connections."""
        # Create two agents
        agent1 = Agent(
            user_id=test_user.id,
            name="Agent 1",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1"
        )
        agent2 = Agent(
            user_id=test_user.id,
            name="Agent 2",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1"
        )
        db_session.add_all([agent1, agent2])
        db_session.commit()
        
        agentflow_data = {
            "name": "Connected Agentflow",
            "orchestration_type": "sequential"
        }
        
        agents_config = [
            {
                "agent_id": str(agent1.id),
                "name": "First Agent",
                "role": "processor",
                "priority": 1
            },
            {
                "agent_id": str(agent2.id),
                "name": "Second Agent",
                "role": "reviewer",
                "priority": 2,
                "dependencies": ["First Agent"]
            }
        ]
        
        edges_config = [
            {
                "source": "First Agent",
                "target": "Second Agent",
                "edge_type": "data_flow",
                "data_mapping": {"output": "input"},
                "label": "Process Result"
            }
        ]
        
        # Create agentflow with edges
        agentflow = integration_service.create_agentflow_with_agents(
            user_id=str(test_user.id),
            agentflow_data=agentflow_data,
            agents_config=agents_config,
            edges_config=edges_config
        )
        
        # Verify edge creation
        edges = db_session.query(AgentflowEdge).filter(
            AgentflowEdge.agentflow_id == agentflow.id
        ).all()
        
        assert len(edges) == 1
        edge = edges[0]
        assert edge.edge_type == "data_flow"
        assert edge.data_mapping == {"output": "input"}
        assert edge.label == "Process Result"
        
        # Verify graph definition includes edges
        assert len(agentflow.graph_definition["edges"]) >= 1
    
    def test_get_execution_plan_sequential(
        self,
        integration_service: AgentWorkflowIntegrationService,
        sample_agent: Agent,
        test_user
    ):
        """Test getting execution plan for sequential orchestration."""
        agentflow_data = {
            "name": "Sequential Flow",
            "orchestration_type": "sequential"
        }
        
        agents_config = [
            {
                "agent_id": str(sample_agent.id),
                "name": "Agent 1",
                "role": "processor",
                "priority": 1
            }
        ]
        
        agentflow = integration_service.create_agentflow_with_agents(
            user_id=str(test_user.id),
            agentflow_data=agentflow_data,
            agents_config=agents_config
        )
        
        # Get execution plan
        plan = integration_service.get_agentflow_execution_plan(str(agentflow.id))
        
        assert plan["orchestration_type"] == "sequential"
        assert plan["total_agents"] == 1
        assert len(plan["execution_plan"]) == 1
        
        step = plan["execution_plan"][0]
        assert step["step"] == 1
        assert step["name"] == "Agent 1"
        assert step["execution_type"] == "sequential"
    
    def test_get_execution_plan_parallel(
        self,
        integration_service: AgentWorkflowIntegrationService,
        db_session: Session,
        test_user
    ):
        """Test getting execution plan for parallel orchestration."""
        # Create multiple agents
        agents = []
        for i in range(3):
            agent = Agent(
                user_id=test_user.id,
                name=f"Agent {i+1}",
                agent_type="custom",
                llm_provider="ollama",
                llm_model="llama3.1"
            )
            agents.append(agent)
        
        db_session.add_all(agents)
        db_session.commit()
        
        agentflow_data = {
            "name": "Parallel Flow",
            "orchestration_type": "parallel"
        }
        
        agents_config = [
            {
                "agent_id": str(agents[0].id),
                "name": "Agent 1",
                "role": "processor",
                "parallel_group": "group_a"
            },
            {
                "agent_id": str(agents[1].id),
                "name": "Agent 2",
                "role": "processor",
                "parallel_group": "group_a"
            },
            {
                "agent_id": str(agents[2].id),
                "name": "Agent 3",
                "role": "reviewer",
                "parallel_group": "group_b"
            }
        ]
        
        agentflow = integration_service.create_agentflow_with_agents(
            user_id=str(test_user.id),
            agentflow_data=agentflow_data,
            agents_config=agents_config
        )
        
        # Get execution plan
        plan = integration_service.get_agentflow_execution_plan(str(agentflow.id))
        
        assert plan["orchestration_type"] == "parallel"
        assert plan["total_agents"] == 3
        assert len(plan["execution_plan"]) == 2  # Two parallel groups
        
        # Verify parallel groups
        for step in plan["execution_plan"]:
            assert step["execution_type"] == "parallel"
            assert "parallel_group" in step
            assert "agents" in step
    
    def test_validate_agentflow_integrity_valid(
        self,
        integration_service: AgentWorkflowIntegrationService,
        sample_agent: Agent,
        test_user
    ):
        """Test validation of a valid agentflow."""
        agentflow_data = {
            "name": "Valid Flow",
            "orchestration_type": "sequential",
            "supervisor_config": {"enabled": True, "llm_provider": "ollama"}
        }
        
        agents_config = [
            {
                "agent_id": str(sample_agent.id),
                "name": "Valid Agent",
                "role": "processor"
            }
        ]
        
        agentflow = integration_service.create_agentflow_with_agents(
            user_id=str(test_user.id),
            agentflow_data=agentflow_data,
            agents_config=agents_config
        )
        
        # Validate integrity
        report = integration_service.validate_agentflow_integrity(str(agentflow.id))
        
        assert report["validation_status"] == "valid"
        assert len(report["issues"]) == 0
        assert report["agent_count"] == 1
        assert report["orchestration_type"] == "sequential"
    
    def test_validate_agentflow_integrity_with_issues(
        self,
        integration_service: AgentWorkflowIntegrationService,
        db_session: Session,
        test_user
    ):
        """Test validation of an agentflow with issues."""
        # Create agentflow with missing agent reference
        agentflow = Agentflow(
            user_id=test_user.id,
            name="Invalid Flow",
            orchestration_type="sequential",
            graph_definition={}
        )
        db_session.add(agentflow)
        db_session.flush()
        
        # Create agentflow agent with non-existent agent_id
        fake_agent_id = uuid.uuid4()
        agentflow_agent = AgentflowAgent(
            agentflow_id=agentflow.id,
            agent_id=fake_agent_id,
            name="Missing Agent",
            role="processor"
        )
        db_session.add(agentflow_agent)
        db_session.commit()
        
        # Validate integrity
        report = integration_service.validate_agentflow_integrity(str(agentflow.id))
        
        assert report["validation_status"] == "invalid"
        assert len(report["issues"]) > 0
        assert any("non-existent agent" in issue for issue in report["issues"])
    
    def test_validate_circular_dependencies(
        self,
        integration_service: AgentWorkflowIntegrationService,
        db_session: Session,
        test_user
    ):
        """Test detection of circular dependencies."""
        # Create agents
        agent1 = Agent(
            user_id=test_user.id,
            name="Agent 1",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1"
        )
        agent2 = Agent(
            user_id=test_user.id,
            name="Agent 2",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1"
        )
        db_session.add_all([agent1, agent2])
        db_session.commit()
        
        agentflow_data = {
            "name": "Circular Flow",
            "orchestration_type": "sequential"
        }
        
        # Create circular dependency: Agent 1 depends on Agent 2, Agent 2 depends on Agent 1
        agents_config = [
            {
                "agent_id": str(agent1.id),
                "name": "Agent 1",
                "role": "processor",
                "dependencies": ["Agent 2"]
            },
            {
                "agent_id": str(agent2.id),
                "name": "Agent 2",
                "role": "processor",
                "dependencies": ["Agent 1"]
            }
        ]
        
        agentflow = integration_service.create_agentflow_with_agents(
            user_id=str(test_user.id),
            agentflow_data=agentflow_data,
            agents_config=agents_config
        )
        
        # Validate integrity
        report = integration_service.validate_agentflow_integrity(str(agentflow.id))
        
        assert report["validation_status"] == "invalid"
        assert any("Circular dependency" in issue for issue in report["issues"])
    
    def test_nonexistent_agentflow_validation(
        self,
        integration_service: AgentWorkflowIntegrationService
    ):
        """Test validation of non-existent agentflow."""
        fake_id = str(uuid.uuid4())
        
        with pytest.raises(NotFoundError):
            integration_service.validate_agentflow_integrity(fake_id)
    
    def test_nonexistent_agentflow_execution_plan(
        self,
        integration_service: AgentWorkflowIntegrationService
    ):
        """Test execution plan for non-existent agentflow."""
        fake_id = str(uuid.uuid4())
        
        with pytest.raises(NotFoundError):
            integration_service.get_agentflow_execution_plan(fake_id)