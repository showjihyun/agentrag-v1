"""
Unit tests for Workflow Generator Service
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from backend.services.agent_builder.workflow_generator import WorkflowGenerator


@pytest.fixture
def generator():
    """Create WorkflowGenerator instance"""
    return WorkflowGenerator()


@pytest.fixture
def mock_llm_response():
    """Mock LLM response with valid workflow"""
    return json.dumps({
        "name": "Test Workflow",
        "description": "A test workflow",
        "nodes": [
            {
                "id": "start-1",
                "type": "start",
                "position": {"x": 100, "y": 100},
                "data": {"label": "Start"}
            },
            {
                "id": "slack-1",
                "type": "slack",
                "position": {"x": 100, "y": 300},
                "data": {"label": "Send Slack Message", "channel": "#alerts"}
            },
            {
                "id": "end-1",
                "type": "end",
                "position": {"x": 100, "y": 500},
                "data": {"label": "End"}
            }
        ],
        "edges": [
            {"id": "e1", "source": "start-1", "target": "slack-1", "type": "custom"},
            {"id": "e2", "source": "slack-1", "target": "end-1", "type": "custom"}
        ]
    })


class TestWorkflowGenerator:
    """Test WorkflowGenerator class"""
    
    def test_initialization(self, generator):
        """Test generator initialization"""
        assert generator is not None
        assert len(generator.node_types) > 20
        assert "start" in generator.node_types
        assert "agent" in generator.node_types
        assert "slack" in generator.node_types
    
    def test_node_types_coverage(self, generator):
        """Test that all major node types are included"""
        expected_types = [
            "start", "end", "agent", "block", "condition",
            "switch", "loop", "parallel", "delay", "merge",
            "http_request", "code", "slack", "discord", "email",
            "google_drive", "s3", "database", "memory",
            "human_approval", "consensus", "manager_agent"
        ]
        
        for node_type in expected_types:
            assert node_type in generator.node_types, f"Missing node type: {node_type}"
    
    @pytest.mark.asyncio
    async def test_generate_workflow_simple(self, generator, mock_llm_response):
        """Test simple workflow generation"""
        with patch.object(generator.llm_manager, 'generate_completion', 
                         new_callable=AsyncMock,
                         return_value=mock_llm_response):
            result = await generator.generate_workflow(
                description="Send a Slack notification",
                user_id="test-user-123"
            )
            
            assert result is not None
            assert "name" in result
            assert "nodes" in result
            assert "edges" in result
            assert len(result["nodes"]) >= 2  # At least start and end
            assert "metadata" in result
            assert result["metadata"]["user_id"] == "test-user-123"
    
    @pytest.mark.asyncio
    async def test_generate_workflow_with_context(self, generator, mock_llm_response):
        """Test workflow generation with additional context"""
        with patch.object(generator.llm_manager, 'generate_completion',
                         new_callable=AsyncMock,
                         return_value=mock_llm_response):
            result = await generator.generate_workflow(
                description="Send email notification",
                user_id="test-user-123",
                additional_context={"preferred_email": "test@example.com"}
            )
            
            assert result is not None
            assert "metadata" in result
    
    def test_parse_llm_response_valid_json(self, generator):
        """Test parsing valid JSON response"""
        response = json.dumps({
            "name": "Test",
            "nodes": [],
            "edges": []
        })
        
        result = generator._parse_llm_response(response)
        assert result["name"] == "Test"
        assert "nodes" in result
        assert "edges" in result
    
    def test_parse_llm_response_with_markdown(self, generator):
        """Test parsing JSON wrapped in markdown code blocks"""
        response = """```json
{
  "name": "Test Workflow",
  "nodes": [],
  "edges": []
}
```"""
        
        result = generator._parse_llm_response(response)
        assert result["name"] == "Test Workflow"
    
    def test_parse_llm_response_invalid_json(self, generator):
        """Test parsing invalid JSON (should return fallback)"""
        response = "This is not valid JSON"
        
        result = generator._parse_llm_response(response)
        assert "nodes" in result
        assert len(result["nodes"]) == 2  # Start and End nodes
        assert "error" in result
    
    def test_validate_and_enhance_missing_fields(self, generator):
        """Test validation adds missing required fields"""
        workflow_def = {
            "nodes": [{"type": "start"}],
            "edges": []
        }
        
        result = generator._validate_and_enhance(workflow_def, "Test description")
        
        assert "name" in result
        assert "description" in result
        assert result["description"] == "Test description"
        assert "id" in result["nodes"][0]
        # Should convert to backend format
        assert "node_type" in result["nodes"][0]
        assert "configuration" in result["nodes"][0]
    
    def test_validate_and_enhance_adds_edge_ids(self, generator):
        """Test validation adds IDs to edges"""
        workflow_def = {
            "name": "Test",
            "nodes": [
                {"id": "n1", "type": "start"},
                {"id": "n2", "type": "end"}
            ],
            "edges": [
                {"source": "n1", "target": "n2"}
            ]
        }
        
        result = generator._validate_and_enhance(workflow_def, "Test")
        
        assert "id" in result["edges"][0]
        # Should convert to backend format
        assert "source_node_id" in result["edges"][0]
        assert "target_node_id" in result["edges"][0]
        assert "edge_type" in result["edges"][0]
    
    def test_validate_and_enhance_invalid_node_types(self, generator):
        """Test validation fixes invalid node types"""
        workflow_def = {
            "name": "Test",
            "nodes": [
                {"id": "n1", "type": "invalid_type"}
            ],
            "edges": []
        }
        
        result = generator._validate_and_enhance(workflow_def, "Test")
        
        # Should default to block and convert to backend format
        assert result["nodes"][0]["node_type"] == "block"
    
    def test_auto_layout_simple_chain(self, generator):
        """Test auto-layout for simple chain workflow"""
        workflow_def = {
            "name": "Test",
            "nodes": [
                {"id": "start", "node_type": "start"},
                {"id": "middle", "node_type": "agent"},
                {"id": "end", "node_type": "end"}
            ],
            "edges": [
                {"source_node_id": "start", "target_node_id": "middle"},
                {"source_node_id": "middle", "target_node_id": "end"}
            ]
        }
        
        result = generator._auto_layout_nodes(workflow_def)
        
        # Check that positions are assigned (backend format)
        for node in result["nodes"]:
            assert "position_x" in node
            assert "position_y" in node
        
        # Check vertical ordering (Y coordinates should increase)
        start_node = next(n for n in result["nodes"] if n["id"] == "start")
        middle_node = next(n for n in result["nodes"] if n["id"] == "middle")
        end_node = next(n for n in result["nodes"] if n["id"] == "end")
        
        assert start_node["position_y"] < middle_node["position_y"]
        assert middle_node["position_y"] < end_node["position_y"]
    
    def test_auto_layout_parallel_branches(self, generator):
        """Test auto-layout for parallel branches"""
        workflow_def = {
            "name": "Test",
            "nodes": [
                {"id": "start", "node_type": "start"},
                {"id": "branch1", "node_type": "agent"},
                {"id": "branch2", "node_type": "agent"},
                {"id": "end", "node_type": "end"}
            ],
            "edges": [
                {"source_node_id": "start", "target_node_id": "branch1"},
                {"source_node_id": "start", "target_node_id": "branch2"},
                {"source_node_id": "branch1", "target_node_id": "end"},
                {"source_node_id": "branch2", "target_node_id": "end"}
            ]
        }
        
        result = generator._auto_layout_nodes(workflow_def)
        
        # Parallel branches should have different X coordinates
        branch1 = next(n for n in result["nodes"] if n["id"] == "branch1")
        branch2 = next(n for n in result["nodes"] if n["id"] == "branch2")
        
        assert branch1["position_x"] != branch2["position_x"]
    
    @pytest.mark.asyncio
    async def test_suggest_improvements_no_error_handling(self, generator):
        """Test suggestions for workflow without error handling"""
        workflow_def = {
            "nodes": [
                {"type": "start"},
                {"type": "http_request"},
                {"type": "end"}
            ],
            "edges": []
        }
        
        suggestions = await generator.suggest_improvements(workflow_def)
        
        # Should suggest adding error handling
        assert len(suggestions) > 0
        assert any(s["type"] == "error_handling" for s in suggestions)
    
    @pytest.mark.asyncio
    async def test_suggest_improvements_no_approval(self, generator):
        """Test suggestions for workflow without human approval"""
        workflow_def = {
            "nodes": [
                {"type": "start"},
                {"type": "email"},
                {"type": "end"}
            ],
            "edges": []
        }
        
        suggestions = await generator.suggest_improvements(workflow_def)
        
        # Should suggest adding human approval
        assert any(s["type"] == "approval" for s in suggestions)
    
    @pytest.mark.asyncio
    async def test_suggest_improvements_complete_workflow(self, generator):
        """Test suggestions for complete workflow"""
        workflow_def = {
            "nodes": [
                {"type": "start"},
                {"type": "condition"},  # Has error handling
                {"type": "human_approval"},  # Has approval
                {"type": "email"},
                {"type": "end"}
            ],
            "edges": []
        }
        
        suggestions = await generator.suggest_improvements(workflow_def)
        
        # Should have fewer or no suggestions
        assert len(suggestions) <= 1
    
    def test_build_generation_prompt(self, generator):
        """Test prompt building"""
        prompt = generator._build_generation_prompt(
            "Send a Slack notification",
            None
        )
        
        assert "Send a Slack notification" in prompt
        assert "Available Node Types:" in prompt
        assert "slack" in prompt.lower()
        assert "JSON" in prompt
        assert "Examples:" in prompt
    
    def test_get_example_workflows(self, generator):
        """Test example workflows"""
        examples = generator._get_example_workflows()
        
        assert examples is not None
        assert len(examples) > 0
        
        # Should be valid JSON
        parsed = json.loads(examples)
        assert isinstance(parsed, list)
        assert len(parsed) > 0
        assert "description" in parsed[0]
        assert "workflow" in parsed[0]


class TestWorkflowGeneratorIntegration:
    """Integration tests for workflow generator"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_generate_slack_notification_workflow(self):
        """Test generating a Slack notification workflow"""
        generator = WorkflowGenerator()
        
        # Mock LLM response
        mock_response = json.dumps({
            "name": "Slack Notification",
            "description": "Send Slack notification on webhook",
            "nodes": [
                {"id": "1", "type": "start", "data": {"label": "Start"}},
                {"id": "2", "type": "webhook_trigger", "data": {"label": "Webhook"}},
                {"id": "3", "type": "slack", "data": {"label": "Notify", "channel": "#alerts"}},
                {"id": "4", "type": "end", "data": {"label": "End"}}
            ],
            "edges": [
                {"source": "1", "target": "2"},
                {"source": "2", "target": "3"},
                {"source": "3", "target": "4"}
            ]
        })
        
        with patch.object(generator.llm_manager, 'generate_completion',
                         return_value=mock_response):
            result = await generator.generate_workflow(
                description="Send Slack notification when webhook is triggered",
                user_id="test-user"
            )
            
            assert result["name"] == "Slack Notification"
            assert len(result["nodes"]) == 4
            assert len(result["edges"]) == 3
            
            # Check node types
            node_types = [n["type"] for n in result["nodes"]]
            assert "start" in node_types
            assert "webhook_trigger" in node_types
            assert "slack" in node_types
            assert "end" in node_types
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_generate_approval_workflow(self):
        """Test generating an approval workflow"""
        generator = WorkflowGenerator()
        
        mock_response = json.dumps({
            "name": "Purchase Approval",
            "description": "Approve purchases over $1000",
            "nodes": [
                {"id": "1", "type": "start", "data": {"label": "Start"}},
                {"id": "2", "type": "webhook_trigger", "data": {"label": "Purchase Request"}},
                {"id": "3", "type": "condition", "data": {"label": "Check Amount"}},
                {"id": "4", "type": "human_approval", "data": {"label": "Manager Approval"}},
                {"id": "5", "type": "http_request", "data": {"label": "Process Payment"}},
                {"id": "6", "type": "end", "data": {"label": "End"}}
            ],
            "edges": [
                {"source": "1", "target": "2"},
                {"source": "2", "target": "3"},
                {"source": "3", "target": "4"},
                {"source": "4", "target": "5"},
                {"source": "5", "target": "6"}
            ]
        })
        
        with patch.object(generator.llm_manager, 'generate_completion',
                         return_value=mock_response):
            result = await generator.generate_workflow(
                description="Purchase requests over $1000 need manager approval",
                user_id="test-user"
            )
            
            assert "Purchase" in result["name"]
            
            # Check for approval node
            node_types = [n["type"] for n in result["nodes"]]
            assert "human_approval" in node_types
            assert "condition" in node_types


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
