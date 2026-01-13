"""
Plugin system Pydantic models for the orchestration plugin system.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid


class PluginStatus(str, Enum):
    """Plugin status enumeration"""
    REGISTERED = "registered"
    INSTALLED = "installed"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    UPDATING = "updating"


class PluginCategory(str, Enum):
    """Plugin category enumeration"""
    ORCHESTRATION = "orchestration"
    INTEGRATION = "integration"
    UTILITY = "utility"
    MONITORING = "monitoring"


class AgentRole(str, Enum):
    """Agent role enumeration for orchestration patterns"""
    COORDINATOR = "coordinator"
    SPECIALIST = "specialist"
    WORKER = "worker"
    SYNTHESIZER = "synthesizer"


class PluginManifest(BaseModel):
    """Plugin manifest containing metadata and configuration"""
    name: str = Field(..., description="Plugin name")
    version: str = Field(..., description="Plugin version")
    description: str = Field(..., description="Plugin description")
    author: str = Field(..., description="Plugin author")
    license: str = Field(..., description="Plugin license")
    dependencies: List[str] = Field(default_factory=list, description="Plugin dependencies")
    permissions: List[str] = Field(default_factory=list, description="Required permissions")
    configuration_schema: Dict[str, Any] = Field(default_factory=dict, description="Configuration schema")
    supported_versions: List[str] = Field(default_factory=list, description="Supported system versions")
    category: PluginCategory = Field(..., description="Plugin category")
    signature: Optional[str] = Field(default=None, description="Digital signature for verification")
    
    class Config:
        use_enum_values = True


class PluginDependency(BaseModel):
    """Plugin dependency specification"""
    name: str = Field(..., description="Dependency name")
    version_constraint: str = Field(..., description="Version constraint")
    optional: bool = Field(default=False, description="Whether dependency is optional")


class PluginPermission(BaseModel):
    """Plugin permission specification"""
    name: str = Field(..., description="Permission name")
    description: str = Field(..., description="Permission description")
    required: bool = Field(default=True, description="Whether permission is required")


class OrchestrationPattern(BaseModel):
    """Orchestration pattern definition"""
    name: str = Field(..., description="Pattern name")
    description: str = Field(..., description="Pattern description")
    agent_roles: List[AgentRole] = Field(..., description="Required agent roles")
    communication_type: str = Field(..., description="Communication type")
    execution_mode: str = Field(..., description="Execution mode")
    configuration_schema: Dict[str, Any] = Field(default_factory=dict, description="Configuration schema")
    
    class Config:
        use_enum_values = True


class PluginInfo(BaseModel):
    """Complete plugin information"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Plugin ID")
    name: str = Field(..., description="Plugin name")
    version: str = Field(..., description="Plugin version")
    description: str = Field(..., description="Plugin description")
    author: str = Field(..., description="Plugin author")
    category: PluginCategory = Field(..., description="Plugin category")
    status: PluginStatus = Field(default=PluginStatus.REGISTERED, description="Plugin status")
    manifest: PluginManifest = Field(..., description="Plugin manifest")
    path: str = Field(..., description="Plugin file path")
    installed_at: Optional[datetime] = Field(default=None, description="Installation timestamp")
    last_updated: Optional[datetime] = Field(default=None, description="Last update timestamp")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Plugin configuration")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Plugin metrics")
    
    class Config:
        use_enum_values = True


class PluginConfiguration(BaseModel):
    """Plugin configuration for specific user and environment"""
    plugin_id: str = Field(..., description="Plugin ID")
    user_id: str = Field(..., description="User ID")
    environment: str = Field(default="production", description="Environment (dev, staging, prod)")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Configuration settings")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Update timestamp")


class ValidationResult(BaseModel):
    """Plugin validation result"""
    is_valid: bool = Field(..., description="Whether validation passed")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    
    @classmethod
    def combine(cls, results: List['ValidationResult']) -> 'ValidationResult':
        """Combine multiple validation results"""
        all_errors = []
        all_warnings = []
        is_valid = True
        
        for result in results:
            if not result.is_valid:
                is_valid = False
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        return cls(
            is_valid=is_valid,
            errors=all_errors,
            warnings=all_warnings
        )


class SecurityValidationResult(BaseModel):
    """Security validation result"""
    is_safe: bool = Field(..., description="Whether plugin is safe")
    threats: List[str] = Field(default_factory=list, description="Detected threats")
    threat_types: List[str] = Field(default_factory=list, description="Types of threats")


class ExecutionResult(BaseModel):
    """Plugin execution result"""
    exit_code: int = Field(..., description="Exit code")
    stdout: str = Field(default="", description="Standard output")
    stderr: str = Field(default="", description="Standard error")
    execution_time: float = Field(..., description="Execution time in seconds")


class ErrorResponse(BaseModel):
    """Error response with recovery information"""
    recovered: bool = Field(..., description="Whether error was recovered")
    message: str = Field(..., description="Error message")
    actions: List[str] = Field(default_factory=list, description="Suggested actions")


# Abstract base interfaces
class IPlugin(ABC):
    """Base interface for all orchestration plugins"""
    
    @abstractmethod
    def get_manifest(self) -> PluginManifest:
        """Return plugin manifest with metadata"""
        pass
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize plugin with configuration"""
        pass
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute plugin functionality"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup plugin resources"""
        pass
    
    @abstractmethod
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate plugin configuration, return errors if any"""
        pass


class IOrchestrationPlugin(IPlugin):
    """Interface for orchestration pattern plugins"""
    
    @abstractmethod
    def get_pattern(self) -> OrchestrationPattern:
        """Return orchestration pattern definition"""
        pass
    
    @abstractmethod
    async def orchestrate(self, agents: List[Dict], task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute orchestration logic"""
        pass
    
    @abstractmethod
    def get_ui_components(self) -> Dict[str, str]:
        """Return UI component definitions for configuration"""
        pass