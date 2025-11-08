"""Unit tests for AgentValidator."""

import pytest
from backend.validators.agent_validator import AgentValidator
from backend.models.agent_builder import AgentCreate, AgentUpdate


class TestAgentValidator:
    """Test AgentValidator methods."""
    
    def test_validate_create_success(self):
        """Test successful validation."""
        data = AgentCreate(
            name="Test Agent",
            description="Test Description",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1",
            tool_ids=[],
            knowledgebase_ids=[],
            is_public=False
        )
        
        errors = AgentValidator.validate_create(data)
        
        assert len(errors) == 0
    
    def test_validate_create_name_too_short(self):
        """Test validation fails for short name."""
        data = AgentCreate(
            name="ab",  # Too short
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1"
        )
        
        errors = AgentValidator.validate_create(data)
        
        assert len(errors) > 0
        assert any("at least 3 characters" in error for error in errors)
    
    def test_validate_create_name_too_long(self):
        """Test validation fails for long name."""
        data = AgentCreate(
            name="a" * 300,  # Too long
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1"
        )
        
        errors = AgentValidator.validate_create(data)
        
        assert len(errors) > 0
        assert any("must not exceed" in error for error in errors)
    
    def test_validate_create_invalid_agent_type(self):
        """Test validation fails for invalid agent type."""
        data = AgentCreate(
            name="Test Agent",
            agent_type="invalid_type",
            llm_provider="ollama",
            llm_model="llama3.1"
        )
        
        errors = AgentValidator.validate_create(data)
        
        assert len(errors) > 0
        assert any("Invalid agent type" in error for error in errors)
    
    def test_validate_create_invalid_llm_provider(self):
        """Test validation fails for invalid LLM provider."""
        data = AgentCreate(
            name="Test Agent",
            agent_type="custom",
            llm_provider="invalid_provider",
            llm_model="llama3.1"
        )
        
        errors = AgentValidator.validate_create(data)
        
        assert len(errors) > 0
        assert any("Invalid LLM provider" in error for error in errors)
    
    def test_validate_create_empty_llm_model(self):
        """Test validation fails for empty LLM model."""
        data = AgentCreate(
            name="Test Agent",
            agent_type="custom",
            llm_provider="ollama",
            llm_model=""
        )
        
        errors = AgentValidator.validate_create(data)
        
        assert len(errors) > 0
        assert any("LLM model is required" in error for error in errors)
    
    def test_validate_create_invalid_name_characters(self):
        """Test validation fails for invalid characters in name."""
        data = AgentCreate(
            name="Test@Agent#123",  # Invalid characters
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1"
        )
        
        errors = AgentValidator.validate_create(data)
        
        assert len(errors) > 0
        assert any("invalid characters" in error.lower() for error in errors)
    
    def test_validate_create_empty_tool_ids(self):
        """Test validation fails for empty tool IDs list."""
        data = AgentCreate(
            name="Test Agent",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1",
            tool_ids=[]  # Empty list is OK
        )
        
        errors = AgentValidator.validate_create(data)
        
        # Empty list should be valid
        assert not any("Tool IDs" in error for error in errors)
    
    def test_validate_create_duplicate_tool_ids(self):
        """Test validation fails for duplicate tool IDs."""
        data = AgentCreate(
            name="Test Agent",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1",
            tool_ids=["tool1", "tool2", "tool1"]  # Duplicate
        )
        
        errors = AgentValidator.validate_create(data)
        
        assert len(errors) > 0
        assert any("duplicates" in error.lower() for error in errors)
    
    def test_validate_update_success(self):
        """Test successful update validation."""
        data = AgentUpdate(
            name="Updated Name",
            description="Updated Description"
        )
        
        errors = AgentValidator.validate_update(data)
        
        assert len(errors) == 0
    
    def test_validate_update_name_too_short(self):
        """Test update validation fails for short name."""
        data = AgentUpdate(
            name="ab"  # Too short
        )
        
        errors = AgentValidator.validate_update(data)
        
        assert len(errors) > 0
        assert any("at least 3 characters" in error for error in errors)
    
    def test_validate_update_empty_llm_model(self):
        """Test update validation fails for empty LLM model."""
        data = AgentUpdate(
            llm_model=""
        )
        
        errors = AgentValidator.validate_update(data)
        
        assert len(errors) > 0
        assert any("cannot be empty" in error for error in errors)
    
    def test_validate_update_partial(self):
        """Test partial update validation."""
        data = AgentUpdate(
            name="Updated Name"
            # Other fields not provided
        )
        
        errors = AgentValidator.validate_update(data)
        
        # Should only validate provided fields
        assert len(errors) == 0
    
    def test_validate_clone_name_success(self):
        """Test clone name validation success."""
        errors = AgentValidator.validate_clone_name(
            original_name="Original Agent",
            new_name="Cloned Agent"
        )
        
        assert len(errors) == 0
    
    def test_validate_clone_name_auto_generated(self):
        """Test clone name validation with auto-generated name."""
        errors = AgentValidator.validate_clone_name(
            original_name="Original Agent",
            new_name=None  # Will auto-generate
        )
        
        # Auto-generated name should be valid
        assert len(errors) == 0
    
    def test_validate_clone_name_too_short(self):
        """Test clone name validation fails for short name."""
        errors = AgentValidator.validate_clone_name(
            original_name="Original Agent",
            new_name="ab"
        )
        
        assert len(errors) > 0
        assert any("at least 3 characters" in error for error in errors)


