"""
Agent Sandbox for secure execution.

Provides isolated execution environment with resource limits.
"""

import logging
import asyncio
import resource
import signal
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timezone
from contextlib import asynccontextmanager
import psutil
import os

logger = logging.getLogger(__name__)


class ResourceLimits:
    """Resource limits for sandbox execution."""
    
    def __init__(
        self,
        max_memory_mb: int = 512,
        max_cpu_time_seconds: int = 60,
        max_execution_time_seconds: int = 120,
        max_file_size_mb: int = 10,
        max_open_files: int = 100,
        max_processes: int = 10
    ):
        """
        Initialize resource limits.
        
        Args:
            max_memory_mb: Maximum memory in MB
            max_cpu_time_seconds: Maximum CPU time
            max_execution_time_seconds: Maximum wall clock time
            max_file_size_mb: Maximum file size
            max_open_files: Maximum open files
            max_processes: Maximum processes
        """
        self.max_memory_mb = max_memory_mb
        self.max_cpu_time_seconds = max_cpu_time_seconds
        self.max_execution_time_seconds = max_execution_time_seconds
        self.max_file_size_mb = max_file_size_mb
        self.max_open_files = max_open_files
        self.max_processes = max_processes


class SandboxViolation(Exception):
    """Raised when sandbox limits are violated."""
    pass


