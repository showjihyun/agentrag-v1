"""
Advanced Error Recovery System for Agent Orchestration

Provides intelligent error handling, recovery strategies, and fallback mechanisms
for robust agent workflow execution.
"""

import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import traceback

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Classification of error types for targeted recovery strategies."""
    TRANSIENT = "transient"  # Temporary network/service issues
    RESOURCE_EXHAUSTION = "resource_exhaustion"  # Memory, CPU, rate limits
    CONFIGURATION = "configuration"  # Invalid parameters, missing keys
    DEPENDENCY = "dependency"  # External service unavailable
    LOGIC = "logic"  # Business logic errors
    TIMEOUT = "timeout"  # Operation timeout
    AUTHENTICATION = "authentication"  # Auth/permission issues
    UNKNOWN = "unknown"  # Unclassified errors


class RecoveryStrategy(Enum):
    """Available recovery strategies."""
    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    SCALE_DOWN = "scale_down"
    RECONFIGURE = "reconfigure"
    ABORT = "abort"


@dataclass
class ErrorPattern:
    """Pattern for error classification and recovery."""
    error_type: ErrorType
    keywords: List[str]
    recovery_strategy: RecoveryStrategy
    max_retries: int = 3
    backoff_multiplier: float = 2.0
    confidence: float = 0.8


@dataclass
class RecoveryAction:
    """Specific recovery action to be taken."""
    strategy: RecoveryStrategy
    parameters: Dict[str, Any]
    estimated_success_rate: float
    execution_time_estimate: float
    description: str


@dataclass
class ErrorContext:
    """Context information for error analysis."""
    agent_id: str
    agent_name: str
    error: Exception
    error_message: str
    stack_trace: str
    timestamp: datetime
    execution_context: Dict[str, Any]
    retry_count: int = 0
    previous_errors: List['ErrorContext'] = None


class CircuitBreaker:
    """Circuit breaker pattern implementation for agent reliability."""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        return (
            self.last_failure_time and 
            datetime.now() - self.last_failure_time >= timedelta(seconds=self.recovery_timeout)
        )
    
    def _on_success(self):
        """Handle successful execution."""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def _on_failure(self):
        """Handle failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'


