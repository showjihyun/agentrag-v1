"""
Plugin Security Manager

Provides comprehensive security validation and code scanning for plugins.
Implements static code analysis, malware detection, and signature verification.
"""

import ast
import hashlib
import hmac
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum

import docker
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.exceptions import InvalidSignature

from backend.core.logging_standards import StandardLogger
from backend.models.plugin import PluginManifest

import logging

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Security threat levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """Types of security threats"""
    MALICIOUS_CODE = "malicious_code"
    SUSPICIOUS_IMPORTS = "suspicious_imports"
    DANGEROUS_FUNCTIONS = "dangerous_functions"
    NETWORK_ACCESS = "network_access"
    FILE_SYSTEM_ACCESS = "file_system_access"
    PROCESS_EXECUTION = "process_execution"
    SIGNATURE_INVALID = "signature_invalid"
    DEPENDENCY_VULNERABILITY = "dependency_vulnerability"


@dataclass
class SecurityThreat:
    """Represents a security threat found in plugin code"""
    threat_type: ThreatType
    level: ThreatLevel
    description: str
    location: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of security validation"""
    is_valid: bool
    threats: List[SecurityThreat]
    score: float  # 0-100, higher is safer
    
    @classmethod
    def combine(cls, results: List['ValidationResult']) -> 'ValidationResult':
        """Combine multiple validation results"""
        all_threats = []
        min_score = 100.0
        
        for result in results:
            all_threats.extend(result.threats)
            min_score = min(min_score, result.score)
        
        # Plugin is valid only if all validations pass and no critical threats
        is_valid = all(r.is_valid for r in results) and not any(
            t.level == ThreatLevel.CRITICAL for t in all_threats
        )
        
        return cls(
            is_valid=is_valid,
            threats=all_threats,
            score=min_score
        )


class PluginSecurityManager:
    """Manages plugin security validation and sandboxing"""
    
    # Dangerous imports that should be flagged
    DANGEROUS_IMPORTS = {
        'os', 'subprocess', 'sys', 'shutil', 'tempfile', 'socket', 
        'urllib', 'requests', 'http', 'ftplib', 'smtplib', 'telnetlib',
        'pickle', 'marshal', 'shelve', 'dbm', 'eval', 'exec', 'compile',
        '__import__', 'importlib', 'ctypes', 'multiprocessing', 'threading'
    }
    
    # Dangerous function calls
    DANGEROUS_FUNCTIONS = {
        'eval', 'exec', 'compile', '__import__', 'open', 'file',
        'input', 'raw_input', 'execfile', 'reload', 'vars', 'globals',
        'locals', 'dir', 'hasattr', 'getattr', 'setattr', 'delattr'
    }
    
    # Malicious code patterns
    MALICIOUS_PATTERNS = [
        r'rm\s+-rf\s+/',  # Delete root filesystem
        r'format\s+c:',   # Format C drive
        r'del\s+/[sq]',   # Delete system directories
        r'sudo\s+rm',     # Sudo delete commands
        r'chmod\s+777',   # Dangerous permissions
        r'wget.*\|\s*sh', # Download and execute
        r'curl.*\|\s*sh', # Download and execute
        r'base64.*decode', # Encoded malicious code
        r'reverse_shell', # Reverse shell attempts
        r'backdoor',      # Backdoor references
        r'keylogger',     # Keylogger references
        r'password.*steal', # Password stealing
    ]
    
    def __init__(self, docker_client: Optional[docker.DockerClient] = None):
        """Initialize security manager"""
        self.docker_client = docker_client or docker.from_env()
        self.sandbox_image = "python:3.10-slim"  # Base sandbox image
        
    async def validate_plugin(self, plugin_path: str, manifest: PluginManifest) -> ValidationResult:
        """Comprehensive plugin security validation"""
        logger.info(f"Starting security validation for plugin: {manifest.name}")
        
        results = []
        
        try:
            # Static code analysis
            static_result = await self._static_code_analysis(plugin_path)
            results.append(static_result)
            
            # Malware pattern detection
            malware_result = await self._scan_malware_patterns(plugin_path)
            results.append(malware_result)
            
            # Dependency security check
            dep_result = await self._check_dependency_security(manifest.dependencies)
            results.append(dep_result)
            
            # Signature verification (if signature exists)
            if hasattr(manifest, 'signature') and manifest.signature:
                sig_result = await self._verify_signature(plugin_path, manifest.signature)
                results.append(sig_result)
            
            combined_result = ValidationResult.combine(results)
            
            logger.info(
                f"Security validation completed for {manifest.name}. "
                f"Valid: {combined_result.is_valid}, Score: {combined_result.score:.1f}, "
                f"Threats: {len(combined_result.threats)}"
            )
            
            return combined_result
            
        except Exception as e:
            logger.error(f"Security validation failed for {manifest.name}: {str(e)}")
            return ValidationResult(
                is_valid=False,
                threats=[SecurityThreat(
                    threat_type=ThreatType.MALICIOUS_CODE,
                    level=ThreatLevel.CRITICAL,
                    description=f"Validation error: {str(e)}"
                )],
                score=0.0
            )
    
    async def _static_code_analysis(self, plugin_path: str) -> ValidationResult:
        """Perform static code analysis on plugin"""
        threats = []
        score = 100.0
        
        try:
            # Read and parse Python files
            python_files = self._find_python_files(plugin_path)
            
            for file_path in python_files:
                file_threats = await self._analyze_python_file(file_path)
                threats.extend(file_threats)
        
        except Exception as e:
            logger.error(f"Static code analysis failed: {str(e)}")
            threats.append(SecurityThreat(
                threat_type=ThreatType.MALICIOUS_CODE,
                level=ThreatLevel.HIGH,
                description=f"Code analysis error: {str(e)}"
            ))
        
        # Calculate score based on threats
        for threat in threats:
            if threat.level == ThreatLevel.CRITICAL:
                score -= 50
            elif threat.level == ThreatLevel.HIGH:
                score -= 25
            elif threat.level == ThreatLevel.MEDIUM:
                score -= 10
            elif threat.level == ThreatLevel.LOW:
                score -= 5
        
        score = max(0, score)
        is_valid = score >= 70 and not any(t.level == ThreatLevel.CRITICAL for t in threats)
        
        return ValidationResult(is_valid=is_valid, threats=threats, score=score)
    
    async def _analyze_python_file(self, file_path: str) -> List[SecurityThreat]:
        """Analyze a single Python file for security threats"""
        threats = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content, filename=file_path)
            
            # Check for dangerous imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in self.DANGEROUS_IMPORTS:
                            threats.append(SecurityThreat(
                                threat_type=ThreatType.SUSPICIOUS_IMPORTS,
                                level=ThreatLevel.MEDIUM,
                                description=f"Dangerous import: {alias.name}",
                                location=file_path,
                                line_number=node.lineno
                            ))
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module in self.DANGEROUS_IMPORTS:
                        threats.append(SecurityThreat(
                            threat_type=ThreatType.SUSPICIOUS_IMPORTS,
                            level=ThreatLevel.MEDIUM,
                            description=f"Dangerous import from: {node.module}",
                            location=file_path,
                            line_number=node.lineno
                        ))
                
                elif isinstance(node, ast.Call):
                    # Check for dangerous function calls
                    if isinstance(node.func, ast.Name):
                        if node.func.id in self.DANGEROUS_FUNCTIONS:
                            threats.append(SecurityThreat(
                                threat_type=ThreatType.DANGEROUS_FUNCTIONS,
                                level=ThreatLevel.HIGH,
                                description=f"Dangerous function call: {node.func.id}",
                                location=file_path,
                                line_number=node.lineno
                            ))
        
        except SyntaxError as e:
            threats.append(SecurityThreat(
                threat_type=ThreatType.MALICIOUS_CODE,
                level=ThreatLevel.MEDIUM,
                description=f"Syntax error in {file_path}: {str(e)}",
                location=file_path,
                line_number=getattr(e, 'lineno', None)
            ))
        
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {str(e)}")
        
        return threats
    
    async def _scan_malware_patterns(self, plugin_path: str) -> ValidationResult:
        """Scan for known malware patterns"""
        threats = []
        score = 100.0
        
        try:
            # Read all text files and scan for patterns
            text_files = self._find_text_files(plugin_path)
            
            for file_path in text_files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    for pattern in self.MALICIOUS_PATTERNS:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            threats.append(SecurityThreat(
                                threat_type=ThreatType.MALICIOUS_CODE,
                                level=ThreatLevel.CRITICAL,
                                description=f"Malicious pattern detected: {pattern}",
                                location=file_path,
                                line_number=line_num,
                                code_snippet=match.group()
                            ))
                            score -= 30
                
                except Exception as e:
                    logger.warning(f"Could not scan file {file_path}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Malware pattern scanning failed: {str(e)}")
            threats.append(SecurityThreat(
                threat_type=ThreatType.MALICIOUS_CODE,
                level=ThreatLevel.HIGH,
                description=f"Malware scan error: {str(e)}"
            ))
        
        score = max(0, score)
        is_valid = not any(t.level == ThreatLevel.CRITICAL for t in threats)
        
        return ValidationResult(is_valid=is_valid, threats=threats, score=score)
    
    async def _check_dependency_security(self, dependencies: List[str]) -> ValidationResult:
        """Check dependencies for known vulnerabilities"""
        threats = []
        score = 100.0
        
        # Known vulnerable packages (simplified list)
        VULNERABLE_PACKAGES = {
            'pickle5': 'Known security vulnerabilities',
            'pyyaml': 'Versions < 5.1 have vulnerabilities',
            'requests': 'Versions < 2.20.0 have vulnerabilities',
            'urllib3': 'Versions < 1.24.2 have vulnerabilities'
        }
        
        for dep in dependencies:
            # Extract package name (remove version constraints)
            package_name = re.split(r'[<>=!]', dep)[0].strip()
            
            if package_name in VULNERABLE_PACKAGES:
                threats.append(SecurityThreat(
                    threat_type=ThreatType.DEPENDENCY_VULNERABILITY,
                    level=ThreatLevel.MEDIUM,
                    description=f"Potentially vulnerable dependency: {package_name} - {VULNERABLE_PACKAGES[package_name]}"
                ))
                score -= 15
        
        score = max(0, score)
        is_valid = score >= 70
        
        return ValidationResult(is_valid=is_valid, threats=threats, score=score)
    
    async def _verify_signature(self, plugin_path: str, signature: str) -> ValidationResult:
        """Verify plugin digital signature"""
        threats = []
        score = 100.0
        
        try:
            # Calculate file hash
            file_hash = self._calculate_file_hash(plugin_path)
            
            # For now, implement a simple HMAC verification
            # In production, this would use proper digital signatures
            expected_signature = hmac.new(
                b'plugin_signing_key',  # This should be a proper key
                file_hash.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                threats.append(SecurityThreat(
                    threat_type=ThreatType.SIGNATURE_INVALID,
                    level=ThreatLevel.HIGH,
                    description="Invalid plugin signature"
                ))
                score = 0
        
        except Exception as e:
            logger.error(f"Signature verification failed: {str(e)}")
            threats.append(SecurityThreat(
                threat_type=ThreatType.SIGNATURE_INVALID,
                level=ThreatLevel.HIGH,
                description=f"Signature verification error: {str(e)}"
            ))
            score = 0
        
        is_valid = len(threats) == 0
        return ValidationResult(is_valid=is_valid, threats=threats, score=score)
    
    def _find_python_files(self, path: str) -> List[str]:
        """Find all Python files in the given path"""
        python_files = []
        path_obj = Path(path)
        
        if path_obj.is_file() and path_obj.suffix == '.py':
            return [str(path_obj)]
        
        if path_obj.is_dir():
            for file_path in path_obj.rglob('*.py'):
                python_files.append(str(file_path))
        
        return python_files
    
    def _find_text_files(self, path: str) -> List[str]:
        """Find all text files for pattern scanning"""
        text_files = []
        path_obj = Path(path)
        
        text_extensions = {'.py', '.txt', '.md', '.yml', '.yaml', '.json', '.sh', '.bat'}
        
        if path_obj.is_file():
            if path_obj.suffix in text_extensions:
                return [str(path_obj)]
            return []
        
        if path_obj.is_dir():
            for file_path in path_obj.rglob('*'):
                if file_path.is_file() and file_path.suffix in text_extensions:
                    text_files.append(str(file_path))
        
        return text_files
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file or directory"""
        hasher = hashlib.sha256()
        
        path_obj = Path(file_path)
        if path_obj.is_file():
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
        elif path_obj.is_dir():
            # Hash all files in directory
            for file_path in sorted(path_obj.rglob('*')):
                if file_path.is_file():
                    hasher.update(str(file_path).encode())
                    with open(file_path, 'rb') as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hasher.update(chunk)
        
        return hasher.hexdigest()