class AgentSandbox:
    """
    Secure sandbox for agent execution.
    
    Features:
    - Memory limits
    - CPU time limits
    - Execution timeout
    - File system restrictions
    - Network isolation (optional)
    - Process limits
    """
    
    def __init__(
        self,
        limits: Optional[ResourceLimits] = None,
        allowed_modules: Optional[list] = None,
        blocked_functions: Optional[list] = None
    ):
        """
        Initialize sandbox.
        
        Args:
            limits: Resource limits
            allowed_modules: List of allowed import modules
            blocked_functions: List of blocked function names
        """
        self.limits = limits or ResourceLimits()
        self.allowed_modules = allowed_modules or [
            "json", "math", "datetime", "re", "collections",
            "itertools", "functools", "typing"
        ]
        self.blocked_functions = blocked_functions or [
            "eval", "exec", "compile", "__import__",
            "open", "file", "input", "raw_input"
        ]
        
        logger.info("AgentSandbox initialized")
    
    @asynccontextmanager
    async def execute(self, execution_id: str):
        """
        Context manager for sandboxed execution.
        
        Usage:
            async with sandbox.execute("exec123"):
                # Your code here
                pass
        """
        # Set resource limits
        self._set_resource_limits()
        
        # Track execution
        start_time = datetime.now(timezone.utc)
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        try:
            # Create timeout
            async with asyncio.timeout(self.limits.max_execution_time_seconds):
                yield
            
            # Check final resource usage
            final_memory = process.memory_info().rss / 1024 / 1024
            memory_used = final_memory - initial_memory
            
            if memory_used > self.limits.max_memory_mb:
                raise SandboxViolation(
                    f"Memory limit exceeded: {memory_used:.1f}MB > {self.limits.max_memory_mb}MB"
                )
            
            logger.info(f"Sandbox execution completed: {execution_id}")
            
        except asyncio.TimeoutError:
            raise SandboxViolation(
                f"Execution timeout: {self.limits.max_execution_time_seconds}s exceeded"
            )
        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")
            raise
        finally:
            # Reset resource limits
            self._reset_resource_limits()
    
    def _set_resource_limits(self):
        """Set OS-level resource limits."""
        try:
            # CPU time limit
            resource.setrlimit(
                resource.RLIMIT_CPU,
                (self.limits.max_cpu_time_seconds, self.limits.max_cpu_time_seconds)
            )
            
            # Memory limit (virtual memory)
            max_memory_bytes = self.limits.max_memory_mb * 1024 * 1024
            resource.setrlimit(
                resource.RLIMIT_AS,
                (max_memory_bytes, max_memory_bytes)
            )
            
            # File size limit
            max_file_bytes = self.limits.max_file_size_mb * 1024 * 1024
            resource.setrlimit(
                resource.RLIMIT_FSIZE,
                (max_file_bytes, max_file_bytes)
            )
            
            # Open files limit
            resource.setrlimit(
                resource.RLIMIT_NOFILE,
                (self.limits.max_open_files, self.limits.max_open_files)
            )
            
            # Process limit
            resource.setrlimit(
                resource.RLIMIT_NPROC,
                (self.limits.max_processes, self.limits.max_processes)
            )
            
            logger.debug("Resource limits set")
            
        except Exception as e:
            logger.warning(f"Failed to set resource limits: {e}")
    
    def _reset_resource_limits(self):
        """Reset resource limits to defaults."""
        try:
            # Reset to soft limits
            resource.setrlimit(resource.RLIMIT_CPU, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
            resource.setrlimit(resource.RLIMIT_AS, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
            resource.setrlimit(resource.RLIMIT_FSIZE, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
            
            logger.debug("Resource limits reset")
        except Exception as e:
            logger.warning(f"Failed to reset resource limits: {e}")
    
    def create_safe_globals(self) -> Dict[str, Any]:
        """
        Create safe global namespace for code execution.
        
        Returns:
            Dictionary of safe built-ins and modules
        """
        safe_builtins = {
            # Safe built-in functions
            "abs": abs,
            "all": all,
            "any": any,
            "bool": bool,
            "dict": dict,
            "enumerate": enumerate,
            "filter": filter,
            "float": float,
            "int": int,
            "isinstance": isinstance,
            "len": len,
            "list": list,
            "map": map,
            "max": max,
            "min": min,
            "range": range,
            "reversed": reversed,
            "round": round,
            "set": set,
            "sorted": sorted,
            "str": str,
            "sum": sum,
            "tuple": tuple,
            "type": type,
            "zip": zip,
            
            # Safe constants
            "True": True,
            "False": False,
            "None": None,
        }
        
        # Add allowed modules
        safe_modules = {}
        for module_name in self.allowed_modules:
            try:
                safe_modules[module_name] = __import__(module_name)
            except ImportError:
                logger.warning(f"Failed to import allowed module: {module_name}")
        
        return {
            "__builtins__": safe_builtins,
            **safe_modules
        }
    
    def validate_code(self, code: str) -> bool:
        """
        Validate code for security issues.
        
        Args:
            code: Code to validate
            
        Returns:
            True if code is safe
            
        Raises:
            SandboxViolation: If code contains blocked patterns
        """
        # Check for blocked functions
        for func in self.blocked_functions:
            if func in code:
                raise SandboxViolation(f"Blocked function detected: {func}")
        
        # Check for dangerous imports
        dangerous_imports = [
            "os", "sys", "subprocess", "socket", "urllib",
            "requests", "http", "ftplib", "telnetlib",
            "pickle", "shelve", "marshal"
        ]
        
        for module in dangerous_imports:
            if f"import {module}" in code or f"from {module}" in code:
                raise SandboxViolation(f"Dangerous import detected: {module}")
        
        # Check for file operations
        file_operations = ["open(", "file(", "read(", "write("]
        for op in file_operations:
            if op in code:
                raise SandboxViolation(f"File operation detected: {op}")
        
        return True
    
    async def execute_code(
        self,
        code: str,
        context: Optional[Dict[str, Any]] = None,
        execution_id: Optional[str] = None
    ) -> Any:
        """
        Execute code in sandbox.
        
        Args:
            code: Code to execute
            context: Execution context
            execution_id: Optional execution ID
            
        Returns:
            Execution result
        """
        execution_id = execution_id or f"exec_{datetime.now(timezone.utc).timestamp()}"
        
        # Validate code
        self.validate_code(code)
        
        # Create safe environment
        safe_globals = self.create_safe_globals()
        safe_locals = {"context": context or {}, "result": None}
        
        # Execute in sandbox
        async with self.execute(execution_id):
            try:
                # Compile code
                compiled_code = compile(code, "<sandbox>", "exec")
                
                # Execute with timeout
                await asyncio.to_thread(
                    exec,
                    compiled_code,
                    safe_globals,
                    safe_locals
                )
                
                return safe_locals.get("result")
                
            except Exception as e:
                logger.error(f"Code execution failed: {e}")
                raise
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """
        Get current resource usage.
        
        Returns:
            Dictionary of resource usage metrics
        """
        process = psutil.Process(os.getpid())
        
        return {
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "cpu_percent": process.cpu_percent(interval=0.1),
            "num_threads": process.num_threads(),
            "num_fds": process.num_fds() if hasattr(process, 'num_fds') else None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class SandboxPool:
    """
    Pool of sandboxes for concurrent execution.
    
    Manages multiple sandboxes to handle concurrent agent executions.
    """
    
    def __init__(
        self,
        pool_size: int = 10,
        limits: Optional[ResourceLimits] = None
    ):
        """
        Initialize sandbox pool.
        
        Args:
            pool_size: Number of sandboxes in pool
            limits: Resource limits for each sandbox
        """
        self.pool_size = pool_size
        self.limits = limits or ResourceLimits()
        self.semaphore = asyncio.Semaphore(pool_size)
        self.active_executions = {}
        
        logger.info(f"SandboxPool initialized with {pool_size} sandboxes")
    
    @asynccontextmanager
    async def acquire(self, execution_id: str):
        """
        Acquire a sandbox from the pool.
        
        Usage:
            async with pool.acquire("exec123") as sandbox:
                result = await sandbox.execute_code(code)
        """
        async with self.semaphore:
            sandbox = AgentSandbox(limits=self.limits)
            self.active_executions[execution_id] = {
                "sandbox": sandbox,
                "start_time": datetime.now(timezone.utc)
            }
            
            try:
                yield sandbox
            finally:
                self.active_executions.pop(execution_id, None)
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get pool status."""
        return {
            "pool_size": self.pool_size,
            "active_executions": len(self.active_executions),
            "available_slots": self.pool_size - len(self.active_executions),
            "executions": [
                {
                    "execution_id": exec_id,
                    "duration_seconds": (
                        datetime.now(timezone.utc) - info["start_time"]
                    ).total_seconds()
                }
                for exec_id, info in self.active_executions.items()
            ]
        }


# Example usage
EXAMPLE_SAFE_CODE = """
# Safe code example
import json
import math

data = context.get("data", [])
result = {
    "sum": sum(data),
    "average": sum(data) / len(data) if data else 0,
    "max": max(data) if data else None,
    "min": min(data) if data else None
}
"""

EXAMPLE_UNSAFE_CODE = """
# This will be blocked
import os
os.system("rm -rf /")  # Dangerous!
"""
