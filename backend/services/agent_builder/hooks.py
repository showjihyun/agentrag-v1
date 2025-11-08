"""
Execution Hooks for Agent Builder.

Provides pre-execution, post-execution, and error hooks for agent/workflow executions.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime, timezone
from enum import Enum
import json

import httpx
from sqlalchemy.orm import Session

from backend.services.retry_handler import RetryHandler

logger = logging.getLogger(__name__)


class HookType(str, Enum):
    """Hook execution types."""
    PRE_EXECUTION = "pre_execution"
    POST_EXECUTION = "post_execution"
    ERROR = "error"


class HookMethod(str, Enum):
    """Hook invocation methods."""
    WEBHOOK = "webhook"
    PYTHON_FUNCTION = "python_function"


class HookConfig:
    """Configuration for a hook."""
    
    def __init__(
        self,
        hook_type: HookType,
        method: HookMethod,
        config: Dict[str, Any]
    ):
        """
        Initialize hook configuration.
        
        Args:
            hook_type: Type of hook (pre, post, error)
            method: Invocation method (webhook, python_function)
            config: Hook-specific configuration
        """
        self.hook_type = hook_type
        self.method = method
        self.config = config
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HookConfig":
        """Create HookConfig from dictionary."""
        return cls(
            hook_type=HookType(data["hook_type"]),
            method=HookMethod(data["method"]),
            config=data.get("config", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert HookConfig to dictionary."""
        return {
            "hook_type": self.hook_type.value,
            "method": self.method.value,
            "config": self.config
        }


