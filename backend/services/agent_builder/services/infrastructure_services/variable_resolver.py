"""Variable Resolver for workflow variables."""

import logging
import re
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from uuid import UUID
from cachetools import TTLCache
import threading

from backend.db.models.agent_builder import Variable
from backend.models.agent_builder import ExecutionContext

logger = logging.getLogger(__name__)


class VariableResolver:
    """Service for resolving workflow variables with caching."""
    
    # Class-level cache shared across instances
    _cache = TTLCache(maxsize=1000, ttl=300)  # 5 minutes TTL
    _cache_lock = threading.Lock()
    
    def __init__(self, db: Session):
        """
        Initialize Variable Resolver.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_variable(
        self,
        name: str,
        scope: str,
        scope_id: Optional[str],
        value: str,
        value_type: str,
        is_secret: bool = False
    ) -> Variable:
        """
        Create a new variable.
        
        Args:
            name: Variable name
            scope: Variable scope (global, workspace, user, agent)
            scope_id: Scope ID (for user, agent, workspace scopes)
            value: Variable value
            value_type: Value type (string, number, boolean, json)
            is_secret: Whether value is secret
            
        Returns:
            Created Variable model
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # Validate scope
            valid_scopes = ["global", "workspace", "user", "agent"]
            if scope not in valid_scopes:
                raise ValueError(f"Invalid scope: {scope}. Must be one of {valid_scopes}")
            
            # Validate scope_id requirement
            if scope in ["workspace", "user", "agent"] and not scope_id:
                raise ValueError(f"scope_id is required for scope '{scope}'")
            
            # Check for duplicate
            existing = self.db.query(Variable).filter(
                Variable.name == name,
                Variable.scope == scope,
                Variable.scope_id == (UUID(scope_id) if scope_id else None),
                Variable.deleted_at.is_(None)
            ).first()
            
            if existing:
                raise ValueError(f"Variable '{name}' already exists in scope '{scope}'")
            
            variable = Variable(
                id=str(uuid.uuid4()),
                name=name,
                scope=scope,
                scope_id=UUID(scope_id) if scope_id else None,
                value=value,
                value_type=value_type,
                is_secret=is_secret
            )
            
            self.db.add(variable)
            self.db.commit()
            self.db.refresh(variable)
            
            logger.info(f"Created variable: {name} (scope: {scope})")
            return variable
            
        except ValueError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create variable: {e}", exc_info=True)
            raise
    
    def update_variable(
        self,
        variable_id: str,
        value: Optional[str] = None,
        value_type: Optional[str] = None
    ) -> Variable:
        """
        Update variable and invalidate cache.
        
        Args:
            variable_id: Variable ID
            value: New value (optional)
            value_type: New value type (optional)
            
        Returns:
            Updated Variable model
            
        Raises:
            ValueError: If variable not found
        """
        try:
            variable = self.db.query(Variable).filter(
                Variable.id == UUID(variable_id),
                Variable.deleted_at.is_(None)
            ).first()
            
            if not variable:
                raise ValueError(f"Variable {variable_id} not found")
            
            if value is not None:
                variable.value = value
            
            if value_type is not None:
                valid_types = ["string", "number", "boolean", "json"]
                if value_type not in valid_types:
                    raise ValueError(f"Invalid value_type: {value_type}")
                variable.value_type = value_type
            
            variable.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(variable)
            
            # Invalidate cache for this variable
            self.invalidate_cache(name=variable.name)
            
            logger.info(f"Updated variable: {variable.name}")
            return variable
            
        except ValueError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update variable: {e}", exc_info=True)
            raise
    
    def delete_variable(self, variable_id: str) -> bool:
        """
        Soft delete variable and invalidate cache.
        
        Args:
            variable_id: Variable ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            variable = self.db.query(Variable).filter(
                Variable.id == UUID(variable_id),
                Variable.deleted_at.is_(None)
            ).first()
            
            if not variable:
                return False
            
            variable_name = variable.name
            variable.deleted_at = datetime.utcnow()
            self.db.commit()
            
            # Invalidate cache for this variable
            self.invalidate_cache(name=variable_name)
            
            logger.info(f"Deleted variable: {variable_name}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete variable: {e}", exc_info=True)
            raise
    
    def list_variables(
        self,
        scope: Optional[str] = None,
        scope_id: Optional[str] = None,
        include_deleted: bool = False
    ) -> List[Variable]:
        """
        List variables with filters.
        
        Args:
            scope: Filter by scope (optional)
            scope_id: Filter by scope_id (optional)
            include_deleted: Include soft-deleted variables
            
        Returns:
            List of Variable models
        """
        query = self.db.query(Variable)
        
        if not include_deleted:
            query = query.filter(Variable.deleted_at.is_(None))
        
        if scope:
            query = query.filter(Variable.scope == scope)
        
        if scope_id:
            query = query.filter(Variable.scope_id == UUID(scope_id))
        
        return query.order_by(Variable.created_at.desc()).all()
    
    async def resolve_variables(
        self,
        template: str,
        context: ExecutionContext,
        default_values: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Resolve variables in template string.
        
        Replaces ${variable_name} with actual values based on scope hierarchy:
        1. Agent scope (if agent_id in context)
        2. User scope
        3. Workspace scope (if workspace_id in context)
        4. Global scope
        5. Default values (if provided)
        
        Args:
            template: Template string with ${variable_name} placeholders
            context: Execution context
            default_values: Default values for variables (optional)
            
        Returns:
            Resolved string with variables replaced
        """
        if not template:
            return template
        
        # Find all variable references
        pattern = r'\$\{([^}]+)\}'
        matches = re.findall(pattern, template)
        
        if not matches:
            return template
        
        resolved = template
        
        for var_name in matches:
            # Try to find variable in database (scope hierarchy)
            variable = self._find_variable(var_name, context)
            
            if variable:
                value = self._get_variable_value(variable)
            elif default_values and var_name in default_values:
                value = str(default_values[var_name])
            else:
                logger.warning(f"Variable not found: {var_name}")
                value = f"${{{var_name}}}"  # Keep original placeholder
            
            resolved = resolved.replace(f"${{{var_name}}}", value)
        
        return resolved
    
    def _find_variable(
        self,
        name: str,
        context: ExecutionContext
    ) -> Optional[Variable]:
        """
        Find variable by name using scope hierarchy with caching.
        
        Args:
            name: Variable name
            context: Execution context
            
        Returns:
            Variable model or None if not found
        """
        # Generate cache key
        cache_key = self._generate_cache_key(name, context)
        
        # Check cache first
        with self._cache_lock:
            if cache_key in self._cache:
                cached_var = self._cache[cache_key]
                logger.debug(f"Variable cache hit: {name}")
                return cached_var
        
        # Cache miss - query database
        variable = self._query_variable_from_db(name, context)
        
        # Store in cache
        if variable:
            with self._cache_lock:
                self._cache[cache_key] = variable
        
        return variable
    
    def _generate_cache_key(
        self,
        name: str,
        context: ExecutionContext
    ) -> str:
        """
        Generate cache key for variable lookup.
        
        Args:
            name: Variable name
            context: Execution context
            
        Returns:
            Cache key string
        """
        return (
            f"{name}:"
            f"{context.agent_id or 'none'}:"
            f"{context.user_id or 'none'}:"
            f"{context.workspace_id or 'none'}"
        )
    
    def _query_variable_from_db(
        self,
        name: str,
        context: ExecutionContext
    ) -> Optional[Variable]:
        """
        Query variable from database using scope hierarchy.
        
        Args:
            name: Variable name
            context: Execution context
            
        Returns:
            Variable model or None if not found
        """
        # 1. Try agent scope first (highest priority)
        if context.agent_id:
            var = self.db.query(Variable).filter(
                Variable.name == name,
                Variable.scope == "agent",
                Variable.scope_id == UUID(context.agent_id),
                Variable.deleted_at.is_(None)
            ).first()
            if var:
                return var
        
        # 2. Try user scope
        if context.user_id:
            var = self.db.query(Variable).filter(
                Variable.name == name,
                Variable.scope == "user",
                Variable.scope_id == UUID(context.user_id),
                Variable.deleted_at.is_(None)
            ).first()
            if var:
                return var
        
        # 3. Try workspace scope
        if context.workspace_id:
            var = self.db.query(Variable).filter(
                Variable.name == name,
                Variable.scope == "workspace",
                Variable.scope_id == UUID(context.workspace_id),
                Variable.deleted_at.is_(None)
            ).first()
            if var:
                return var
        
        # 4. Try global scope (lowest priority)
        var = self.db.query(Variable).filter(
            Variable.name == name,
            Variable.scope == "global",
            Variable.deleted_at.is_(None)
        ).first()
        
        return var
    
    def invalidate_cache(self, name: Optional[str] = None, context: Optional[ExecutionContext] = None):
        """
        Invalidate variable cache.
        
        Args:
            name: Variable name to invalidate (None for all)
            context: Execution context (None for all)
        """
        with self._cache_lock:
            if name is None and context is None:
                # Clear entire cache
                self._cache.clear()
                logger.info("Variable cache cleared")
            elif name and context:
                # Clear specific variable
                cache_key = self._generate_cache_key(name, context)
                self._cache.pop(cache_key, None)
                logger.debug(f"Variable cache invalidated: {name}")
            else:
                # Clear all matching variables
                keys_to_remove = []
                for key in self._cache.keys():
                    if name and key.startswith(f"{name}:"):
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    self._cache.pop(key, None)
                
                logger.debug(f"Variable cache invalidated: {len(keys_to_remove)} entries")
    
    def _get_variable_value(self, variable: Variable) -> str:
        """
        Get variable value with type conversion and secret decryption.
        
        Args:
            variable: Variable model
            
        Returns:
            String representation of variable value
        """
        if variable.is_secret:
            # Decrypt secret value
            try:
                from backend.services.agent_builder.secret_manager import SecretManager
                secret_manager = SecretManager(self.db)
                return secret_manager.decrypt_variable(str(variable.id))
            except Exception as e:
                logger.error(f"Failed to decrypt secret variable: {e}")
                return "********"  # Return masked value on error
        
        # Convert based on type
        if variable.value_type == "number":
            return str(variable.value)
        elif variable.value_type == "boolean":
            return str(variable.value).lower()
        elif variable.value_type == "json":
            return variable.value
        else:  # string
            return variable.value
