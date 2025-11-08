"""Execution logging for workflows.

This module provides enhanced logging capabilities for workflow execution,
including detailed block execution logs, timing information, and cost tracking.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import traceback

from backend.core.execution.context import ExecutionContext

logger = logging.getLogger(__name__)


class ExecutionLogger:
    """
    Enhanced logger for workflow execution.
    
    Provides detailed logging of workflow execution including:
    - Block execution timing
    - Error tracking with stack traces
    - Token usage and cost calculation
    - File metadata tracking
    """
    
    @staticmethod
    def log_workflow_start(
        context: ExecutionContext,
        workflow_name: Optional[str] = None
    ):
        """
        Log workflow execution start.
        
        Args:
            context: Execution context
            workflow_name: Workflow name (optional)
        """
        logger.info(
            f"=== Workflow Execution Started ===\n"
            f"Workflow ID: {context.workflow_id}\n"
            f"Execution ID: {context.execution_id}\n"
            f"User ID: {context.user_id}\n"
            f"Trigger: {context.trigger}\n"
            f"Started At: {context.started_at.isoformat() if context.started_at else 'N/A'}\n"
            f"{'Workflow Name: ' + workflow_name if workflow_name else ''}"
        )
    
    @staticmethod
    def log_workflow_complete(
        context: ExecutionContext,
        workflow_name: Optional[str] = None
    ):
        """
        Log workflow execution completion.
        
        Args:
            context: Execution context
            workflow_name: Workflow name (optional)
        """
        duration_ms = None
        if context.started_at and context.completed_at:
            duration_ms = int(
                (context.completed_at - context.started_at).total_seconds() * 1000
            )
        
        # Count successful and failed blocks
        successful_blocks = sum(
            1 for state in context.block_states.values()
            if state.executed and state.success
        )
        failed_blocks = sum(
            1 for state in context.block_states.values()
            if state.executed and not state.success
        )
        
        logger.info(
            f"=== Workflow Execution Completed ===\n"
            f"Workflow ID: {context.workflow_id}\n"
            f"Execution ID: {context.execution_id}\n"
            f"Status: {context.status}\n"
            f"Duration: {duration_ms}ms\n"
            f"Blocks Executed: {successful_blocks + failed_blocks}\n"
            f"Successful: {successful_blocks}\n"
            f"Failed: {failed_blocks}\n"
            f"Total Tokens: {context.total_tokens}\n"
            f"Estimated Cost: ${context.estimated_cost:.4f}\n"
            f"{'Error: ' + context.error_message if context.error_message else ''}"
        )
    
    @staticmethod
    def log_block_start(
        block_id: str,
        block_type: str,
        block_name: str,
        inputs: Dict[str, Any]
    ):
        """
        Log block execution start.
        
        Args:
            block_id: Block identifier
            block_type: Block type
            block_name: Block name
            inputs: Block inputs
        """
        logger.info(
            f"--- Block Execution Started ---\n"
            f"Block ID: {block_id}\n"
            f"Block Type: {block_type}\n"
            f"Block Name: {block_name}\n"
            f"Inputs: {ExecutionLogger._format_data(inputs)}"
        )
    
    @staticmethod
    def log_block_complete(
        block_id: str,
        block_type: str,
        block_name: str,
        outputs: Dict[str, Any],
        duration_ms: int
    ):
        """
        Log block execution completion.
        
        Args:
            block_id: Block identifier
            block_type: Block type
            block_name: Block name
            outputs: Block outputs
            duration_ms: Execution duration in milliseconds
        """
        logger.info(
            f"--- Block Execution Completed ---\n"
            f"Block ID: {block_id}\n"
            f"Block Type: {block_type}\n"
            f"Block Name: {block_name}\n"
            f"Duration: {duration_ms}ms\n"
            f"Outputs: {ExecutionLogger._format_data(outputs)}"
        )
    
    @staticmethod
    def log_block_error(
        block_id: str,
        block_type: str,
        block_name: str,
        error: Exception,
        duration_ms: Optional[int] = None
    ):
        """
        Log block execution error with stack trace.
        
        Args:
            block_id: Block identifier
            block_type: Block type
            block_name: Block name
            error: Exception that occurred
            duration_ms: Execution duration in milliseconds (optional)
        """
        stack_trace = traceback.format_exc()
        
        logger.error(
            f"--- Block Execution Failed ---\n"
            f"Block ID: {block_id}\n"
            f"Block Type: {block_type}\n"
            f"Block Name: {block_name}\n"
            f"{'Duration: ' + str(duration_ms) + 'ms' if duration_ms else ''}\n"
            f"Error: {str(error)}\n"
            f"Stack Trace:\n{stack_trace}"
        )
    
    @staticmethod
    def log_token_usage(
        context: ExecutionContext,
        block_id: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float
    ):
        """
        Log token usage and cost for a block.
        
        Args:
            context: Execution context
            block_id: Block identifier
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            cost: Estimated cost
        """
        total_tokens = prompt_tokens + completion_tokens
        
        logger.info(
            f"Token Usage - Block {block_id}:\n"
            f"Prompt Tokens: {prompt_tokens}\n"
            f"Completion Tokens: {completion_tokens}\n"
            f"Total Tokens: {total_tokens}\n"
            f"Cost: ${cost:.4f}\n"
            f"Cumulative Total: {context.total_tokens} tokens, ${context.estimated_cost:.4f}"
        )
    
    @staticmethod
    def log_file_metadata(
        context: ExecutionContext,
        file_id: str,
        file_metadata: Dict[str, Any]
    ):
        """
        Log file metadata.
        
        Args:
            context: Execution context
            file_id: File identifier
            file_metadata: File metadata
        """
        logger.info(
            f"File Generated - {file_id}:\n"
            f"Metadata: {ExecutionLogger._format_data(file_metadata)}"
        )
    
    @staticmethod
    def log_condition_evaluation(
        block_id: str,
        selected_path: str,
        matched_condition: Optional[Dict[str, Any]] = None
    ):
        """
        Log condition evaluation result.
        
        Args:
            block_id: Condition block identifier
            selected_path: Selected path
            matched_condition: Condition that matched (optional)
        """
        logger.info(
            f"Condition Evaluation - Block {block_id}:\n"
            f"Selected Path: {selected_path}\n"
            f"{'Matched Condition: ' + str(matched_condition) if matched_condition else 'No condition matched (default path)'}"
        )
    
    @staticmethod
    def log_loop_iteration(
        block_id: str,
        iteration_index: int,
        total_iterations: int
    ):
        """
        Log loop iteration.
        
        Args:
            block_id: Loop block identifier
            iteration_index: Current iteration index
            total_iterations: Total number of iterations
        """
        logger.info(
            f"Loop Iteration - Block {block_id}:\n"
            f"Iteration: {iteration_index + 1}/{total_iterations}"
        )
    
    @staticmethod
    def log_parallel_branch(
        block_id: str,
        branch_index: int,
        total_branches: int,
        status: str = "started"
    ):
        """
        Log parallel branch execution.
        
        Args:
            block_id: Parallel block identifier
            branch_index: Branch index
            total_branches: Total number of branches
            status: Branch status ("started", "completed", "failed")
        """
        logger.info(
            f"Parallel Branch {status.capitalize()} - Block {block_id}:\n"
            f"Branch: {branch_index + 1}/{total_branches}"
        )
    
    @staticmethod
    def create_execution_summary(context: ExecutionContext) -> Dict[str, Any]:
        """
        Create execution summary for logging.
        
        Args:
            context: Execution context
            
        Returns:
            Dict containing execution summary
        """
        duration_ms = None
        if context.started_at and context.completed_at:
            duration_ms = int(
                (context.completed_at - context.started_at).total_seconds() * 1000
            )
        
        # Count blocks by status
        total_blocks = len(context.block_states)
        executed_blocks = sum(
            1 for state in context.block_states.values()
            if state.executed
        )
        successful_blocks = sum(
            1 for state in context.block_states.values()
            if state.executed and state.success
        )
        failed_blocks = sum(
            1 for state in context.block_states.values()
            if state.executed and not state.success
        )
        
        # Calculate average block duration
        block_durations = [
            state.duration_ms
            for state in context.block_states.values()
            if state.duration_ms is not None
        ]
        avg_block_duration = (
            sum(block_durations) / len(block_durations)
            if block_durations else 0
        )
        
        return {
            "workflow_id": context.workflow_id,
            "execution_id": context.execution_id,
            "user_id": context.user_id,
            "trigger": context.trigger,
            "status": context.status,
            "started_at": context.started_at.isoformat() if context.started_at else None,
            "completed_at": context.completed_at.isoformat() if context.completed_at else None,
            "duration_ms": duration_ms,
            "blocks": {
                "total": total_blocks,
                "executed": executed_blocks,
                "successful": successful_blocks,
                "failed": failed_blocks,
            },
            "performance": {
                "avg_block_duration_ms": round(avg_block_duration, 2),
                "total_duration_ms": duration_ms,
            },
            "tokens": {
                "total": context.total_tokens,
                "prompt": context.prompt_tokens,
                "completion": context.completion_tokens,
            },
            "cost": {
                "estimated": round(context.estimated_cost, 4),
            },
            "files": len(context.files),
            "error": context.error_message,
        }
    
    @staticmethod
    def _format_data(data: Any, max_length: int = 500) -> str:
        """
        Format data for logging (truncate if too long).
        
        Args:
            data: Data to format
            max_length: Maximum length
            
        Returns:
            Formatted string
        """
        import json
        
        try:
            formatted = json.dumps(data, indent=2)
            if len(formatted) > max_length:
                return formatted[:max_length] + "... (truncated)"
            return formatted
        except Exception:
            str_data = str(data)
            if len(str_data) > max_length:
                return str_data[:max_length] + "... (truncated)"
            return str_data
