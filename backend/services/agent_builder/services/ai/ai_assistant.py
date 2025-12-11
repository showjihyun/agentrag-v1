"""
AI Assistant Service for Workflow Development

Provides AI-powered assistance for:
- Automatic error diagnosis
- Smart breakpoint suggestions
- Predictive bottleneck detection
- Natural language debugging queries
- Code optimization recommendations
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
import re
import json

from backend.services.llm_manager import LLMManager
from backend.services.agent_builder.workflow_debugger import (
    WorkflowDebugger,
    ExecutionState,
)


@dataclass
class ErrorDiagnosis:
    """AI-generated error diagnosis"""
    error_type: str
    root_cause: str
    explanation: str
    suggested_fixes: List[str]
    related_nodes: List[str]
    confidence: float  # 0.0 to 1.0


@dataclass
class BreakpointSuggestion:
    """AI-suggested breakpoint"""
    node_id: str
    reason: str
    priority: str  # high, medium, low
    condition: Optional[str] = None


@dataclass
class OptimizationSuggestion:
    """AI-generated optimization suggestion"""
    node_id: str
    issue: str
    suggestion: str
    expected_improvement: str
    implementation_difficulty: str  # easy, medium, hard
    code_example: Optional[str] = None


class AIAssistant:
    """
    AI-powered assistant for workflow development
    
    Features:
    - Automatic error diagnosis with root cause analysis
    - Smart breakpoint suggestions based on execution patterns
    - Predictive bottleneck detection
    - Natural language debugging queries
    - Code optimization recommendations
    """
    
    def __init__(self, llm_manager: Optional[LLMManager] = None):
        self.llm_manager = llm_manager or LLMManager()
        
    async def diagnose_error(
        self,
        error_message: str,
        execution_state: ExecutionState,
        workflow_context: Dict[str, Any]
    ) -> ErrorDiagnosis:
        """
        Diagnose error using AI
        
        Args:
            error_message: The error message
            execution_state: Current execution state
            workflow_context: Workflow metadata and context
            
        Returns:
            ErrorDiagnosis with root cause and fixes
        """
        # Build prompt for LLM
        prompt = self._build_error_diagnosis_prompt(
            error_message,
            execution_state,
            workflow_context
        )
        
        # Get AI response
        response = await self.llm_manager.generate_completion(
            prompt=prompt,
            temperature=0.3,  # Lower temperature for more focused responses
            max_tokens=1000
        )
        
        # Parse response
        diagnosis = self._parse_error_diagnosis(response)
        
        return diagnosis
        
    def _build_error_diagnosis_prompt(
        self,
        error_message: str,
        execution_state: ExecutionState,
        workflow_context: Dict[str, Any]
    ) -> str:
        """Build prompt for error diagnosis"""
        return f"""You are an expert workflow debugger. Analyze this error and provide a diagnosis.

**Error Message:**
{error_message}

**Node Information:**
- Node ID: {execution_state.node_id}
- Status: {execution_state.status}
- Duration: {execution_state.duration_ms}ms

**Input Data:**
{json.dumps(execution_state.input_data, indent=2) if execution_state.input_data else 'None'}

**Workflow Context:**
{json.dumps(workflow_context, indent=2)}

Please provide:
1. **Error Type**: Classification of the error
2. **Root Cause**: The underlying cause of the error
3. **Explanation**: Detailed explanation of what went wrong
4. **Suggested Fixes**: 3-5 specific fixes to resolve the issue
5. **Related Nodes**: Other nodes that might be affected
6. **Confidence**: Your confidence level (0.0 to 1.0)

