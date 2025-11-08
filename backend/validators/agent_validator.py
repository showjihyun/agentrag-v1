"""Agent validation logic."""

import re
from typing import List, Dict, Any, Optional
from backend.models.agent_builder import AgentCreate, AgentUpdate


class AgentValidator:
    """Validator for Agent operations."""
    
    # Valid agent types
    VALID_AGENT_TYPES = ["custom", "template_based"]
    
    # Valid LLM providers
    VALID_LLM_PROVIDERS = ["ollama", "openai", "claude", "anthropic"]
    
    # Name constraints
    MIN_NAME_LENGTH = 3
    MAX_NAME_LENGTH = 255
    
    # Description constraints
    MAX_DESCRIPTION_LENGTH = 2000
    
    @classmethod
    def validate_create(cls, data: AgentCreate) -> List[str]:
        """
        Validate agent creation data.
        
        Args:
            data: Agent creation data
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate name
        name_errors = cls._validate_name(data.name)
        errors.extend(name_errors)
        
        # Validate description
        if data.description:
            desc_errors = cls._validate_description(data.description)
            errors.extend(desc_errors)
        
        # Validate agent type
        if data.agent_type not in cls.VALID_AGENT_TYPES:
            errors.append(
                f"Invalid agent type: {data.agent_type}. "
                f"Must be one of: {', '.join(cls.VALID_AGENT_TYPES)}"
            )
        
        # Validate LLM provider
        if data.llm_provider not in cls.VALID_LLM_PROVIDERS:
            errors.append(
                f"Invalid LLM provider: {data.llm_provider}. "
                f"Must be one of: {', '.join(cls.VALID_LLM_PROVIDERS)}"
            )
        
        # Validate LLM model
        if not data.llm_model or len(data.llm_model.strip()) == 0:
            errors.append("LLM model is required")
        
        # Validate configuration
        if data.configuration:
            config_errors = cls._validate_configuration(data.configuration)
            errors.extend(config_errors)
        
        # Validate tool IDs
        if data.tool_ids:
            tool_errors = cls._validate_tool_ids(data.tool_ids)
            errors.extend(tool_errors)
        
        # Validate knowledgebase IDs
        if data.knowledgebase_ids:
            kb_errors = cls._validate_knowledgebase_ids(data.knowledgebase_ids)
            errors.extend(kb_errors)
        
        return errors
    
    @classmethod
    def validate_update(cls, data: AgentUpdate) -> List[str]:
        """
        Validate agent update data.
        
        Args:
            data: Agent update data
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate name if provided
        if data.name is not None:
            name_errors = cls._validate_name(data.name)
            errors.extend(name_errors)
        
        # Validate description if provided
        if data.description is not None:
            desc_errors = cls._validate_description(data.description)
            errors.extend(desc_errors)
        
        # Validate agent type if provided
        if data.agent_type is not None and data.agent_type not in cls.VALID_AGENT_TYPES:
            errors.append(
                f"Invalid agent type: {data.agent_type}. "
                f"Must be one of: {', '.join(cls.VALID_AGENT_TYPES)}"
            )
        
        # Validate LLM provider if provided
        if data.llm_provider is not None and data.llm_provider not in cls.VALID_LLM_PROVIDERS:
            errors.append(
                f"Invalid LLM provider: {data.llm_provider}. "
                f"Must be one of: {', '.join(cls.VALID_LLM_PROVIDERS)}"
            )
        
        # Validate LLM model if provided
        if data.llm_model is not None and len(data.llm_model.strip()) == 0:
            errors.append("LLM model cannot be empty")
        
        # Validate configuration if provided
        if data.configuration is not None:
            config_errors = cls._validate_configuration(data.configuration)
            errors.extend(config_errors)
        
        # Validate tool IDs if provided
        if data.tool_ids is not None:
            tool_errors = cls._validate_tool_ids(data.tool_ids)
            errors.extend(tool_errors)
        
        # Validate knowledgebase IDs if provided
        if data.knowledgebase_ids is not None:
            kb_errors = cls._validate_knowledgebase_ids(data.knowledgebase_ids)
            errors.extend(kb_errors)
        
        return errors
    
    @classmethod
    def _validate_name(cls, name: str) -> List[str]:
        """Validate agent name."""
        errors = []
        
        if not name or len(name.strip()) == 0:
            errors.append("Name is required")
            return errors
        
        name = name.strip()
        
        if len(name) < cls.MIN_NAME_LENGTH:
            errors.append(f"Name must be at least {cls.MIN_NAME_LENGTH} characters")
        
        if len(name) > cls.MAX_NAME_LENGTH:
            errors.append(f"Name must not exceed {cls.MAX_NAME_LENGTH} characters")
        
        # Check for invalid characters
        if not re.match(r'^[a-zA-Z0-9\s\-_()]+$', name):
            errors.append("Name contains invalid characters. Only alphanumeric, spaces, hyphens, underscores, and parentheses are allowed")
        
        return errors
    
    @classmethod
    def _validate_description(cls, description: str) -> List[str]:
        """Validate agent description."""
        errors = []
        
        if len(description) > cls.MAX_DESCRIPTION_LENGTH:
            errors.append(f"Description must not exceed {cls.MAX_DESCRIPTION_LENGTH} characters")
        
        return errors
    
    @classmethod
    def _validate_configuration(cls, configuration: Dict[str, Any]) -> List[str]:
        """Validate agent configuration."""
        errors = []
        
        if not isinstance(configuration, dict):
            errors.append("Configuration must be a dictionary")
            return errors
        
        # Validate specific configuration keys if needed
        # For example, check for required keys, valid values, etc.
        
        return errors
    
    @classmethod
    def _validate_tool_ids(cls, tool_ids: List[str]) -> List[str]:
        """Validate tool IDs."""
        errors = []
        
        if not isinstance(tool_ids, list):
            errors.append("Tool IDs must be a list")
            return errors
        
        if len(tool_ids) == 0:
            errors.append("Tool IDs list cannot be empty")
        
        # Check for duplicates
        if len(tool_ids) != len(set(tool_ids)):
            errors.append("Tool IDs contain duplicates")
        
        # Validate each tool ID format
        for tool_id in tool_ids:
            if not isinstance(tool_id, str) or len(tool_id.strip()) == 0:
                errors.append(f"Invalid tool ID: {tool_id}")
        
        return errors
    
    @classmethod
    def _validate_knowledgebase_ids(cls, kb_ids: List[str]) -> List[str]:
        """Validate knowledgebase IDs."""
        errors = []
        
        if not isinstance(kb_ids, list):
            errors.append("Knowledgebase IDs must be a list")
            return errors
        
        if len(kb_ids) == 0:
            errors.append("Knowledgebase IDs list cannot be empty")
        
        # Check for duplicates
        if len(kb_ids) != len(set(kb_ids)):
            errors.append("Knowledgebase IDs contain duplicates")
        
        # Validate each KB ID format
        for kb_id in kb_ids:
            if not isinstance(kb_id, str) or len(kb_id.strip()) == 0:
                errors.append(f"Invalid knowledgebase ID: {kb_id}")
        
        return errors
    
    @classmethod
    def validate_clone_name(cls, original_name: str, new_name: Optional[str]) -> List[str]:
        """
        Validate cloned agent name.
        
        Args:
            original_name: Original agent name
            new_name: New name for cloned agent (optional)
            
        Returns:
            List of validation errors
        """
        if new_name is None:
            # Auto-generated name
            new_name = f"{original_name} (Copy)"
        
        return cls._validate_name(new_name)
