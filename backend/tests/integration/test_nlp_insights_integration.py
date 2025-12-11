"""
Integration tests for NLP Generator and Insights
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from backend.main import app
from backend.db.models.flows import Chatflow, Agentflow, FlowExecution
from backend.tests.fixtures.user import test_user, auth_headers
from backend.tests.fixtures.database import test_db


class TestNLPGeneratorIntegration:
    """Integration tests for NLP Generator API"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_generate_workflow_endpoint(self, client, auth_headers):
        """Test workflow generation endpoint"""
        
        response = client.post(
            "/api/agent-builder/nlp/generate",
            json={
                "description": "Create a chatbot that answers questions about products"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "workflow" in data
        assert "suggestions" in data
        
        workflow = data["workflow"]
        assert workflow["workflow_type"] in ["chatflow", "agentflow"]
        assert len(workflow["nodes"]) >= 3
        assert len(workflow["edges"]) >= 2
        assert 0 <= workflow["confidence"] <= 1
    
    def test_generate_workflow_with_type_override(self, client, auth_headers):
        """Test workflow generation with type override"""
        
        response = client.post(
            "/api/agent-builder/nlp/generate",
            json={
                "description": "Process data from API",
                "workflow_type": "agentflow"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["workflow"]["workflow_type"] == "agentflow"
    
    def test_generate_workflow_invalid_description(self, client, auth_headers):
        """Test workflow generation with invalid description"""
        
        response = client.post(
            "/api/agent-builder/nlp/generate",
            json={
                "description": "short"  # Too short
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_examples_endpoint(self, client):
        """Test get examples endpoint"""
        
        response = client.get("/api/agent-builder/nlp/examples")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "examples" in data
        assert len(data["examples"]) > 0
        
        for example in data["examples"]:
            assert "prompt" in example
            assert "workflow_type" in example
            assert "description" in example
    
    def test_suggest_improvements_endpoint(self, client, auth_headers):
        """Test improvement suggestions endpoint"""
        
        workflow = {
            "nodes": [
                {"id": "1", "type": "start", "data": {}},
                {"id": "2", "type": "llm", "data": {}},
                {"id": "3", "type": "end", "data": {}}
            ],
            "edges": []
        }
        
        response = client.post(
            "/api/agent-builder/nlp/improve",
            json={"workflow": workflow},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        suggestions = response.json()
        
        assert isinstance(suggestions, list)
    
    def test_refine_workflow_endpoint(self, client, auth_headers):
        """Test workflow refinement endpoint"""
        
        workflow = {
            "nodes": [
                {"id": "1", "type": "start", "data": {}},
                {"id": "2", "type": "llm", "data": {}},
                {"id": "3", "type": "end", "data": {}}
            ]
        }
        
        response = client.post(
            "/api/agent-builder/nlp/refine",
            json={
                "workflow": workflow,
                "refinement": "Add error handling"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "workflow" in data
        assert "suggestions" in data


class TestInsightsIntegration:
    """Integration tests for Insights API"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_data(self, test_db, test_user):
        """Create sample data for testing"""
        
        # Create chatflows
        chatflow1 = Chatflow(
            name="Test Chatflow 1",
            user_id=test_user.id,
            flow_data={"nodes": [], "edges": []},
            created_at=datetime.utcnow() - timedelta(days=5)
        )
        chatflow2 = Chatflow(
            name="Test Chatflow 2",
            user_id=test_user.id,
            flow_data={"nodes": [], "edges": []},
            created_at=datetime.utcnow() - timedelta(days=10)
        )
        
        test_db.add_all([chatflow1, chatflow2])
        test_db.commit()
        
        # Create executions
        for i in range(10):
            execution = FlowExecution(
                flow_id=chatflow1.id,
                flow_type="chatflow",
                user_id=test_user.id,
                status="completed" if i < 8 else "failed",
                duration=1000 + i * 100,
                created_at=datetime.utcnow() - timedelta(days=i),
                error_message="Test error" if i >= 8 else None
            )
            test_db.add(execution)
        
        test_db.commit()
        
        return {
            "chatflows": [chatflow1, chatflow2],
            "execution_count": 10
        }
    
    def test_get_user_insights_endpoint(self, client, auth_headers, sample_data):
        """Test user insights endpoint"""
        
        response = client.get(
            "/api/agent-builder/insights/user?time_range=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "user_id" in data
        assert "time_range_days" in data
        assert "workflows" in data
        assert "executions" in data
        assert "performance" in data
        assert "patterns" in data
        assert "recommendations" in data
        
        # Check workflow stats
        assert data["workflows"]["total_workflows"] >= 2
        
        # Check execution stats
        assert data["executions"]["total_executions"] >= 10
    
    def test_get_user_insights_custom_range(self, client, auth_headers, sample_data):
        """Test user insights with custom time range"""
        
        response = client.get(
            "/api/agent-builder/insights/user?time_range=7",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["time_range_days"] == 7
    
    def test_get_workflow_insights_endpoint(self, client, auth_headers, sample_data):
        """Test workflow-specific insights endpoint"""
        
        chatflow = sample_data["chatflows"][0]
        
        response = client.get(
            f"/api/agent-builder/insights/workflow/chatflow/{chatflow.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["flow_id"] == chatflow.id
        assert data["flow_type"] == "chatflow"
        assert "total_executions" in data
        assert "success_rate" in data
        assert "avg_duration_ms" in data
        assert "common_errors" in data
        assert "recent_executions" in data
    
    def test_get_workflow_insights_invalid_type(self, client, auth_headers):
        """Test workflow insights with invalid type"""
        
        response = client.get(
            "/api/agent-builder/insights/workflow/invalid_type/1",
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_recommendations_endpoint(self, client, auth_headers, sample_data):
        """Test recommendations endpoint"""
        
        response = client.get(
            "/api/agent-builder/insights/recommendations",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        recommendations = response.json()
        
        assert isinstance(recommendations, list)
        
        if recommendations:
            for rec in recommendations:
                assert "type" in rec
                assert "priority" in rec
                assert "message" in rec
                assert "action" in rec
    
    def test_export_insights_json(self, client, auth_headers, sample_data):
        """Test insights export in JSON format"""
        
        response = client.get(
            "/api/agent-builder/insights/export?format=json&time_range=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "workflows" in data
        assert "executions" in data
    
    def test_export_insights_csv(self, client, auth_headers, sample_data):
        """Test insights export in CSV format"""
        
        response = client.get(
            "/api/agent-builder/insights/export?format=csv&time_range=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        
        # Check CSV content
        content = response.text
        assert "Metric,Value" in content
        assert "Total Workflows" in content
    
    def test_get_system_insights_unauthorized(self, client, auth_headers):
        """Test system insights without admin access"""
        
        response = client.get(
            "/api/agent-builder/insights/system",
            headers=auth_headers
        )
        
        # Should fail if user is not admin
        assert response.status_code in [403, 500]
    
    def test_insights_performance(self, client, auth_headers, sample_data):
        """Test insights endpoint performance"""
        
        import time
        
        start = time.time()
        response = client.get(
            "/api/agent-builder/insights/user?time_range=30",
            headers=auth_headers
        )
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 2.0  # Should complete within 2 seconds


class TestNLPInsightsCombined:
    """Test combined NLP and Insights functionality"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_generate_and_analyze_workflow(self, client, auth_headers):
        """Test generating a workflow and analyzing it"""
        
        # Generate workflow
        gen_response = client.post(
            "/api/agent-builder/nlp/generate",
            json={
                "description": "Create a workflow that processes customer feedback"
            },
            headers=auth_headers
        )
        
        assert gen_response.status_code == 200
        workflow = gen_response.json()["workflow"]
        
        # Get improvement suggestions
        improve_response = client.post(
            "/api/agent-builder/nlp/improve",
            json={"workflow": workflow},
            headers=auth_headers
        )
        
        assert improve_response.status_code == 200
        suggestions = improve_response.json()
        
        assert isinstance(suggestions, list)
    
    def test_workflow_lifecycle_insights(self, client, auth_headers, test_db, test_user):
        """Test insights throughout workflow lifecycle"""
        
        # Create workflow
        chatflow = Chatflow(
            name="Lifecycle Test",
            user_id=test_user.id,
            flow_data={"nodes": [], "edges": []}
        )
        test_db.add(chatflow)
        test_db.commit()
        
        # Add some executions
        for i in range(5):
            execution = FlowExecution(
                flow_id=chatflow.id,
                flow_type="chatflow",
                user_id=test_user.id,
                status="completed",
                duration=1000 + i * 100,
                created_at=datetime.utcnow() - timedelta(hours=i)
            )
            test_db.add(execution)
        
        test_db.commit()
        
        # Get insights
        insights_response = client.get(
            f"/api/agent-builder/insights/workflow/chatflow/{chatflow.id}",
            headers=auth_headers
        )
        
        assert insights_response.status_code == 200
        insights = insights_response.json()
        
        assert insights["total_executions"] == 5
        assert insights["success_rate"] == 100.0