class TestAgentValidatorEdgeCases:
    """Test edge cases for AgentValidator."""
    
    def test_validate_name_with_spaces(self):
        """Test name with multiple spaces."""
        data = AgentCreate(
            name="Test   Agent   Name",  # Multiple spaces
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1"
        )
        
        errors = AgentValidator.validate_create(data)
        
        # Should be valid (spaces are allowed)
        assert len(errors) == 0
    
    def test_validate_name_with_hyphens(self):
        """Test name with hyphens."""
        data = AgentCreate(
            name="Test-Agent-Name",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1"
        )
        
        errors = AgentValidator.validate_create(data)
        
        assert len(errors) == 0
    
    def test_validate_name_with_underscores(self):
        """Test name with underscores."""
        data = AgentCreate(
            name="Test_Agent_Name",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1"
        )
        
        errors = AgentValidator.validate_create(data)
        
        assert len(errors) == 0
    
    def test_validate_name_with_parentheses(self):
        """Test name with parentheses."""
        data = AgentCreate(
            name="Test Agent (v2)",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1"
        )
        
        errors = AgentValidator.validate_create(data)
        
        assert len(errors) == 0
    
    def test_validate_description_max_length(self):
        """Test description at max length."""
        data = AgentCreate(
            name="Test Agent",
            description="a" * 2000,  # Max length
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1"
        )
        
        errors = AgentValidator.validate_create(data)
        
        # Should be valid at max length
        assert not any("Description" in error for error in errors)
    
    def test_validate_description_exceeds_max(self):
        """Test description exceeds max length."""
        data = AgentCreate(
            name="Test Agent",
            description="a" * 2001,  # Exceeds max
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1"
        )
        
        errors = AgentValidator.validate_create(data)
        
        assert len(errors) > 0
        assert any("Description" in error and "exceed" in error for error in errors)
    
    def test_validate_all_llm_providers(self):
        """Test all valid LLM providers."""
        providers = ["ollama", "openai", "claude", "anthropic"]
        
        for provider in providers:
            data = AgentCreate(
                name="Test Agent",
                agent_type="custom",
                llm_provider=provider,
                llm_model="test-model"
            )
            
            errors = AgentValidator.validate_create(data)
            
            # Should not have provider error
            assert not any("Invalid LLM provider" in error for error in errors)
    
    def test_validate_all_agent_types(self):
        """Test all valid agent types."""
        types = ["custom", "template_based"]
        
        for agent_type in types:
            data = AgentCreate(
                name="Test Agent",
                agent_type=agent_type,
                llm_provider="ollama",
                llm_model="llama3.1"
            )
            
            errors = AgentValidator.validate_create(data)
            
            # Should not have type error
            assert not any("Invalid agent type" in error for error in errors)