class SandboxContext:
    """Context manager for plugin sandbox execution"""
    
    def __init__(self, container, plugin_id: str):
        self.container = container
        self.plugin_id = plugin_id
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            self.container.stop()
            self.container.remove()
        except Exception as e:
            logger.error(f"Error cleaning up sandbox for {self.plugin_id}: {str(e)}")


@dataclass
class ExecutionResult:
    """Result of plugin execution in sandbox"""
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    resource_usage: Optional[Dict[str, Any]] = None


class PluginSandboxManager:
    """Manages Docker-based plugin sandboxing"""
    
    def __init__(self, docker_client: Optional[docker.DockerClient] = None):
        """Initialize sandbox manager"""
        self.docker_client = docker_client or docker.from_env()
        self.sandbox_image = "python:3.10-slim"
        
    async def create_sandbox(self, plugin_id: str) -> SandboxContext:
        """Create isolated execution environment for plugin"""
        container_name = f"plugin-sandbox-{plugin_id}"
        
        # Security configuration
        security_opts = [
            "no-new-privileges:true",
            "seccomp:default"
        ]
        
        # Resource limits
        resource_limits = {
            'mem_limit': '512m',
            'cpu_quota': 50000,  # 50% of one CPU
            'cpu_period': 100000,
            'pids_limit': 100,
            'ulimits': [
                docker.types.Ulimit(name='nofile', soft=1024, hard=1024),
                docker.types.Ulimit(name='nproc', soft=50, hard=50)
            ]
        }
        
        # Network isolation - no network access by default
        network_config = {
            'network_mode': 'none'
        }
        
        # Create temporary workspace
        workspace_path = f"/tmp/plugin-workspace-{plugin_id}"
        
        try:
            container = self.docker_client.containers.run(
                self.sandbox_image,
                name=container_name,
                detach=True,
                security_opt=security_opts,
                **resource_limits,
                **network_config,
                volumes={
                    workspace_path: {'bind': '/workspace', 'mode': 'rw'}
                },
                working_dir='/workspace',
                command='sleep 3600'  # Keep container alive
            )
            
            logger.info(f"Created sandbox container {container_name} for plugin {plugin_id}")
            return SandboxContext(container, plugin_id)
            
        except Exception as e:
            logger.error(f"Failed to create sandbox for plugin {plugin_id}: {str(e)}")
            raise
    
    async def execute_in_sandbox(
        self, 
        sandbox: SandboxContext, 
        code: str, 
        timeout: int = 30
    ) -> ExecutionResult:
        """Execute code in sandboxed environment"""
        import time
        
        start_time = time.time()
        
        try:
            # Create temporary Python file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Copy file to container
            with open(temp_file, 'rb') as f:
                data = f.read()
            
            # Put file in container
            import tarfile
            import io
            
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                tarinfo = tarfile.TarInfo(name='plugin_code.py')
                tarinfo.size = len(data)
                tar.addfile(tarinfo, io.BytesIO(data))
            
            tar_stream.seek(0)
            sandbox.container.put_archive('/workspace/', tar_stream)
            
            # Execute with timeout
            exec_result = sandbox.container.exec_run(
                "python /workspace/plugin_code.py",
                timeout=timeout,
                demux=True
            )
            
            execution_time = time.time() - start_time
            
            # Get resource usage stats
            stats = sandbox.container.stats(stream=False)
            resource_usage = {
                'memory_usage': stats.get('memory_stats', {}).get('usage', 0),
                'cpu_usage': stats.get('cpu_stats', {}).get('cpu_usage', {}).get('total_usage', 0)
            }
            
            stdout = exec_result.output[0].decode('utf-8') if exec_result.output[0] else ""
            stderr = exec_result.output[1].decode('utf-8') if exec_result.output[1] else ""
            
            return ExecutionResult(
                exit_code=exec_result.exit_code,
                stdout=stdout,
                stderr=stderr,
                execution_time=execution_time,
                resource_usage=resource_usage
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Sandbox execution failed: {str(e)}")
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                execution_time=execution_time
            )
        finally:
            # Cleanup temporary file
            if 'temp_file' in locals():
                Path(temp_file).unlink(missing_ok=True)
    
    async def test_plugin_isolation(self, plugin_id: str) -> ValidationResult:
        """Test that plugin cannot escape sandbox"""
        threats = []
        score = 100.0
        
        try:
            sandbox = await self.create_sandbox(plugin_id)
            
            # Test various escape attempts
            escape_tests = [
                # Try to access host filesystem
                "import os; print(os.listdir('/'))",
                # Try to access network
                "import socket; s = socket.socket(); s.connect(('google.com', 80))",
                # Try to execute system commands
                "import subprocess; subprocess.run(['ls', '/etc'])",
                # Try to access environment variables
                "import os; print(os.environ)",
                # Try to write outside workspace
                "with open('/etc/passwd', 'w') as f: f.write('hacked')"
            ]
            
            async with sandbox:
                for i, test_code in enumerate(escape_tests):
                    result = await self.execute_in_sandbox(sandbox, test_code, timeout=10)
                    
                    # If any escape attempt succeeds, it's a critical threat
                    if result.exit_code == 0 and not result.stderr:
                        threats.append(SecurityThreat(
                            threat_type=ThreatType.MALICIOUS_CODE,
                            level=ThreatLevel.CRITICAL,
                            description=f"Sandbox escape possible: test {i+1} succeeded"
                        ))
                        score = 0
        
        except Exception as e:
            logger.error(f"Isolation test failed: {str(e)}")
            threats.append(SecurityThreat(
                threat_type=ThreatType.MALICIOUS_CODE,
                level=ThreatLevel.HIGH,
                description=f"Isolation test error: {str(e)}"
            ))
            score = 50
        
        is_valid = len(threats) == 0
        return ValidationResult(is_valid=is_valid, threats=threats, score=score)