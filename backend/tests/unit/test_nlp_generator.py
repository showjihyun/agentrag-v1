"""
Unit tests for NLP Workflow Generator
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from backend.services.agent_builder.nlp_generator import (
    NLPWorkflowGenerator,
    WorkflowIntent
)


class TestNLPWorkflowGenerator:
    """Test NLP workflow generation"""
    
    @pytest.fixture
    def generator(self):
        """Create generator instance"""
        return NLPWorkflowGenerator()
    
    @pytest.fixture
    def mock_llm_manager(self):
        """Create mock LLM manager"""
        manager = Mock()
        manager.generate = AsyncMock()
        return manager
    
    @pytest.mark.asyncio
    async def test_simple_intent_parsing(self, generator):
        """Test simple rule-based intent parsing"""
        
        # Test chatflow detection
        result = generator._simple_intent_parsing("Create a chatbot for customer support")
        assert result["workflow_type"] == "chatflow"
        assert "chat" in result["name"].lower() or "customer" in result["name"].lower()
        
        # Test agentflow detection
        result = generator._simple_intent_parsing("Build a workflow to process data")
        assert result["workflow_type"] == "agentflow"
        
        # Test LLM node detection
        result = generator._simple_intent_parsing("Use AI to generate responses")
        assert any(step["type"] == "llm" for step in result["steps"])
        
        # Test HTTP node detection
        result = generator._simple_intent_parsing("Fetch data from an API")
        assert any(step["type"] == "http" for step in result["steps"])
        
        # Test condition node detection
        result = generator._simple_intent_parsing("Check if value is greater than 10")
        assert any(step["type"] == "condition" for step in result["steps"])
        
        # Test code node detection
        result = generator._simple_intent_parsing("Calculate the sum of numbers")
        assert any(step["type"] == "code" for step in result["steps"])
    
    @pytest.mark.asyncio
    async def test_generate_workflow_structure(self, generator):
        """Test workflow structure generation"""
        
        intent = {
            "workflow_type": "chatflow",
            "name": "Test Workflow",
            "description": "Test description",
            "steps": [
                {
                    "type": "llm",
                    "purpose": "Generate response",
                    "inputs": ["prompt"],
                    "outputs": ["response"]
                }
            ],
            "confidence": 0.8
        }
        
        workflow = await generator._generate_workflow_structure(intent)
        
        # Check basic structure
        assert isinstance(workflow, WorkflowIntent)
        assert workflow.workflow_type == "chatflow"
        assert workflow.name == "Test Workflow"
        assert len(workflow.nodes) >= 3  # start + llm + end
        assert len(workflow.edges) >= 2  # connections
        
        # Check start node
        start_nodes = [n for n in workflow.nodes if n["type"] == "start"]
        assert len(start_nodes) == 1
        
        # Check end node
        end_nodes = [n for n in workflow.nodes if n["type"] == "end"]
        assert len(end_nodes) == 1
        
        # Check LLM node
        llm_nodes = [n for n in workflow.nodes if n["type"] == "llm"]
        assert len(llm_nodes) == 1
    
    @pytest.mark.asyncio
    async def test_validate_workflow(self, generator):
        """Test workflow validation"""
        
        # Valid workflow
        valid_workflow = WorkflowIntent(
            workflow_type="chatflow",
            name="Valid",
            description="Valid workflow",
            nodes=[
                {"id": "1", "type": "start", "data": {}},
                {"id": "2", "type": "llm", "data": {}},
                {"id": "3", "type": "end", "data": {}}
            ],
            edges=[
                {"id": "e1", "source": "1", "target": "2"},
                {"id": "e2", "source": "2", "target": "3"}
            ],
            confidence=0.9
        )
        
        result = generator._validate_workflow(valid_workflow)
        assert result.confidence == 0.9  # No penalty
        
        # Missing start node
        invalid_workflow = WorkflowIntent(
            workflow_type="chatflow",
            name="Invalid",
            description="Missing start",
            nodes=[
                {"id": "2", "type": "llm", "data": {}},
                {"id": "3", "type": "end", "data": {}}
            ],
            edges=[
                {"id": "e1", "source": "2", "target": "3"}
            ],
            confidence=0.9
        )
        
        result = generator._validate_workflow(invalid_workflow)
        assert result.confidence < 0.9  # Penalty applied
    
    @pytest.mark.asyncio
    async def test_suggest_improvements(self, generator):
        """Test improvement suggestions"""
        
        # Workflow without error handling
        workflow = {
            "nodes": [
                {"type": "start", "data": {}},
                {"type": "llm", "data": {}},
                {"type": "end", "data": {}}
            ]
        }
        
        suggestions = await generator.suggest_improvements(workflow)
        assert any("error handling" in s.lower() for s in suggestions)
        
        # Workflow with many LLM nodes
        workflow_many_llm = {
            "nodes": [
                {"type": "start", "data": {}},
                {"type": "llm", "data": {}},
                {"type": "llm", "data": {}},
                {"type": "llm", "data": {}},
                {"type": "llm", "data": {}},
                {"type": "end", "data": {}}
            ]
        }
        
        suggestions = await generator.suggest_improvements(workflow_many_llm)
        assert any("combining" in s.lower() or "reduce" in s.lower() for s in suggestions)
        
        # Slow execution history
        slow_history = [
            {"duration": 15000},
            {"duration": 12000},
            {"duration": 18000}
        ]
        
        suggestions = await generator.suggest_improvements(workflow, slow_history)
        assert any("slow" in s.lower() or "caching" in s.lower() for s in suggestions)
    
    def test_generate_examples(self, generator):
        """Test example generation"""
        
        examples = generator.generate_examples()
        
        assert len(examples) > 0
        assert all("prompt" in ex for ex in examples)
        assert all("workflow_type" in ex for ex in examples)
        assert all("description" in ex for ex in examples)
        
        # Check variety
        types = {ex["workflow_type"] for ex in examples}
        assert "chatflow" in types
        assert "agentflow" in types
    
    @pytest.mark.asyncio
    async def test_generate_from_text_with_llm(self, generator, mock_llm_manager):
        """Test full generation with LLM"""
        
        generator.llm_manager = mock_llm_manager
        
        # Mock LLM response
        mock_llm_manager.generate.return_value = '''
        {
            "workflow_type": "chatflow",
            "name": "Customer Support Bot",
            "description": "Answers customer questions",
            "steps": [
                {
                    "type": "llm",
                    "purpose": "Generate response",
                    "inputs": ["question"],
                    "outputs": ["answer"]
                }
            ],
            "confidence": 0.9
        }
        '''
        
        result = await generator.generate_from_text(
            description="Create a customer support chatbot",
            user_id=1
        )
        
        assert isinstance(result, WorkflowIntent)
        assert result.workflow_type == "chatflow"
        assert result.name == "Customer Support Bot"
        assert len(result.nodes) >= 3
        assert result.confidence > 0
        
        # Verify LLM was called
        mock_llm_manager.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_from_text_fallback(self, generator):
        """Test generation without LLM (fallback)"""
        
        # No LLM manager - should use fallback
        result = await generator.generate_from_text(
            description="Create a chatbot that answers questions",
            user_id=1
        )
        
        assert isinstance(result, WorkflowIntent)
        assert result.workflow_type == "chatflow"
        assert len(result.nodes) >= 3
        assert len(result.edges) >= 2
    
    @pytest.mark.asyncio
    async def test_complex_workflow_generation(self, generator):
        """Test generation of complex multi-step workflow"""
        
        description = """
        Create a workflow that:
        1. Fetches data from an API
        2. Processes it with AI
        3. Checks if result is valid
        4. Sends notification if valid
        """
        
        result = await generator.generate_from_text(
            description=description,
            user_id=1
        )
        
        # Should detect multiple node types
        node_types = {n["type"] for n in result.nodes}
        assert "start" in node_types
        assert "end" in node_types
        
        # Should have multiple processing nodes
        processing_nodes = [
            n for n in result.nodes
            if n["type"] not in ["start", "end"]
        ]
        assert len(processing_nodes) >= 2
    
    @pytest.mark.asyncio
    async def test_context_usage(self, generator, mock_llm_manager):
        """Test that context is used in generation"""
        
        generator.llm_manager = mock_llm_manager
        
        mock_llm_manager.generate.return_value = '''
        {
            "workflow_type": "agentflow",
            "name": "Enhanced Workflow",
            "description": "Based on existing workflow",
            "steps": [{"type": "llm", "purpose": "Process", "inputs": [], "outputs": []}],
            "confidence": 0.85
        }
        '''
        
        context = {
            "existing_workflows": ["workflow1", "workflow2"],
            "preferences": {"default_model": "gpt-4"}
        }
        
        await generator.generate_from_text(
            description="Create a new workflow",
            user_id=1,
            context=context
        )
        
        # Check that context was passed to LLM
        call_args = mock_llm_manager.generate.call_args
        messages = call_args[1]["messages"]
        user_message = next(m for m in messages if m["role"] == "user")
        assert "Context:" in user_message["content"]
