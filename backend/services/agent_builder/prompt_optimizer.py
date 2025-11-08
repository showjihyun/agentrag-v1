"""
Auto Prompt Optimizer for Agent Builder.

Automatically optimizes agent prompts based on performance data and feedback.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum
import json
import hashlib

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

logger = logging.getLogger(__name__)


class OptimizationStrategy(str, Enum):
    """Prompt optimization strategies."""
    PERFORMANCE_BASED = "performance_based"  # Based on execution metrics
    FEEDBACK_BASED = "feedback_based"        # Based on user feedback
    AB_TESTING = "ab_testing"                # A/B testing variants
    ITERATIVE = "iterative"                  # Iterative refinement
    HYBRID = "hybrid"                        # Combination of strategies


class PromptVersion:
    """Represents a prompt version with performance metrics."""
    
    def __init__(
        self,
        version_id: str,
        prompt_text: str,
        agent_id: str,
        created_at: datetime,
        strategy: OptimizationStrategy,
        parent_version_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.version_id = version_id
        self.prompt_text = prompt_text
        self.agent_id = agent_id
        self.created_at = created_at
        self.strategy = strategy
        self.parent_version_id = parent_version_id
        self.metadata = metadata or {}
        
        # Performance metrics
        self.execution_count = 0
        self.success_count = 0
        self.avg_duration_ms = 0.0
        self.avg_token_count = 0.0
        self.avg_feedback_rating = 0.0
        self.feedback_count = 0
        
        # A/B testing metrics
        self.conversion_rate = 0.0
        self.confidence_score = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.execution_count == 0:
            return 0.0
        return self.success_count / self.execution_count
    
    @property
    def performance_score(self) -> float:
        """
        Calculate overall performance score.
        
        Combines success rate, speed, and feedback.
        """
        # Normalize metrics
        success_weight = 0.4
        speed_weight = 0.3
        feedback_weight = 0.3
        
        # Success rate (0-1)
        success_score = self.success_rate
        
        # Speed score (inverse of duration, normalized)
        # Assume 5000ms is baseline, lower is better
        speed_score = max(0, 1 - (self.avg_duration_ms / 5000))
        
        # Feedback score (0-1, assuming 5-point scale)
        feedback_score = self.avg_feedback_rating / 5.0 if self.feedback_count > 0 else 0.5
        
        return (
            success_weight * success_score +
            speed_weight * speed_score +
            feedback_weight * feedback_score
        )


class AutoPromptOptimizer:
    """
    Automatically optimizes agent prompts based on performance data.
    
    Features:
    - Performance-based optimization
    - A/B testing
    - Iterative refinement
    - Automatic rollback on degradation
    - Prompt version management
    """
    
    def __init__(
        self,
        db: Session,
        llm_service: Optional[Any] = None,
        cache_manager: Optional[Any] = None
    ):
        """
        Initialize prompt optimizer.
        
        Args:
            db: Database session
            llm_service: LLM service for generating optimizations
            cache_manager: Cache manager for storing versions
        """
        self.db = db
        self.llm_service = llm_service
        self.cache_manager = cache_manager
        
        # In-memory storage (use database in production)
        self.prompt_versions: Dict[str, List[PromptVersion]] = {}
        self.active_ab_tests: Dict[str, Dict[str, Any]] = {}
        
        logger.info("AutoPromptOptimizer initialized")
    
    async def optimize_prompt(
        self,
        agent_id: str,
        current_prompt: str,
        performance_data: Dict[str, Any],
        strategy: OptimizationStrategy = OptimizationStrategy.HYBRID
    ) -> str:
        """
        Optimize prompt based on performance data.
        
        Args:
            agent_id: Agent ID
            current_prompt: Current prompt text
            performance_data: Performance metrics
            strategy: Optimization strategy
            
        Returns:
            Optimized prompt text
        """
        logger.info(f"Optimizing prompt for agent {agent_id} using {strategy.value} strategy")
        
        # Analyze performance issues
        issues = await self._analyze_performance(performance_data)
        
        if not issues:
            logger.info("No performance issues detected")
            return current_prompt
        
        # Generate optimization suggestions
        suggestions = await self._generate_suggestions(
            current_prompt,
            issues,
            performance_data
        )
        
        # Apply optimizations
        optimized_prompt = await self._apply_optimizations(
            current_prompt,
            suggestions
        )
        
        # Create new version
        version = await self._create_prompt_version(
            agent_id=agent_id,
            prompt_text=optimized_prompt,
            strategy=strategy,
            metadata={
                "issues": issues,
                "suggestions": suggestions,
                "performance_data": performance_data
            }
        )
        
        logger.info(f"Created optimized prompt version: {version.version_id}")
        
        return optimized_prompt
    
    async def run_ab_test(
        self,
        agent_id: str,
        prompt_variants: List[str],
        test_duration_hours: int = 24,
        min_samples: int = 100,
        confidence_threshold: float = 0.95
    ) -> Dict[str, Any]:
        """
        Run A/B test on prompt variants.
        
        Args:
            agent_id: Agent ID
            prompt_variants: List of prompt variants to test
            test_duration_hours: Test duration in hours
            min_samples: Minimum samples per variant
            confidence_threshold: Statistical confidence threshold
            
        Returns:
            A/B test results
        """
        logger.info(f"Starting A/B test for agent {agent_id} with {len(prompt_variants)} variants")
        
        test_id = self._generate_test_id(agent_id)
        
        # Create versions for each variant
        versions = []
        for i, prompt in enumerate(prompt_variants):
            version = await self._create_prompt_version(
                agent_id=agent_id,
                prompt_text=prompt,
                strategy=OptimizationStrategy.AB_TESTING,
                metadata={
                    "test_id": test_id,
                    "variant_index": i,
                    "variant_name": f"Variant {chr(65 + i)}"  # A, B, C, ...
                }
            )
            versions.append(version)
        
        # Store test configuration
        self.active_ab_tests[test_id] = {
            "test_id": test_id,
            "agent_id": agent_id,
            "versions": [v.version_id for v in versions],
            "start_time": datetime.now(timezone.utc),
            "end_time": datetime.now(timezone.utc) + timedelta(hours=test_duration_hours),
            "min_samples": min_samples,
            "confidence_threshold": confidence_threshold,
            "status": "running"
        }
        
        logger.info(f"A/B test {test_id} started, will run for {test_duration_hours} hours")
        
        return {
            "test_id": test_id,
            "variants": len(prompt_variants),
            "start_time": self.active_ab_tests[test_id]["start_time"].isoformat(),
            "end_time": self.active_ab_tests[test_id]["end_time"].isoformat()
        }
    
    async def get_ab_test_results(
        self,
        test_id: str
    ) -> Dict[str, Any]:
        """
        Get A/B test results.
        
        Args:
            test_id: Test ID
            
        Returns:
            Test results with winner
        """
        test = self.active_ab_tests.get(test_id)
        
        if not test:
            raise ValueError(f"A/B test not found: {test_id}")
        
        # Get versions
        agent_id = test["agent_id"]
        versions = [
            v for v in self.prompt_versions.get(agent_id, [])
            if v.version_id in test["versions"]
        ]
        
        # Calculate statistics
        results = []
        for version in versions:
            results.append({
                "version_id": version.version_id,
                "variant_name": version.metadata.get("variant_name"),
                "execution_count": version.execution_count,
                "success_rate": version.success_rate,
                "avg_duration_ms": version.avg_duration_ms,
                "avg_feedback_rating": version.avg_feedback_rating,
                "performance_score": version.performance_score,
                "confidence_score": version.confidence_score
            })
        
        # Determine winner
        winner = max(results, key=lambda r: r["performance_score"]) if results else None
        
        # Check if test is complete
        is_complete = (
            datetime.now(timezone.utc) >= test["end_time"] or
            all(r["execution_count"] >= test["min_samples"] for r in results)
        )
        
        if is_complete and test["status"] == "running":
            test["status"] = "completed"
            logger.info(f"A/B test {test_id} completed, winner: {winner['variant_name']}")
        
        return {
            "test_id": test_id,
            "status": test["status"],
            "start_time": test["start_time"].isoformat(),
            "end_time": test["end_time"].isoformat(),
            "is_complete": is_complete,
            "results": results,
            "winner": winner,
            "recommendation": self._generate_recommendation(results, winner)
        }
    
    async def track_prompt_performance(
        self,
        agent_id: str,
        version_id: str,
        execution_result: Dict[str, Any]
    ):
        """
        Track performance metrics for a prompt version.
        
        Args:
            agent_id: Agent ID
            version_id: Prompt version ID
            execution_result: Execution result with metrics
        """
        versions = self.prompt_versions.get(agent_id, [])
        version = next((v for v in versions if v.version_id == version_id), None)
        
        if not version:
            logger.warning(f"Version not found: {version_id}")
            return
        
        # Update metrics
        version.execution_count += 1
        
        if execution_result.get("success", False):
            version.success_count += 1
        
        # Update running averages
        duration = execution_result.get("duration_ms", 0)
        version.avg_duration_ms = (
            (version.avg_duration_ms * (version.execution_count - 1) + duration) /
            version.execution_count
        )
        
        token_count = execution_result.get("token_count", 0)
        version.avg_token_count = (
            (version.avg_token_count * (version.execution_count - 1) + token_count) /
            version.execution_count
        )
        
        # Update feedback if provided
        if "feedback_rating" in execution_result:
            rating = execution_result["feedback_rating"]
            version.feedback_count += 1
            version.avg_feedback_rating = (
                (version.avg_feedback_rating * (version.feedback_count - 1) + rating) /
                version.feedback_count
            )
        
        logger.debug(
            f"Updated metrics for version {version_id}: "
            f"executions={version.execution_count}, "
            f"success_rate={version.success_rate:.2f}"
        )
    
    async def get_best_prompt_version(
        self,
        agent_id: str,
        min_executions: int = 10
    ) -> Optional[PromptVersion]:
        """
        Get best performing prompt version.
        
        Args:
            agent_id: Agent ID
            min_executions: Minimum executions required
            
        Returns:
            Best prompt version or None
        """
        versions = self.prompt_versions.get(agent_id, [])
        
        # Filter by minimum executions
        qualified = [v for v in versions if v.execution_count >= min_executions]
        
        if not qualified:
            return None
        
        # Sort by performance score
        best = max(qualified, key=lambda v: v.performance_score)
        
        logger.info(
            f"Best prompt version for agent {agent_id}: {best.version_id} "
            f"(score: {best.performance_score:.3f})"
        )
        
        return best
    
    async def auto_rollback_if_degraded(
        self,
        agent_id: str,
        current_version_id: str,
        degradation_threshold: float = 0.1
    ) -> Optional[str]:
        """
        Automatically rollback if performance degraded.
        
        Args:
            agent_id: Agent ID
            current_version_id: Current version ID
            degradation_threshold: Threshold for degradation (0-1)
            
        Returns:
            Rollback version ID if rolled back, None otherwise
        """
        versions = self.prompt_versions.get(agent_id, [])
        current = next((v for v in versions if v.version_id == current_version_id), None)
        
        if not current or current.execution_count < 10:
            return None  # Not enough data
        
        # Get parent version
        if not current.parent_version_id:
            return None  # No parent to rollback to
        
        parent = next((v for v in versions if v.version_id == current.parent_version_id), None)
        
        if not parent:
            return None
        
        # Check for degradation
        performance_drop = parent.performance_score - current.performance_score
        
        if performance_drop > degradation_threshold:
            logger.warning(
                f"Performance degradation detected for agent {agent_id}: "
                f"{performance_drop:.3f} drop. Rolling back to {parent.version_id}"
            )
            return parent.version_id
        
        return None
    
    async def _analyze_performance(
        self,
        performance_data: Dict[str, Any]
    ) -> List[str]:
        """Analyze performance data and identify issues."""
        issues = []
        
        # Check success rate
        success_rate = performance_data.get("success_rate", 1.0)
        if success_rate < 0.8:
            issues.append("low_success_rate")
        
        # Check duration
        avg_duration = performance_data.get("avg_duration_ms", 0)
        if avg_duration > 5000:
            issues.append("slow_execution")
        
        # Check token usage
        avg_tokens = performance_data.get("avg_token_count", 0)
        if avg_tokens > 3000:
            issues.append("high_token_usage")
        
        # Check feedback
        avg_feedback = performance_data.get("avg_feedback_rating", 5.0)
        if avg_feedback < 3.0:
            issues.append("low_user_satisfaction")
        
        # Check error patterns
        common_errors = performance_data.get("common_errors", [])
        if common_errors:
            issues.append("frequent_errors")
        
        return issues
    
    async def _generate_suggestions(
        self,
        current_prompt: str,
        issues: List[str],
        performance_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate optimization suggestions based on issues."""
        suggestions = []
        
        if "low_success_rate" in issues:
            suggestions.append({
                "type": "clarity",
                "description": "Improve prompt clarity and specificity",
                "action": "add_examples",
                "priority": "high"
            })
        
        if "slow_execution" in issues:
            suggestions.append({
                "type": "conciseness",
                "description": "Reduce prompt length for faster processing",
                "action": "simplify_instructions",
                "priority": "medium"
            })
        
        if "high_token_usage" in issues:
            suggestions.append({
                "type": "efficiency",
                "description": "Optimize token usage",
                "action": "compress_prompt",
                "priority": "medium"
            })
        
        if "low_user_satisfaction" in issues:
            suggestions.append({
                "type": "quality",
                "description": "Improve output quality",
                "action": "add_quality_guidelines",
                "priority": "high"
            })
        
        if "frequent_errors" in issues:
            suggestions.append({
                "type": "robustness",
                "description": "Add error handling instructions",
                "action": "add_error_handling",
                "priority": "high"
            })
        
        # Use LLM to generate specific suggestions
        if self.llm_service and suggestions:
            llm_suggestions = await self._generate_llm_suggestions(
                current_prompt,
                issues,
                performance_data
            )
            suggestions.extend(llm_suggestions)
        
        return suggestions
    
    async def _generate_llm_suggestions(
        self,
        current_prompt: str,
        issues: List[str],
        performance_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Use LLM to generate specific optimization suggestions."""
        analysis_prompt = f"""Analyze this agent prompt and suggest specific improvements:

Current Prompt:
{current_prompt}

Identified Issues:
{', '.join(issues)}

Performance Data:
{json.dumps(performance_data, indent=2)}

Provide 3-5 specific, actionable suggestions to improve the prompt.
Focus on:
1. Clarity and specificity
2. Reducing ambiguity
3. Adding helpful examples
4. Improving structure
5. Optimizing for the identified issues

Format each suggestion as:
- Type: [clarity|conciseness|quality|robustness]
- Description: [what to improve]
- Specific change: [exact text to add/modify]

Respond in JSON format."""
        
        try:
            response = await self.llm_service.generate(analysis_prompt)
            suggestions_data = json.loads(response)
            
            return [
                {
                    "type": s.get("type", "general"),
                    "description": s.get("description", ""),
                    "action": "llm_suggested",
                    "specific_change": s.get("specific_change", ""),
                    "priority": "medium"
                }
                for s in suggestions_data.get("suggestions", [])
            ]
        except Exception as e:
            logger.error(f"Failed to generate LLM suggestions: {e}")
            return []
    
    async def _apply_optimizations(
        self,
        current_prompt: str,
        suggestions: List[Dict[str, Any]]
    ) -> str:
        """Apply optimization suggestions to prompt."""
        optimized = current_prompt
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        sorted_suggestions = sorted(
            suggestions,
            key=lambda s: priority_order.get(s.get("priority", "low"), 2)
        )
        
        # Apply high priority suggestions
        for suggestion in sorted_suggestions:
            if suggestion.get("priority") != "high":
                continue
            
            action = suggestion.get("action")
            
            if action == "add_examples":
                optimized = self._add_examples(optimized)
            elif action == "simplify_instructions":
                optimized = self._simplify_instructions(optimized)
            elif action == "add_quality_guidelines":
                optimized = self._add_quality_guidelines(optimized)
            elif action == "add_error_handling":
                optimized = self._add_error_handling(optimized)
            elif action == "llm_suggested" and "specific_change" in suggestion:
                optimized = self._apply_specific_change(
                    optimized,
                    suggestion["specific_change"]
                )
        
        return optimized
    
    def _add_examples(self, prompt: str) -> str:
        """Add example section to prompt."""
        if "Example:" in prompt or "Examples:" in prompt:
            return prompt  # Already has examples
        
        example_section = """

Examples:
Input: [example input]
Output: [example output]

Input: [another example]
Output: [another output]"""
        
        return prompt + example_section
    
    def _simplify_instructions(self, prompt: str) -> str:
        """Simplify prompt instructions."""
        # Remove redundant phrases
        simplified = prompt.replace("Please note that", "")
        simplified = simplified.replace("It is important to", "")
        simplified = simplified.replace("Make sure to", "")
        
        # Remove excessive line breaks
        while "\n\n\n" in simplified:
            simplified = simplified.replace("\n\n\n", "\n\n")
        
        return simplified.strip()
    
    def _add_quality_guidelines(self, prompt: str) -> str:
        """Add quality guidelines to prompt."""
        if "Quality guidelines:" in prompt:
            return prompt
        
        guidelines = """

Quality guidelines:
- Provide accurate and complete information
- Use clear and concise language
- Verify facts before stating them
- Acknowledge uncertainty when appropriate"""
        
        return prompt + guidelines
    
    def _add_error_handling(self, prompt: str) -> str:
        """Add error handling instructions."""
        if "error" in prompt.lower() or "fail" in prompt.lower():
            return prompt
        
        error_handling = """

Error handling:
- If you encounter an error, explain what went wrong
- Suggest alternative approaches
- Never make up information to fill gaps"""
        
        return prompt + error_handling
    
    def _apply_specific_change(self, prompt: str, change: str) -> str:
        """Apply a specific change suggested by LLM."""
        # Simple append for now
        # In production, use more sophisticated text manipulation
        return prompt + "\n\n" + change
    
    async def _create_prompt_version(
        self,
        agent_id: str,
        prompt_text: str,
        strategy: OptimizationStrategy,
        parent_version_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PromptVersion:
        """Create a new prompt version."""
        version_id = self._generate_version_id(agent_id, prompt_text)
        
        version = PromptVersion(
            version_id=version_id,
            prompt_text=prompt_text,
            agent_id=agent_id,
            created_at=datetime.now(timezone.utc),
            strategy=strategy,
            parent_version_id=parent_version_id,
            metadata=metadata
        )
        
        if agent_id not in self.prompt_versions:
            self.prompt_versions[agent_id] = []
        
        self.prompt_versions[agent_id].append(version)
        
        return version
    
    def _generate_version_id(self, agent_id: str, prompt_text: str) -> str:
        """Generate unique version ID."""
        content = f"{agent_id}:{prompt_text}:{datetime.now(timezone.utc).isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _generate_test_id(self, agent_id: str) -> str:
        """Generate unique test ID."""
        content = f"test:{agent_id}:{datetime.now(timezone.utc).isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _generate_recommendation(
        self,
        results: List[Dict[str, Any]],
        winner: Optional[Dict[str, Any]]
    ) -> str:
        """Generate recommendation based on A/B test results."""
        if not winner:
            return "Insufficient data to make a recommendation"
        
        # Check if winner is significantly better
        other_scores = [r["performance_score"] for r in results if r != winner]
        if not other_scores:
            return f"Deploy {winner['variant_name']} (only variant tested)"
        
        avg_other = sum(other_scores) / len(other_scores)
        improvement = ((winner["performance_score"] - avg_other) / avg_other) * 100
        
        if improvement > 10:
            return f"Deploy {winner['variant_name']} (significant improvement: +{improvement:.1f}%)"
        elif improvement > 5:
            return f"Deploy {winner['variant_name']} (moderate improvement: +{improvement:.1f}%)"
        else:
            return f"Results inconclusive (improvement: +{improvement:.1f}%). Consider longer test."


# Example usage
EXAMPLE_OPTIMIZATION = {
    "agent_id": "agent_123",
    "current_prompt": "You are a helpful assistant. Answer questions.",
    "performance_data": {
        "success_rate": 0.75,
        "avg_duration_ms": 6000,
        "avg_token_count": 3500,
        "avg_feedback_rating": 2.8,
        "common_errors": ["timeout", "incomplete_response"]
    }
}

EXAMPLE_AB_TEST = {
    "agent_id": "agent_123",
    "variants": [
        "You are a helpful assistant. Provide clear, concise answers.",
        "You are an expert assistant. Give detailed, accurate responses with examples.",
        "You are a friendly assistant. Answer questions in a conversational tone."
    ],
    "test_duration_hours": 24,
    "min_samples": 100
}