class AgentErrorRecovery:
    """
    Advanced error recovery system for agent orchestration.
    
    Features:
    - Intelligent error classification
    - Adaptive recovery strategies
    - Circuit breaker pattern
    - Fallback workflow generation
    - Error pattern learning
    """
    
    def __init__(self):
        """Initialize the error recovery system."""
        self.error_patterns = self._initialize_error_patterns()
        self.circuit_breakers = {}  # agent_id -> CircuitBreaker
        self.error_history = []
        self.recovery_stats = {
            'total_errors': 0,
            'successful_recoveries': 0,
            'failed_recoveries': 0,
            'recovery_strategies_used': {},
        }
        
        logger.info("AgentErrorRecovery initialized")
    
    def _initialize_error_patterns(self) -> List[ErrorPattern]:
        """Initialize predefined error patterns."""
        return [
            # Transient errors
            ErrorPattern(
                error_type=ErrorType.TRANSIENT,
                keywords=['connection', 'timeout', 'network', 'temporary', 'unavailable'],
                recovery_strategy=RecoveryStrategy.RETRY,
                max_retries=3,
                backoff_multiplier=2.0,
                confidence=0.9
            ),
            
            # Resource exhaustion
            ErrorPattern(
                error_type=ErrorType.RESOURCE_EXHAUSTION,
                keywords=['memory', 'cpu', 'rate limit', 'quota', 'throttle'],
                recovery_strategy=RecoveryStrategy.SCALE_DOWN,
                max_retries=2,
                backoff_multiplier=3.0,
                confidence=0.8
            ),
            
            # Configuration errors
            ErrorPattern(
                error_type=ErrorType.CONFIGURATION,
                keywords=['invalid', 'missing', 'config', 'parameter', 'key'],
                recovery_strategy=RecoveryStrategy.RECONFIGURE,
                max_retries=1,
                confidence=0.9
            ),
            
            # Authentication errors
            ErrorPattern(
                error_type=ErrorType.AUTHENTICATION,
                keywords=['auth', 'permission', 'unauthorized', 'forbidden', 'token'],
                recovery_strategy=RecoveryStrategy.RECONFIGURE,
                max_retries=2,
                confidence=0.95
            ),
            
            # Dependency errors
            ErrorPattern(
                error_type=ErrorType.DEPENDENCY,
                keywords=['service', 'api', 'external', 'dependency', 'unavailable'],
                recovery_strategy=RecoveryStrategy.FALLBACK,
                max_retries=2,
                confidence=0.8
            ),
            
            # Timeout errors
            ErrorPattern(
                error_type=ErrorType.TIMEOUT,
                keywords=['timeout', 'deadline', 'expired'],
                recovery_strategy=RecoveryStrategy.RETRY,
                max_retries=2,
                backoff_multiplier=1.5,
                confidence=0.9
            ),
        ]
    
    async def handle_error(self, 
                          agent_id: str,
                          agent_name: str,
                          error: Exception,
                          execution_context: Dict[str, Any]) -> RecoveryAction:
        """
        Handle an agent error and determine recovery action.
        
        Args:
            agent_id: ID of the failed agent
            agent_name: Name of the failed agent
            error: The exception that occurred
            execution_context: Context of the execution
            
        Returns:
            Recovery action to be taken
        """
        # Create error context
        error_context = ErrorContext(
            agent_id=agent_id,
            agent_name=agent_name,
            error=error,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            timestamp=datetime.now(),
            execution_context=execution_context,
            retry_count=execution_context.get('retry_count', 0)
        )
        
        # Update statistics
        self.recovery_stats['total_errors'] += 1
        self.error_history.append(error_context)
        
        # Keep only recent error history
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-500:]
        
        logger.error(f"Error in agent {agent_name} ({agent_id}): {error}")
        
        # Classify error and determine recovery strategy
        error_type, pattern = self._classify_error(error_context)
        recovery_action = await self._determine_recovery_action(error_context, pattern)
        
        # Update recovery statistics
        strategy_name = recovery_action.strategy.value
        if strategy_name not in self.recovery_stats['recovery_strategies_used']:
            self.recovery_stats['recovery_strategies_used'][strategy_name] = 0
        self.recovery_stats['recovery_strategies_used'][strategy_name] += 1
        
        logger.info(f"Recovery strategy for {agent_name}: {recovery_action.strategy.value}")
        
        return recovery_action
    
    def _classify_error(self, error_context: ErrorContext) -> tuple[ErrorType, Optional[ErrorPattern]]:
        """Classify error type based on error message and patterns."""
        error_message = error_context.error_message.lower()
        
        # Find matching pattern
        best_match = None
        best_score = 0
        
        for pattern in self.error_patterns:
            score = 0
            for keyword in pattern.keywords:
                if keyword.lower() in error_message:
                    score += 1
            
            # Normalize score by number of keywords
            normalized_score = score / len(pattern.keywords) if pattern.keywords else 0
            
            if normalized_score > best_score and normalized_score >= 0.3:  # Minimum 30% match
                best_score = normalized_score
                best_match = pattern
        
        if best_match:
            return best_match.error_type, best_match
        else:
            # Check for specific exception types
            if isinstance(error_context.error, (ConnectionError, TimeoutError)):
                return ErrorType.TRANSIENT, None
            elif isinstance(error_context.error, MemoryError):
                return ErrorType.RESOURCE_EXHAUSTION, None
            elif isinstance(error_context.error, (ValueError, KeyError)):
                return ErrorType.CONFIGURATION, None
            else:
                return ErrorType.UNKNOWN, None
    
    async def _determine_recovery_action(self, 
                                       error_context: ErrorContext,
                                       pattern: Optional[ErrorPattern]) -> RecoveryAction:
        """Determine the best recovery action for the error."""
        
        if pattern:
            strategy = pattern.recovery_strategy
            max_retries = pattern.max_retries
        else:
            # Default strategy for unknown errors
            strategy = RecoveryStrategy.RETRY
            max_retries = 2
        
        # Check retry limits
        if error_context.retry_count >= max_retries:
            if strategy == RecoveryStrategy.RETRY:
                strategy = RecoveryStrategy.FALLBACK
            elif strategy == RecoveryStrategy.FALLBACK:
                strategy = RecoveryStrategy.SKIP
            elif strategy == RecoveryStrategy.SKIP:
                strategy = RecoveryStrategy.ABORT
        
        # Generate recovery action based on strategy
        if strategy == RecoveryStrategy.RETRY:
            return await self._create_retry_action(error_context, pattern)
        elif strategy == RecoveryStrategy.FALLBACK:
            return await self._create_fallback_action(error_context)
        elif strategy == RecoveryStrategy.SKIP:
            return await self._create_skip_action(error_context)
        elif strategy == RecoveryStrategy.SCALE_DOWN:
            return await self._create_scale_down_action(error_context)
        elif strategy == RecoveryStrategy.RECONFIGURE:
            return await self._create_reconfigure_action(error_context)
        else:  # ABORT
            return await self._create_abort_action(error_context)
    
    async def _create_retry_action(self, 
                                 error_context: ErrorContext,
                                 pattern: Optional[ErrorPattern]) -> RecoveryAction:
        """Create retry recovery action."""
        backoff_multiplier = pattern.backoff_multiplier if pattern else 2.0
        delay = min(60, (backoff_multiplier ** error_context.retry_count))  # Max 60 seconds
        
        return RecoveryAction(
            strategy=RecoveryStrategy.RETRY,
            parameters={
                'delay_seconds': delay,
                'retry_count': error_context.retry_count + 1,
                'modified_params': self._suggest_parameter_modifications(error_context)
            },
            estimated_success_rate=max(0.1, 0.8 - (error_context.retry_count * 0.2)),
            execution_time_estimate=delay + 30,  # Delay + estimated execution time
            description=f"재시도 #{error_context.retry_count + 1} ({delay:.1f}초 후)"
        )
    
    async def _create_fallback_action(self, error_context: ErrorContext) -> RecoveryAction:
        """Create fallback recovery action."""
        fallback_agent = self._suggest_fallback_agent(error_context)
        
        return RecoveryAction(
            strategy=RecoveryStrategy.FALLBACK,
            parameters={
                'fallback_agent': fallback_agent,
                'simplified_params': self._simplify_parameters(error_context.execution_context),
                'fallback_workflow': await self._generate_fallback_workflow(error_context)
            },
            estimated_success_rate=0.6,
            execution_time_estimate=45,
            description=f"대체 에이전트 사용: {fallback_agent}"
        )
    
    async def _create_skip_action(self, error_context: ErrorContext) -> RecoveryAction:
        """Create skip recovery action."""
        return RecoveryAction(
            strategy=RecoveryStrategy.SKIP,
            parameters={
                'skip_reason': f"에이전트 {error_context.agent_name} 실행 실패",
                'default_output': self._generate_default_output(error_context)
            },
            estimated_success_rate=1.0,  # Always succeeds by definition
            execution_time_estimate=1,
            description=f"에이전트 {error_context.agent_name} 건너뛰기"
        )
    
    async def _create_scale_down_action(self, error_context: ErrorContext) -> RecoveryAction:
        """Create scale down recovery action."""
        return RecoveryAction(
            strategy=RecoveryStrategy.SCALE_DOWN,
            parameters={
                'reduce_concurrency': True,
                'reduce_batch_size': True,
                'increase_timeout': True,
                'new_concurrency': max(1, error_context.execution_context.get('concurrency', 3) // 2)
            },
            estimated_success_rate=0.7,
            execution_time_estimate=60,
            description="리소스 사용량 감소 후 재시도"
        )
    
    async def _create_reconfigure_action(self, error_context: ErrorContext) -> RecoveryAction:
        """Create reconfigure recovery action."""
        suggested_config = await self._suggest_configuration_fix(error_context)
        
        return RecoveryAction(
            strategy=RecoveryStrategy.RECONFIGURE,
            parameters={
                'suggested_config': suggested_config,
                'config_changes': self._identify_config_issues(error_context)
            },
            estimated_success_rate=0.8,
            execution_time_estimate=30,
            description="설정 수정 후 재시도"
        )
    
    async def _create_abort_action(self, error_context: ErrorContext) -> RecoveryAction:
        """Create abort recovery action."""
        return RecoveryAction(
            strategy=RecoveryStrategy.ABORT,
            parameters={
                'abort_reason': f"복구 불가능한 오류: {error_context.error_message}",
                'error_details': {
                    'error_type': str(type(error_context.error).__name__),
                    'error_message': error_context.error_message,
                    'retry_count': error_context.retry_count
                }
            },
            estimated_success_rate=0.0,
            execution_time_estimate=1,
            description="워크플로우 중단"
        )
    
    def _suggest_parameter_modifications(self, error_context: ErrorContext) -> Dict[str, Any]:
        """Suggest parameter modifications for retry."""
        modifications = {}
        
        # Increase timeout for timeout errors
        if 'timeout' in error_context.error_message.lower():
            current_timeout = error_context.execution_context.get('timeout', 30)
            modifications['timeout'] = min(300, current_timeout * 2)
        
        # Reduce batch size for resource errors
        if any(keyword in error_context.error_message.lower() 
               for keyword in ['memory', 'resource', 'limit']):
            current_batch = error_context.execution_context.get('batch_size', 10)
            modifications['batch_size'] = max(1, current_batch // 2)
        
        return modifications
    
    def _suggest_fallback_agent(self, error_context: ErrorContext) -> str:
        """Suggest a fallback agent based on the failed agent."""
        agent_name = error_context.agent_name.lower()
        
        # Simple fallback mapping
        fallback_map = {
            'vector_search': 'local_data',
            'web_search': 'vector_search',
            'local_data': 'vector_search',
            'llm_agent': 'simple_llm_agent'
        }
        
        for key, fallback in fallback_map.items():
            if key in agent_name:
                return fallback
        
        return 'basic_agent'  # Default fallback
    
    def _simplify_parameters(self, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Simplify parameters for fallback execution."""
        simplified = execution_context.copy()
        
        # Reduce complexity
        simplified['limit'] = min(simplified.get('limit', 5), 3)
        simplified['max_depth'] = min(simplified.get('max_depth', 3), 2)
        simplified['timeout'] = min(simplified.get('timeout', 30), 15)
        
        return simplified
    
    async def _generate_fallback_workflow(self, error_context: ErrorContext) -> Dict[str, Any]:
        """Generate a simplified fallback workflow."""
        return {
            'type': 'simplified_workflow',
            'agents': [
                {
                    'name': self._suggest_fallback_agent(error_context),
                    'parameters': self._simplify_parameters(error_context.execution_context)
                }
            ],
            'execution_mode': 'sequential',
            'error_tolerance': 'high'
        }
    
    def _generate_default_output(self, error_context: ErrorContext) -> Dict[str, Any]:
        """Generate default output when skipping an agent."""
        return {
            'status': 'skipped',
            'reason': f"Agent {error_context.agent_name} failed and was skipped",
            'error': error_context.error_message,
            'timestamp': error_context.timestamp.isoformat(),
            'default_result': {
                'message': 'This agent was skipped due to an error',
                'confidence': 0.0,
                'results': []
            }
        }
    
    async def _suggest_configuration_fix(self, error_context: ErrorContext) -> Dict[str, Any]:
        """Suggest configuration fixes based on error analysis."""
        suggestions = {}
        error_msg = error_context.error_message.lower()
        
        # API key issues
        if any(keyword in error_msg for keyword in ['api key', 'authentication', 'unauthorized']):
            suggestions['check_api_keys'] = True
            suggestions['refresh_tokens'] = True
        
        # Parameter validation issues
        if any(keyword in error_msg for keyword in ['invalid', 'missing', 'required']):
            suggestions['validate_parameters'] = True
            suggestions['use_default_values'] = True
        
        # Rate limit issues
        if 'rate limit' in error_msg or 'throttle' in error_msg:
            suggestions['add_rate_limiting'] = True
            suggestions['increase_delays'] = True
        
        return suggestions
    
    def _identify_config_issues(self, error_context: ErrorContext) -> List[str]:
        """Identify specific configuration issues."""
        issues = []
        error_msg = error_context.error_message.lower()
        
        if 'api key' in error_msg:
            issues.append('Invalid or missing API key')
        if 'timeout' in error_msg:
            issues.append('Timeout value too low')
        if 'parameter' in error_msg:
            issues.append('Invalid parameter values')
        if 'permission' in error_msg:
            issues.append('Insufficient permissions')
        
        return issues
    
    def get_circuit_breaker(self, agent_id: str) -> CircuitBreaker:
        """Get or create circuit breaker for an agent."""
        if agent_id not in self.circuit_breakers:
            self.circuit_breakers[agent_id] = CircuitBreaker()
        return self.circuit_breakers[agent_id]
    
    async def execute_with_recovery(self, 
                                  agent_id: str,
                                  agent_name: str,
                                  execution_func: Callable,
                                  execution_context: Dict[str, Any],
                                  *args, **kwargs) -> Any:
        """
        Execute a function with automatic error recovery.
        
        Args:
            agent_id: ID of the agent
            agent_name: Name of the agent
            execution_func: Function to execute
            execution_context: Execution context
            *args, **kwargs: Arguments for the function
            
        Returns:
            Result of the execution or recovery action
        """
        circuit_breaker = self.get_circuit_breaker(agent_id)
        max_recovery_attempts = 3
        recovery_attempt = 0
        
        while recovery_attempt < max_recovery_attempts:
            try:
                # Execute with circuit breaker protection
                result = await circuit_breaker.call(execution_func, *args, **kwargs)
                
                # Success - update statistics
                if recovery_attempt > 0:
                    self.recovery_stats['successful_recoveries'] += 1
                
                return result
                
            except Exception as error:
                recovery_attempt += 1
                
                # Handle the error
                recovery_action = await self.handle_error(
                    agent_id, agent_name, error, execution_context
                )
                
                # Execute recovery action
                if recovery_action.strategy == RecoveryStrategy.RETRY:
                    # Wait before retry
                    delay = recovery_action.parameters.get('delay_seconds', 1)
                    await asyncio.sleep(delay)
                    
                    # Update execution context with modifications
                    modifications = recovery_action.parameters.get('modified_params', {})
                    execution_context.update(modifications)
                    execution_context['retry_count'] = recovery_action.parameters.get('retry_count', 1)
                    
                    continue  # Retry the execution
                    
                elif recovery_action.strategy == RecoveryStrategy.FALLBACK:
                    # Execute fallback workflow
                    fallback_workflow = recovery_action.parameters.get('fallback_workflow')
                    if fallback_workflow:
                        # This would integrate with the workflow executor
                        logger.info(f"Executing fallback workflow for {agent_name}")
                        return {'status': 'fallback_executed', 'workflow': fallback_workflow}
                    
                elif recovery_action.strategy == RecoveryStrategy.SKIP:
                    # Return default output
                    default_output = recovery_action.parameters.get('default_output')
                    logger.info(f"Skipping agent {agent_name}")
                    return default_output
                    
                elif recovery_action.strategy == RecoveryStrategy.ABORT:
                    # Re-raise the error to abort execution
                    self.recovery_stats['failed_recoveries'] += 1
                    raise error
                    
                else:
                    # For other strategies, try once more with modified parameters
                    if recovery_attempt < max_recovery_attempts:
                        continue
                    else:
                        self.recovery_stats['failed_recoveries'] += 1
                        raise error
        
        # If we've exhausted all recovery attempts
        self.recovery_stats['failed_recoveries'] += 1
        raise Exception(f"Failed to recover from error in {agent_name} after {max_recovery_attempts} attempts")
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """Get error recovery statistics."""
        total_errors = self.recovery_stats['total_errors']
        successful_recoveries = self.recovery_stats['successful_recoveries']
        
        return {
            **self.recovery_stats,
            'recovery_success_rate': successful_recoveries / total_errors if total_errors > 0 else 0,
            'recent_errors': len([e for e in self.error_history 
                                if e.timestamp > datetime.now() - timedelta(hours=24)]),
            'circuit_breaker_states': {
                agent_id: cb.state for agent_id, cb in self.circuit_breakers.items()
            }
        }
    
    def learn_from_error_patterns(self):
        """Learn and update error patterns from historical data."""
        # This would implement machine learning to improve error classification
        # For now, it's a placeholder for future enhancement
        logger.info("Error pattern learning not yet implemented")
        pass