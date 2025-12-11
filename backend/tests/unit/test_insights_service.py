"""
Unit tests for Insights Service
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from backend.services.agent_builder.insights_service import InsightsService
from backend.db.models.flows import Chatflow, Agentflow, FlowExecution


class TestInsightsService:
    """Test insights service"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        db = Mock()
        return db
    
    @pytest.fixture
    def service(self, mock_db):
        """Create service instance"""
        return InsightsService(mock_db)
    
    @pytest.fixture
    def sample_executions(self):
        """Create sample execution data"""
        now = datetime.utcnow()
        
        return [
            Mock(
                id=1,
                user_id=1,
                flow_id=1,
                flow_type="chatflow",
                status="completed",
                duration=1000,
                created_at=now - timedelta(days=1),
                error_message=None
            ),
            Mock(
                id=2,
                user_id=1,
                flow_id=1,
                flow_type="chatflow",
                status="completed",
                duration=1500,
                created_at=now - timedelta(days=2),
                error_message=None
            ),
            Mock(
                id=3,
                user_id=1,
                flow_id=2,
                flow_type="agentflow",
                status="failed",
                duration=None,
                created_at=now - timedelta(days=3),
                error_message="Connection timeout"
            ),
            Mock(
                id=4,
                user_id=1,
                flow_id=2,
                flow_type="agentflow",
                status="completed",
                duration=2000,
                created_at=now - timedelta(days=4),
                error_message=None
            )
        ]
    
    @pytest.mark.asyncio
    async def test_get_workflow_stats(self, service, mock_db):
        """Test workflow statistics calculation"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # Mock query results
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 5
        mock_db.query.return_value = mock_query
        
        # Mock most used query
        mock_most_used = Mock()
        mock_most_used.filter.return_value = mock_most_used
        mock_most_used.group_by.return_value = mock_most_used
        mock_most_used.order_by.return_value = mock_most_used
        mock_most_used.limit.return_value = mock_most_used
        mock_most_used.all.return_value = [
            (1, "chatflow", 10),
            (2, "agentflow", 5)
        ]
        
        # Setup query mock to return different mocks
        def query_side_effect(model):
            if hasattr(model, 'flow_id'):  # FlowExecution query
                return mock_most_used
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        stats = await service._get_workflow_stats(user_id=1, cutoff_date=cutoff_date)
        
        assert "total_chatflows" in stats
        assert "total_agentflows" in stats
        assert "total_workflows" in stats
        assert "most_used" in stats
    
    @pytest.mark.asyncio
    async def test_get_execution_stats(self, service, mock_db):
        """Test execution statistics calculation"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # Mock total count
        mock_total = Mock()
        mock_total.filter.return_value = mock_total
        mock_total.scalar.return_value = 100
        
        # Mock success count
        mock_success = Mock()
        mock_success.filter.return_value = mock_success
        mock_success.scalar.return_value = 80
        
        # Mock failed count
        mock_failed = Mock()
        mock_failed.filter.return_value = mock_failed
        mock_failed.scalar.return_value = 20
        
        # Mock daily executions
        mock_daily = Mock()
        mock_daily.filter.return_value = mock_daily
        mock_daily.group_by.return_value = mock_daily
        mock_daily.order_by.return_value = mock_daily
        mock_daily.all.return_value = [
            (datetime.utcnow().date(), 10),
            ((datetime.utcnow() - timedelta(days=1)).date(), 15)
        ]
        
        call_count = [0]
        
        def query_side_effect(*args):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_total
            elif call_count[0] == 2:
                return mock_success
            elif call_count[0] == 3:
                return mock_failed
            else:
                return mock_daily
        
        mock_db.query.side_effect = query_side_effect
        
        stats = await service._get_execution_stats(user_id=1, cutoff_date=cutoff_date)
        
        assert stats["total_executions"] == 100
        assert stats["successful"] == 80
        assert stats["failed"] == 20
        assert stats["success_rate"] == 80.0
        assert "daily_executions" in stats
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, service, mock_db, sample_executions):
        """Test performance metrics calculation"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # Filter to completed executions with duration
        completed = [e for e in sample_executions if e.status == "completed" and e.duration]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = completed
        mock_db.query.return_value = mock_query
        
        metrics = await service._get_performance_metrics(user_id=1, cutoff_date=cutoff_date)
        
        assert "avg_duration_ms" in metrics
        assert "min_duration_ms" in metrics
        assert "max_duration_ms" in metrics
        assert "by_type" in metrics
        
        # Check calculations
        durations = [e.duration for e in completed]
        assert metrics["avg_duration_ms"] == round(sum(durations) / len(durations), 2)
        assert metrics["min_duration_ms"] == min(durations)
        assert metrics["max_duration_ms"] == max(durations)
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics_no_data(self, service, mock_db):
        """Test performance metrics with no data"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        
        metrics = await service._get_performance_metrics(user_id=1, cutoff_date=cutoff_date)
        
        assert metrics["avg_duration_ms"] == 0
        assert metrics["min_duration_ms"] == 0
        assert metrics["max_duration_ms"] == 0
        assert metrics["by_type"] == {}
    
    @pytest.mark.asyncio
    async def test_get_usage_patterns(self, service, mock_db, sample_executions):
        """Test usage pattern analysis"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_executions
        mock_db.query.return_value = mock_query
        
        patterns = await service._get_usage_patterns(user_id=1, cutoff_date=cutoff_date)
        
        assert "peak_hours" in patterns
        assert "peak_days" in patterns
        assert "most_active_day" in patterns
        
        # Check structure
        if patterns["peak_hours"]:
            assert all("hour" in p and "count" in p for p in patterns["peak_hours"])
        if patterns["peak_days"]:
            assert all("day" in p and "count" in p for p in patterns["peak_days"])
    
    @pytest.mark.asyncio
    async def test_generate_recommendations_new_user(self, service):
        """Test recommendations for new user"""
        
        workflow_stats = {
            "total_workflows": 0,
            "total_chatflows": 0,
            "total_agentflows": 0
        }
        
        execution_stats = {
            "total_executions": 0,
            "success_rate": 0
        }
        
        performance = {
            "avg_duration_ms": 0
        }
        
        recommendations = await service._generate_recommendations(
            user_id=1,
            workflow_stats=workflow_stats,
            execution_stats=execution_stats,
            performance=performance
        )
        
        assert len(recommendations) > 0
        assert any(r["type"] == "getting_started" for r in recommendations)
    
    @pytest.mark.asyncio
    async def test_generate_recommendations_low_success_rate(self, service):
        """Test recommendations for low success rate"""
        
        workflow_stats = {
            "total_workflows": 5,
            "total_chatflows": 3,
            "total_agentflows": 2
        }
        
        execution_stats = {
            "total_executions": 50,
            "success_rate": 60.0  # Low success rate
        }
        
        performance = {
            "avg_duration_ms": 2000
        }
        
        recommendations = await service._generate_recommendations(
            user_id=1,
            workflow_stats=workflow_stats,
            execution_stats=execution_stats,
            performance=performance
        )
        
        assert any(r["type"] == "reliability" for r in recommendations)
    
    @pytest.mark.asyncio
    async def test_generate_recommendations_slow_performance(self, service):
        """Test recommendations for slow performance"""
        
        workflow_stats = {
            "total_workflows": 5,
            "total_chatflows": 3,
            "total_agentflows": 2
        }
        
        execution_stats = {
            "total_executions": 50,
            "success_rate": 95.0
        }
        
        performance = {
            "avg_duration_ms": 8000  # Slow
        }
        
        recommendations = await service._generate_recommendations(
            user_id=1,
            workflow_stats=workflow_stats,
            execution_stats=execution_stats,
            performance=performance
        )
        
        assert any(r["type"] == "performance" for r in recommendations)
    
    @pytest.mark.asyncio
    async def test_get_workflow_insights(self, service, mock_db, sample_executions):
        """Test workflow-specific insights"""
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = sample_executions
        mock_db.query.return_value = mock_query
        
        insights = await service.get_workflow_insights(
            flow_id=1,
            flow_type="chatflow",
            user_id=1
        )
        
        assert insights["flow_id"] == 1
        assert insights["flow_type"] == "chatflow"
        assert "total_executions" in insights
        assert "success_rate" in insights
        assert "avg_duration_ms" in insights
        assert "common_errors" in insights
        assert "recent_executions" in insights
    
    @pytest.mark.asyncio
    async def test_get_workflow_insights_no_data(self, service, mock_db):
        """Test workflow insights with no execution history"""
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        
        insights = await service.get_workflow_insights(
            flow_id=1,
            flow_type="chatflow",
            user_id=1
        )
        
        assert "message" in insights
        assert "No execution history" in insights["message"]
    
    @pytest.mark.asyncio
    async def test_get_system_insights(self, service, mock_db):
        """Test system-wide insights"""
        
        # Mock various queries
        mock_query = Mock()
        mock_query.scalar.return_value = 100
        
        mock_templates = Mock()
        mock_templates.group_by.return_value = mock_templates
        mock_templates.order_by.return_value = mock_templates
        mock_templates.limit.return_value = mock_templates
        mock_templates.all.return_value = [
            ("Template 1", 50),
            ("Template 2", 30)
        ]
        
        call_count = [0]
        
        def query_side_effect(*args):
            call_count[0] += 1
            if call_count[0] <= 4:
                return mock_query
            else:
                return mock_templates
        
        mock_db.query.side_effect = query_side_effect
        
        insights = await service.get_system_insights()
        
        assert "total_users" in insights
        assert "total_workflows" in insights
        assert "total_chatflows" in insights
        assert "total_agentflows" in insights
        assert "total_executions" in insights
        assert "popular_templates" in insights
    
    @pytest.mark.asyncio
    async def test_get_user_insights_integration(self, service, mock_db):
        """Test full user insights integration"""
        
        # Mock all sub-methods
        with patch.object(service, '_get_workflow_stats') as mock_workflow, \
             patch.object(service, '_get_execution_stats') as mock_execution, \
             patch.object(service, '_get_performance_metrics') as mock_performance, \
             patch.object(service, '_get_usage_patterns') as mock_patterns, \
             patch.object(service, '_generate_recommendations') as mock_recommendations:
            
            mock_workflow.return_value = {"total_workflows": 5}
            mock_execution.return_value = {"total_executions": 50}
            mock_performance.return_value = {"avg_duration_ms": 2000}
            mock_patterns.return_value = {"peak_hours": []}
            mock_recommendations.return_value = []
            
            insights = await service.get_user_insights(user_id=1, time_range=30)
            
            assert insights["user_id"] == 1
            assert insights["time_range_days"] == 30
            assert "workflows" in insights
            assert "executions" in insights
            assert "performance" in insights
            assert "patterns" in insights
            assert "recommendations" in insights
            
            # Verify all methods were called
            mock_workflow.assert_called_once()
            mock_execution.assert_called_once()
            mock_performance.assert_called_once()
            mock_patterns.assert_called_once()
            mock_recommendations.assert_called_once()
