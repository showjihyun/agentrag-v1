"""Secure Block Executor with RestrictedPython."""

import logging
import time
import json
from typing import Dict, Any, Optional
from RestrictedPython import compile_restricted, safe_globals
from RestrictedPython.Guards import (
    guarded_iter_unpack_sequence,
    safe_builtins,
)
from RestrictedPython.Eval import default_guarded_getitem

logger = logging.getLogger(__name__)


class SecureBlockExecutor:
    """Secure executor for logic blocks using RestrictedPython."""
    
    def __init__(self, use_docker: bool = False):
        """
        Initialize secure executor.
        
        Args:
            use_docker: Whether to use Docker for maximum isolation
        """
        self.max_execution_time = 5  # seconds
        self.max_memory = 128 * 1024 * 1024  # 128MB
        self.use_docker = use_docker
        
        # Blacklisted patterns (more comprehensive)
        self.dangerous_patterns = [
            # System access
            'import os', 'import sys', 'import subprocess', 'import socket',
            '__import__', 'importlib',
            # File operations
            'open(', 'file(', 'with open',
            # Code execution
            'eval(', 'exec(', 'compile(', 'execfile(',
            # Network
            'urllib', 'requests', 'http', 'socket',
            # Process control
            'fork(', 'spawn(', 'popen(',
            # Dangerous builtins
            'globals(', 'locals(', 'vars(', 'dir(',
            '__builtins__', '__dict__', '__class__',
            # Reflection
            'getattr(', 'setattr(', 'delattr(', 'hasattr(',
            # Memory access
            'memoryview', 'bytearray',
        ]
    
    def execute_logic_block(
        self,
        code: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute logic block code in restricted environment.
        
        Args:
            code: Python code to execute
            input_data: Input data for the block
            context: Execution context
            
        Returns:
            Dictionary with output
            
        Raises:
            ValueError: If code compilation or execution fails
            TimeoutError: If execution exceeds time limit
        """
        if not code or not code.strip():
            raise ValueError("Logic block has no implementation")
        
        # Compile with restrictions
        byte_code = compile_restricted(
            code,
            filename='<logic_block>',
            mode='exec'
        )
        
        if byte_code.errors:
            error_msg = "; ".join(byte_code.errors)
            raise ValueError(f"Code compilation failed: {error_msg}")
        
        # Create safe execution environment
        restricted_globals = self._create_safe_globals()
        
        restricted_locals = {
            'input': input_data,
            'context': context or {},
            'output': None,
            'result': None,
        }
        
        # Execute with timeout
        start_time = time.time()
        
        try:
            exec(byte_code.code, restricted_globals, restricted_locals)
            
            # Check execution time
            execution_time = time.time() - start_time
            if execution_time > self.max_execution_time:
                raise TimeoutError(
                    f"Execution exceeded time limit ({self.max_execution_time}s)"
                )
            
            # Get output
            output = restricted_locals.get('output') or restricted_locals.get('result')
            
            return {
                "output": output,
                "execution_time_ms": int(execution_time * 1000)
            }
            
        except TimeoutError:
            raise
        except Exception as e:
            logger.error(f"Logic block execution failed: {e}", exc_info=True)
            raise ValueError(f"Logic block execution failed: {str(e)}")
    
    def _create_safe_globals(self) -> Dict[str, Any]:
        """
        Create safe global environment for code execution.
        
        Returns:
            Dictionary of safe globals
        """
        # Start with safe builtins
        safe_builtins_dict = {
            'True': True,
            'False': False,
            'None': None,
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'tuple': tuple,
            'set': set,
            'range': range,
            'enumerate': enumerate,
            'zip': zip,
            'map': map,
            'filter': filter,
            'sorted': sorted,
            'sum': sum,
            'min': min,
            'max': max,
            'abs': abs,
            'round': round,
            'any': any,
            'all': all,
            'isinstance': isinstance,
            'type': type,
            'print': self._safe_print,  # Custom print
        }
        
        # Add safe string methods
        safe_string_methods = {
            'upper': str.upper,
            'lower': str.lower,
            'strip': str.strip,
            'split': str.split,
            'join': str.join,
            'replace': str.replace,
            'startswith': str.startswith,
            'endswith': str.endswith,
            'find': str.find,
            'format': str.format,
        }
        
        # Add safe list methods
        safe_list_methods = {
            'append': list.append,
            'extend': list.extend,
            'insert': list.insert,
            'remove': list.remove,
            'pop': list.pop,
            'clear': list.clear,
            'index': list.index,
            'count': list.count,
            'sort': list.sort,
            'reverse': list.reverse,
        }
        
        # Add safe dict methods
        safe_dict_methods = {
            'get': dict.get,
            'keys': dict.keys,
            'values': dict.values,
            'items': dict.items,
            'update': dict.update,
            'pop': dict.pop,
            'clear': dict.clear,
        }
        
        # Add safe JSON operations
        safe_json = {
            'loads': json.loads,
            'dumps': json.dumps,
        }
        
        # Combine all safe operations
        restricted_globals = {
            '__builtins__': safe_builtins_dict,
            '_getiter_': guarded_iter_unpack_sequence,
            '_iter_unpack_sequence_': guarded_iter_unpack_sequence,
            '__name__': 'restricted_module',
            '__metaclass__': type,
            '_getitem_': default_guarded_getitem,
            # Add safe modules
            'json': type('json', (), safe_json),
            'str': type('str', (), safe_string_methods),
            'list': type('list', (), safe_list_methods),
            'dict': type('dict', (), safe_dict_methods),
        }
        
        return restricted_globals
    
    def _safe_print(self, *args, **kwargs):
        """
        Safe print function that logs instead of printing to stdout.
        
        Args:
            *args: Arguments to print
            **kwargs: Keyword arguments
        """
        message = " ".join(str(arg) for arg in args)
        logger.info(f"[Logic Block Print] {message}")
    
    def validate_code(self, code: str) -> tuple[bool, list[str]]:
        """
        Validate code without executing it.
        
        Args:
            code: Python code to validate
            
        Returns:
            Tuple of (is_valid, errors)
        """
        if not code or not code.strip():
            return False, ["Code is empty"]
        
        # Check code length
        if len(code) > 10000:  # 10KB limit
            return False, ["Code is too long (max 10KB)"]
        
        # Try to compile
        byte_code = compile_restricted(
            code,
            filename='<logic_block>',
            mode='exec'
        )
        
        if byte_code.errors:
            return False, byte_code.errors
        
        # Check for dangerous patterns
        code_lower = code.lower()
        warnings = []
        
        for pattern in self.dangerous_patterns:
            if pattern.lower() in code_lower:
                warnings.append(f"Dangerous pattern detected: {pattern}")
        
        # Check for suspicious string operations
        if any(x in code for x in ['chr(', 'ord(', 'hex(', 'oct(']):
            warnings.append("Suspicious character encoding detected")
        
        # Check for base64 or encoding attempts
        if any(x in code_lower for x in ['base64', 'decode', 'encode']):
            warnings.append("Encoding/decoding operations detected")
        
        if warnings:
            return False, warnings
        
        return True, []


class DockerBlockExecutor:
    """
    Docker-based block executor for maximum isolation.
    
    This is a more secure alternative that runs code in isolated containers.
    Requires Docker to be installed and running.
    """
    
    def __init__(self):
        """Initialize Docker executor."""
        try:
            import docker
            self.docker_client = docker.from_env()
            self.docker_available = True
        except Exception as e:
            logger.warning(f"Docker not available: {e}")
            self.docker_available = False
    
    def execute_logic_block(
        self,
        code: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute logic block in Docker container.
        
        Args:
            code: Python code to execute
            input_data: Input data for the block
            context: Execution context
            
        Returns:
            Dictionary with output
            
        Raises:
            ValueError: If Docker is not available or execution fails
        """
        if not self.docker_available:
            raise ValueError("Docker is not available")
        
        # Create execution script
        script = f"""
import json
import sys

# Load input data
input_data = {json.dumps(input_data)}
context = {json.dumps(context or {{}})}

# User code
try:
    {code}
    
    # Get output
    if 'output' in locals():
        result = output
    elif 'result' in locals():
        result = result
    else:
        result = None
    
    print(json.dumps({{"success": True, "output": result}}))
except Exception as e:
    print(json.dumps({{"success": False, "error": str(e)}}))
    sys.exit(1)
"""
        
        try:
            # Run in isolated container
            container = self.docker_client.containers.run(
                "python:3.10-alpine",
                command=["python", "-c", script],
                remove=True,
                mem_limit="128m",
                cpu_period=100000,
                cpu_quota=50000,  # 50% CPU
                network_disabled=True,
                timeout=5,
                detach=False,
            )
            
            # Parse result
            output = container.decode('utf-8')
            result = json.loads(output)
            
            if not result.get('success'):
                raise ValueError(result.get('error', 'Unknown error'))
            
            return {"output": result.get('output')}
            
        except Exception as e:
            logger.error(f"Docker execution failed: {e}", exc_info=True)
            raise ValueError(f"Docker execution failed: {str(e)}")


# Factory function to get appropriate executor
def get_block_executor(use_docker: bool = False) -> Any:
    """
    Get appropriate block executor.
    
    Args:
        use_docker: Whether to use Docker executor
        
    Returns:
        Block executor instance
    """
    if use_docker:
        executor = DockerBlockExecutor()
        if executor.docker_available:
            return executor
        logger.warning("Docker requested but not available, falling back to RestrictedPython")
    
    return SecureBlockExecutor()
