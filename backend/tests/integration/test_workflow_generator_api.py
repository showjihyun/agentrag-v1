"""
Integration tests for Workflow Generator API
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from backend.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    # In real tests, you'd generate a valid JWT token
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def mock_workflow_response():
    """Mock workflow generation response"""
    return {
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
                "id": "end-1",
                "type": "end",
                "position": {"x": 100, "y": 300},
                "data": {"label": "End"}
            }
        ],
        "edges": [
            {
                "id": "e1",
                "source": "start-1",
                "target": "end-1",
                "type": "custom"
            }
        ],
        "metadata": {
            "generated_from": "Test description",
            "user_id": "test-user",
            "generator_version": "1.0.0"
        }
    }


class TestWorkflowGeneratorAPI:
    """Test Workflow Generator API endpoints"""
    
    def test_generate_workflow_endpoint_exists(self, client):
        """Test that the generate endpoint exists"""
        response = client.post(
            "/api/workflow-generator/generate",
            json={"description": "Test"}
        )
        # Should not be 404
        assert response.status_code != 404
    
    @pytest.mark.skip(reason="Requires authentication setup")
    def test_generate_workflow_success(self, client, auth_headers, mock_workflow_response):
        """Test successful workflow generation"""
        with patch('backend.services.agent_builder.workflow_generator.WorkflowGenerator.generate_workflow',
                  new_callable=AsyncMock, return_value=mock_workflow_response):
            response = client.post(
                "/api/workflow-generator/generate",
                headers=auth_headers,
                json={
                    "description": "Send a Slack notification when webhook is triggered"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "workflow" in data
            assert "suggestions" in data
            assert data["workflow"]["name"] == "Test Workflow"
            assert len(data["workflow"]["nodes"]) >= 2
    
    @pytest.mark.skip(reason="Requires authentication setup")
    def test_generate_workflow_empty_description(self, client, auth_headers):
        """Test generation with empty description"""
        response = client.post(
            "/api/workflow-generator/generate",
            headers=auth_headers,
            json={"description": ""}
        )
        
        # Should still work but might generate a basic workflow
        assert response.status_code in [200, 400]
    
    @pytest.mark.skip(reason="Requires authentication setup")
    def test_generate_workflow_with_context(self, client, auth_headers, mock_workflow_response):
        """Test generation with additional context"""
        with patch('backend.services.agent_builder.workflow_generator.WorkflowGenerator.generate_workflow',
                  new_callable=AsyncMock, return_value=mock_workflow_response):
            response = client.post(
                "/api/workflow-generator/generate",
                headers=auth_headers,
                json={
                    "description": "Send email notification",
                    "additional_context": {
                        "preferred_email": "test@example.com"
                    }
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "workflow" in data
    
    def test_get_examples_endpoint(self, client):
        """Test getting example descriptions"""
        response = client.get("/api/workflow-generator/examples")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "examples" in data
        assert len(data["examples"]) > 0
        
        # Check example structure
        example = data["examples"][0]
        assert "title" in example
        assert "description" in example
        assert "category" in example
        assert "complexity" in example
    
    def test_get_node_types_endpoint(self, client):
        """Test getting available node types"""
        response = client.get("/api/workflow-generator/node-types")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "node_types" in data
        assert len(data["node_types"]) > 20
        
        # Check node type structure
        node_type = data["node_types"][0]
        assert "type" in node_type
        assert "description" in node_type
        
        # Check for essential node types
        types = [nt["type"] for nt in data["node_types"]]
        assert "start" in types
        assert "end" in types
        assert "agent" in types
        assert "slack" in types
    
    @pytest.mark.skip(reason="Requires authentication setup")
    def test_suggest_improvements_endpoint(self, client, auth_headers):
        """Test suggesting improvements"""
        workflow = {
            "nodes": [
                {"type": "start"},
                {"type": "http_request"},
                {"type": "end"}
            ],
            "edges": []
        }
        
        response = client.post(
            "/api/workflow-generator/suggest-improvements",
            headers=auth_headers,
            json={"workflow": workflow}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
    
    @pytest.mark.skip(reason="Requires authentication setup")
    def test_optimize_workflow_endpoint(self, client, auth_headers):
        """Test workflow optimization"""
        workflow = {
            "nodes": [
                {"type": "start"},
                {"type": "agent"},
                {"type": "end"}
            ],
            "edges": []
        }
        
        response = client.post(
            "/api/workflow-generator/optimize",
            headers=auth_headers,
            json={"workflow": workflow}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "workflow" in data
        assert "improvements" in data
        assert isinstance(data["improvements"], list)


class TestWorkflowGeneratorScenarios:
    """Test real-world scenarios"""
    
    @pytest.mark.skip(reason="Requires authentication and LLM setup")
    def test_scenario_slack_notification(self, client, auth_headers):
        """Test: Generate Slack notification workflow"""
        response = client.post(
            "/api/workflow-generator/generate",
            headers=auth_headers,
            json={
                "description": "Webhook이 트리거되면 #alerts 채널에 Slack 메시지 전송"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        workflow = data["workflow"]
        node_types = [n["type"] for n in workflow["nodes"]]
        
        # Should have webhook trigger and slack nodes
        assert "webhook_trigger" in node_types or "trigger" in node_types
        assert "slack" in node_types
    
    @pytest.mark.skip(reason="Requires authentication and LLM setup")
    def test_scenario_approval_workflow(self, client, auth_headers):
        """Test: Generate approval workflow"""
        response = client.post(
            "/api/workflow-generator/generate",
            headers=auth_headers,
            json={
                "description": "구매 요청이 들어오면 금액이 $1000 이상이면 관리자 승인 필요"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        workflow = data["workflow"]
        node_types = [n["type"] for n in workflow["nodes"]]
        
        # Should have condition and approval nodes
        assert "condition" in node_types or "switch" in node_types
        assert "human_approval" in node_types
    
    @pytest.mark.skip(reason="Requires authentication and LLM setup")
    def test_scenario_document_analysis(self, client, auth_headers):
        """Test: Generate document analysis workflow"""
        response = client.post(
            "/api/workflow-generator/generate",
            headers=auth_headers,
            json={
                "description": "PDF를 업로드하면 텍스트를 추출하고 AI로 요약해서 이메일 전송"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        workflow = data["workflow"]
        node_types = [n["type"] for n in workflow["nodes"]]
        
        # Should have agent and email nodes
        assert "agent" in node_types
        assert "email" in node_types


class TestWorkflowGeneratorValidation:
    """Test input validation"""
    
    def test_generate_missing_description(self, client):
        """Test generation without description"""
        response = client.post(
            "/api/workflow-generator/generate",
            json={}
        )
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_suggest_improvements_missing_workflow(self, client):
        """Test suggestions without workflow"""
        response = client.post(
            "/api/workflow-generator/suggest-improvements",
            json={}
        )
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_optimize_missing_workflow(self, client):
        """Test optimization without workflow"""
        response = client.post(
            "/api/workflow-generator/optimize",
            json={}
        )
        
        # Should return validation error
        assert response.status_code == 422


class TestWorkflowGeneratorPerformance:
    """Test performance characteristics"""
    
    @pytest.mark.skip(reason="Performance test - run manually")
    @pytest.mark.asyncio
    async def test_generation_time(self, client, auth_headers):
        """Test that generation completes in reasonable time"""
        import time
        
        start = time.time()
        
        response = client.post(
            "/api/workflow-generator/generate",
            headers=auth_headers,
            json={"description": "Send Slack notification"}
        )
        
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 10.0  # Should complete in under 10 seconds
    
    @pytest.mark.skip(reason="Load test - run manually")
    def test_concurrent_generations(self, client, auth_headers):
        """Test handling multiple concurrent requests"""
        import concurrent.futures
        
        def generate():
            return client.post(
                "/api/workflow-generator/generate",
                headers=auth_headers,
                json={"description": "Test workflow"}
            )
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(generate) for _ in range(5)]
            results = [f.result() for f in futures]
        
        # All should succeed
        assert all(r.status_code == 200 for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