Format your response as JSON:
{{
    "error_type": "...",
    "root_cause": "...",
    "explanation": "...",
    "suggested_fixes": ["...", "..."],
    "related_nodes": ["...", "..."],
    "confidence": 0.85
}}
"""
        
    def _parse_error_diagnosis(self, response: str) -> ErrorDiagnosis:
        """Parse AI response into ErrorDiagnosis"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                # Fallback parsing
                data = {
                    "error_type": "Unknown",
                    "root_cause": "Unable to determine",
                    "explanation": response,
                    "suggested_fixes": ["Review error message and logs"],
                    "related_nodes": [],
                    "confidence": 0.5
                }
                
            return ErrorDiagnosis(
                error_type=data.get("error_type", "Unknown"),
                root_cause=data.get("root_cause", "Unable to determine"),
                explanation=data.get("explanation", ""),
                suggested_fixes=data.get("suggested_fixes", []),
                related_nodes=data.get("related_nodes", []),
                confidence=float(data.get("confidence", 0.5))
            )
        except Exception as e:
            # Fallback diagnosis
            return ErrorDiagnosis(
                error_type="Parse Error",
                root_cause="Failed to parse AI response",
                explanation=str(e),
                suggested_fixes=["Review error manually"],
                related_nodes=[],
                confidence=0.3
            )
            
    async def suggest_breakpoints(
        self,
        debugger: WorkflowDebugger,
        workflow_context: Dict[str, Any]
    ) -> List[BreakpointSuggestion]:
        """
        Suggest smart breakpoints based on execution history
        
        Args:
            debugger: WorkflowDebugger instance
            workflow_context: Workflow metadata
            
        Returns:
            List of breakpoint suggestions
        """
        # Analyze execution history
        execution_history = debugger.execution_history
        
        if not execution_history:
            return []
            
        # Build prompt
        prompt = self._build_breakpoint_suggestion_prompt(
            execution_history,
            workflow_context
        )
        
        # Get AI response
        response = await self.llm_manager.generate_completion(
            prompt=prompt,
            temperature=0.4,
            max_tokens=800
        )
        
        # Parse suggestions
        suggestions = self._parse_breakpoint_suggestions(response)
        
        return suggestions
        
    def _build_breakpoint_suggestion_prompt(
        self,
        execution_history: List[ExecutionState],
        workflow_context: Dict[str, Any]
    ) -> str:
        """Build prompt for breakpoint suggestions"""
        # Summarize execution history
        error_nodes = [
            state.node_id for state in execution_history
            if state.status.value == "error"
        ]
        slow_nodes = [
            state.node_id for state in execution_history
            if state.duration_ms and state.duration_ms > 1000
        ]
        
        return f"""You are an expert workflow debugger. Suggest strategic breakpoints for debugging.

**Execution History Summary:**
- Total executions: {len(execution_history)}
- Nodes with errors: {error_nodes}
- Slow nodes (>1s): {slow_nodes}

**Workflow Context:**
{json.dumps(workflow_context, indent=2)}

Suggest 3-5 strategic breakpoints that would help debug issues. For each breakpoint:
1. **Node ID**: Which node to set breakpoint on
2. **Reason**: Why this breakpoint would be helpful
3. **Priority**: high, medium, or low
4. **Condition**: Optional condition (e.g., "input['value'] > 100")

Format as JSON array:
[
    {{
        "node_id": "...",
        "reason": "...",
        "priority": "high",
        "condition": "..."
    }}
]
"""
        
    def _parse_breakpoint_suggestions(
        self,
        response: str
    ) -> List[BreakpointSuggestion]:
        """Parse AI response into breakpoint suggestions"""
        try:
            # Extract JSON array
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                return []
                
            suggestions = []
            for item in data:
                suggestions.append(BreakpointSuggestion(
                    node_id=item.get("node_id", ""),
                    reason=item.get("reason", ""),
                    priority=item.get("priority", "medium"),
                    condition=item.get("condition")
                ))
                
            return suggestions
        except Exception:
            return []
            
    async def predict_bottlenecks(
        self,
        debugger: WorkflowDebugger,
        workflow_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Predict potential bottlenecks before they occur
        
        Args:
            debugger: WorkflowDebugger instance
            workflow_context: Workflow metadata
            
        Returns:
            List of predicted bottlenecks
        """
        # Get performance metrics
        metrics = debugger.get_performance_metrics()
        
        # Build prompt
        prompt = f"""You are a performance optimization expert. Predict potential bottlenecks.

**Current Performance Metrics:**
- Total Duration: {metrics['total_duration_ms']}ms
- Average Duration: {metrics['avg_duration_ms']}ms
- Success Rate: {metrics['success_rate']}%
- Error Rate: {metrics['error_rate']}%

**Node Metrics:**
{json.dumps(metrics['node_metrics'], indent=2)}

**Workflow Context:**
{json.dumps(workflow_context, indent=2)}

Predict 3-5 potential bottlenecks that might occur as the workflow scales. For each:
1. **Node ID**: Which node might become a bottleneck
2. **Risk Level**: high, medium, or low
3. **Reason**: Why this might become a bottleneck
4. **Mitigation**: How to prevent or mitigate it

Format as JSON array.
"""
        
        response = await self.llm_manager.generate_completion(
            prompt=prompt,
            temperature=0.4,
            max_tokens=1000
        )
        
        # Parse predictions
        try:
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass
            
        return []
        
    async def answer_debug_query(
        self,
        query: str,
        debugger: WorkflowDebugger,
        workflow_context: Dict[str, Any]
    ) -> str:
        """
        Answer natural language debugging queries
        
        Args:
            query: User's question in natural language
            debugger: WorkflowDebugger instance
            workflow_context: Workflow metadata
            
        Returns:
            AI-generated answer
        """
        # Get current state
        current_state = debugger.get_current_state()
        metrics = debugger.get_performance_metrics()
        
        # Build prompt
        prompt = f"""You are a helpful workflow debugging assistant. Answer the user's question.

**User Question:**
{query}

**Current Workflow State:**
{json.dumps({
    'current_node': current_state.node_id if current_state else None,
    'status': current_state.status.value if current_state else None,
    'metrics': metrics,
    'context': workflow_context
}, indent=2)}

**Execution History:**
{len(debugger.execution_history)} executions recorded

Provide a clear, concise answer to the user's question. If you need more information, suggest what to check.
"""
        
        response = await self.llm_manager.generate_completion(
            prompt=prompt,
            temperature=0.5,
            max_tokens=500
        )
        
        return response.strip()
        
    async def suggest_optimizations(
        self,
        debugger: WorkflowDebugger,
        workflow_context: Dict[str, Any]
    ) -> List[OptimizationSuggestion]:
        """
        Suggest code optimizations for workflow nodes
        
        Args:
            debugger: WorkflowDebugger instance
            workflow_context: Workflow metadata
            
        Returns:
            List of optimization suggestions
        """
        # Get bottlenecks
        bottlenecks = debugger.identify_bottlenecks(threshold_percent=15.0)
        
        if not bottlenecks:
            return []
            
        # Build prompt
        prompt = f"""You are a code optimization expert. Suggest optimizations for these bottleneck nodes.

**Bottlenecks:**
{json.dumps(bottlenecks, indent=2)}

**Workflow Context:**
{json.dumps(workflow_context, indent=2)}

For each bottleneck, suggest specific optimizations:
1. **Node ID**: The node to optimize
2. **Issue**: What's causing the slowdown
3. **Suggestion**: Specific optimization technique
4. **Expected Improvement**: Estimated performance gain
5. **Implementation Difficulty**: easy, medium, or hard
6. **Code Example**: Optional code snippet

Format as JSON array.
"""
        
        response = await self.llm_manager.generate_completion(
            prompt=prompt,
            temperature=0.4,
            max_tokens=1500
        )
        
        # Parse suggestions
        suggestions = []
        try:
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                for item in data:
                    suggestions.append(OptimizationSuggestion(
                        node_id=item.get("node_id", ""),
                        issue=item.get("issue", ""),
                        suggestion=item.get("suggestion", ""),
                        expected_improvement=item.get("expected_improvement", ""),
                        implementation_difficulty=item.get("implementation_difficulty", "medium"),
                        code_example=item.get("code_example")
                    ))
        except Exception:
            pass
            
        return suggestions
        
    async def explain_execution_flow(
        self,
        debugger: WorkflowDebugger,
        workflow_context: Dict[str, Any]
    ) -> str:
        """
        Generate natural language explanation of execution flow
        
        Args:
            debugger: WorkflowDebugger instance
            workflow_context: Workflow metadata
            
        Returns:
            Human-readable explanation
        """
        execution_history = debugger.execution_history[-10:]  # Last 10 executions
        
        prompt = f"""You are a workflow documentation expert. Explain the execution flow in simple terms.

**Recent Execution History:**
{json.dumps([
    {{
        'node': state.node_id,
        'status': state.status.value,
        'duration': f"{state.duration_ms}ms" if state.duration_ms else None,
        'error': state.error
    }}
    for state in execution_history
], indent=2)}

**Workflow Context:**
{json.dumps(workflow_context, indent=2)}

Provide a clear, step-by-step explanation of what happened during execution. Use simple language that a non-technical person could understand.
"""
        
        response = await self.llm_manager.generate_completion(
            prompt=prompt,
            temperature=0.6,
            max_tokens=800
        )
        
        return response.strip()