class HookExecutor:
    """
    Executes hooks for agent/workflow executions.
    
    Features:
    - Webhook invocation with retry
    - Custom Python function execution
    - Safe execution with timeout
    - Detailed logging
    """
    
    def __init__(
        self,
        retry_handler: Optional[RetryHandler] = None,
        timeout: int = 30
    ):
        """
        Initialize hook executor.
        
        Args:
            retry_handler: Optional retry handler for failed hooks
            timeout: Timeout for hook execution in seconds
        """
        self.retry_handler = retry_handler or RetryHandler(
            max_retries=3,
            base_delay=1.0,
            max_delay=10.0
        )
        self.timeout = timeout
        self.http_client = httpx.AsyncClient(timeout=timeout)
        
        logger.info("HookExecutor initialized")
    
    async def execute_hooks(
        self,
        hooks: List[HookConfig],
        hook_type: HookType,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Execute all hooks of a specific type.
        
        Args:
            hooks: List of hook configurations
            hook_type: Type of hooks to execute
            context: Execution context data
            
        Returns:
            List of hook execution results
        """
        # Filter hooks by type
        matching_hooks = [h for h in hooks if h.hook_type == hook_type]
        
        if not matching_hooks:
            return []
        
        logger.info(f"Executing {len(matching_hooks)} {hook_type.value} hooks")
        
        results = []
        
        for hook in matching_hooks:
            try:
                result = await self._execute_single_hook(hook, context)
                results.append(result)
            except Exception as e:
                logger.error(f"Hook execution failed: {e}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "hook_type": hook.hook_type.value,
                    "method": hook.method.value
                })
        
        return results
    
    async def _execute_single_hook(
        self,
        hook: HookConfig,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single hook.
        
        Args:
            hook: Hook configuration
            context: Execution context
            
        Returns:
            Hook execution result
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            if hook.method == HookMethod.WEBHOOK:
                result = await self._execute_webhook_hook(hook, context)
            elif hook.method == HookMethod.PYTHON_FUNCTION:
                result = await self._execute_python_hook(hook, context)
            else:
                raise ValueError(f"Unknown hook method: {hook.method}")
            
            duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            
            return {
                "success": True,
                "result": result,
                "hook_type": hook.hook_type.value,
                "method": hook.method.value,
                "duration_ms": duration_ms
            }
            
        except Exception as e:
            duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            logger.error(f"Hook execution failed: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "hook_type": hook.hook_type.value,
                "method": hook.method.value,
                "duration_ms": duration_ms
            }
    
    async def _execute_webhook_hook(
        self,
        hook: HookConfig,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute webhook hook.
        
        Args:
            hook: Hook configuration
            context: Execution context
            
        Returns:
            Webhook response data
        """
        url = hook.config.get("url")
        method = hook.config.get("method", "POST").upper()
        headers = hook.config.get("headers", {})
        
        if not url:
            raise ValueError("Webhook URL not configured")
        
        # Prepare payload
        payload = {
            "hook_type": hook.hook_type.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": context
        }
        
        # Execute with retry
        async def make_request():
            if method == "POST":
                response = await self.http_client.post(
                    url,
                    json=payload,
                    headers=headers
                )
            elif method == "PUT":
                response = await self.http_client.put(
                    url,
                    json=payload,
                    headers=headers
                )
            elif method == "GET":
                response = await self.http_client.get(
                    url,
                    params={"context": json.dumps(context)},
                    headers=headers
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            try:
                return response.json()
            except:
                return {"status": "success", "text": response.text}
        
        result = await self.retry_handler.execute_with_retry(
            make_request,
            retry_on=(httpx.HTTPError, httpx.TimeoutException)
        )
        
        logger.info(f"Webhook hook executed successfully: {url}")
        
        return result
    
    async def _execute_python_hook(
        self,
        hook: HookConfig,
        context: Dict[str, Any]
    ) -> Any:
        """
        Execute Python function hook.
        
        Args:
            hook: Hook configuration
            context: Execution context
            
        Returns:
            Function execution result
        """
        function_code = hook.config.get("function_code")
        
        if not function_code:
            raise ValueError("Python function code not configured")
        
        # Create safe execution environment
        safe_globals = {
            "__builtins__": {
                # Safe built-ins only
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "set": set,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "sum": sum,
                "min": min,
                "max": max,
                "abs": abs,
                "round": round,
                "sorted": sorted,
                "reversed": reversed,
                "any": any,
                "all": all,
                "print": print,
                "isinstance": isinstance,
                "type": type,
            },
            "json": json,
            "datetime": datetime,
        }
        
        safe_locals = {
            "context": context,
            "result": None
        }
        
        # Execute with timeout
        try:
            # Compile code
            compiled_code = compile(function_code, "<hook>", "exec")
            
            # Execute with timeout
            await asyncio.wait_for(
                asyncio.to_thread(exec, compiled_code, safe_globals, safe_locals),
                timeout=self.timeout
            )
            
            result = safe_locals.get("result")
            
            logger.info("Python hook executed successfully")
            
            return result
            
        except asyncio.TimeoutError:
            raise TimeoutError(f"Hook execution timed out after {self.timeout}s")
        except Exception as e:
            logger.error(f"Python hook execution failed: {e}")
            raise
    
    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()


class HookManager:
    """
    Manages hooks for agents and workflows.
    
    Provides high-level interface for hook execution during agent/workflow lifecycle.
    """
    
    def __init__(
        self,
        db: Session,
        hook_executor: Optional[HookExecutor] = None
    ):
        """
        Initialize hook manager.
        
        Args:
            db: Database session
            db: Hook executor instance
        """
        self.db = db
        self.hook_executor = hook_executor or HookExecutor()
        
        logger.info("HookManager initialized")
    
    def get_hooks_from_config(self, config: Dict[str, Any]) -> List[HookConfig]:
        """
        Extract hooks from agent/workflow configuration.
        
        Args:
            config: Agent or workflow configuration
            
        Returns:
            List of HookConfig objects
        """
        hooks_data = config.get("hooks", [])
        
        if not hooks_data:
            return []
        
        hooks = []
        for hook_data in hooks_data:
            try:
                hook = HookConfig.from_dict(hook_data)
                hooks.append(hook)
            except Exception as e:
                logger.error(f"Failed to parse hook config: {e}")
        
        return hooks
    
    async def execute_pre_execution_hooks(
        self,
        config: Dict[str, Any],
        execution_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Execute pre-execution hooks.
        
        Args:
            config: Agent/workflow configuration
            execution_context: Execution context
            
        Returns:
            List of hook execution results
        """
        hooks = self.get_hooks_from_config(config)
        
        return await self.hook_executor.execute_hooks(
            hooks,
            HookType.PRE_EXECUTION,
            execution_context
        )
    
    async def execute_post_execution_hooks(
        self,
        config: Dict[str, Any],
        execution_context: Dict[str, Any],
        execution_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Execute post-execution hooks.
        
        Args:
            config: Agent/workflow configuration
            execution_context: Execution context
            execution_result: Execution result data
            
        Returns:
            List of hook execution results
        """
        hooks = self.get_hooks_from_config(config)
        
        # Add execution result to context
        context = {
            **execution_context,
            "execution_result": execution_result
        }
        
        return await self.hook_executor.execute_hooks(
            hooks,
            HookType.POST_EXECUTION,
            context
        )
    
    async def execute_error_hooks(
        self,
        config: Dict[str, Any],
        execution_context: Dict[str, Any],
        error: Exception
    ) -> List[Dict[str, Any]]:
        """
        Execute error hooks.
        
        Args:
            config: Agent/workflow configuration
            execution_context: Execution context
            error: Exception that occurred
            
        Returns:
            List of hook execution results
        """
        hooks = self.get_hooks_from_config(config)
        
        # Add error info to context
        context = {
            **execution_context,
            "error": {
                "type": type(error).__name__,
                "message": str(error),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        return await self.hook_executor.execute_hooks(
            hooks,
            HookType.ERROR,
            context
        )
    
    async def close(self):
        """Close hook executor."""
        await self.hook_executor.close()


# Example hook configurations

EXAMPLE_WEBHOOK_HOOK = {
    "hook_type": "post_execution",
    "method": "webhook",
    "config": {
        "url": "https://example.com/webhook",
        "method": "POST",
        "headers": {
            "Authorization": "Bearer ${WEBHOOK_TOKEN}",
            "Content-Type": "application/json"
        }
    }
}

EXAMPLE_PYTHON_HOOK = {
    "hook_type": "pre_execution",
    "method": "python_function",
    "config": {
        "function_code": """
# Pre-execution hook example
# Validate input data

input_data = context.get('input_data', {})

if not input_data.get('query'):
    raise ValueError('Query is required')

# Set result
result = {'validated': True}
"""
    }
}

EXAMPLE_ERROR_HOOK = {
    "hook_type": "error",
    "method": "webhook",
    "config": {
        "url": "https://example.com/error-notification",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json"
        }
    }
}
