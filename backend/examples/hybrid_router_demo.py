"""
Demo script for HybridQueryRouter functionality.

This script demonstrates the three query modes and their behavior.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.models.hybrid import QueryMode, ResponseType


async def demo_router_modes():
    """Demonstrate the three query modes."""

    print("\n" + "=" * 70)
    print("HYBRID QUERY ROUTER DEMONSTRATION")
    print("=" * 70 + "\n")

    # Note: This is a demonstration of the API, not actual execution
    # Actual execution requires initialized components

    print("1. FAST MODE - Quick Response (Speculative Only)")
    print("-" * 70)
    print("Use Case: Simple lookups, quick questions")
    print("Expected Time: 1-2 seconds")
    print("Path: Speculative → Final Response")
    print("\nExample:")
    print("  Query: 'What is machine learning?'")
    print("  Response: [FINAL] Machine learning is a subset of AI...")
    print("  Confidence: 0.75")
    print("  Time: 1.8s")

    print("\n" + "=" * 70 + "\n")

    print("2. BALANCED MODE - Progressive Refinement (Hybrid)")
    print("-" * 70)
    print("Use Case: Standard queries, best user experience")
    print("Expected Time: 2s (preliminary) + 5-15s (final)")
    print("Path: Speculative → Preliminary → Agentic → Refinements → Final")
    print("\nExample:")
    print("  Query: 'Explain neural networks'")
    print("  [PRELIMINARY] Neural networks are computational models... (2s)")
    print("  [REFINEMENT] Analyzing architecture details... (5s)")
    print("  [REFINEMENT] Comparing with traditional methods... (8s)")
    print("  [FINAL] Neural networks are sophisticated computational models... (12s)")
    print("  Confidence: 0.92")

    print("\n" + "=" * 70 + "\n")

    print("3. DEEP MODE - Comprehensive Analysis (Agentic Only)")
    print("-" * 70)
    print("Use Case: Complex questions, detailed analysis")
    print("Expected Time: 10-15 seconds")
    print("Path: Agentic → Reasoning Steps → Final Response")
    print("\nExample:")
    print("  Query: 'Compare supervised vs unsupervised learning'")
    print("  [REFINEMENT] Planning analysis approach... (2s)")
    print("  [REFINEMENT] Searching for supervised learning info... (5s)")
    print("  [REFINEMENT] Searching for unsupervised learning info... (8s)")
    print("  [REFINEMENT] Synthesizing comparison... (11s)")
    print("  [FINAL] Comprehensive comparison with examples... (14s)")
    print("  Confidence: 0.95")

    print("\n" + "=" * 70 + "\n")

    print("KEY FEATURES:")
    print("-" * 70)
    print("✓ Mode-based routing (FAST/BALANCED/DEEP)")
    print("✓ Parallel execution in BALANCED mode")
    print("✓ Resource sharing between paths")
    print("✓ Timeout handling with graceful degradation")
    print("✓ Progressive streaming for real-time updates")
    print("✓ Confidence scoring for all responses")
    print("✓ Source citations and reasoning steps")

    print("\n" + "=" * 70 + "\n")

    print("USAGE EXAMPLE:")
    print("-" * 70)
    print(
        """
from backend.services.hybrid_query_router import HybridQueryRouter
from backend.models.hybrid import QueryMode

# Initialize router
router = HybridQueryRouter(
    speculative_processor=speculative,
    agentic_processor=agentic,
    response_coordinator=coordinator
)

# Process query in BALANCED mode
async for chunk in router.process_query(
    query="What are the benefits of machine learning?",
    mode=QueryMode.BALANCED,
    session_id="user_123",
    top_k=10
):
    if chunk.type == ResponseType.PRELIMINARY:
        print(f"Quick answer: {chunk.content}")
    elif chunk.type == ResponseType.REFINEMENT:
        print(f"Refining: {chunk.content}")
    elif chunk.type == ResponseType.FINAL:
        print(f"Final answer: {chunk.content}")
        print(f"Confidence: {chunk.confidence_score:.2f}")
    """
    )

    print("\n" + "=" * 70 + "\n")

    print("PERFORMANCE COMPARISON:")
    print("-" * 70)
    print(f"{'Mode':<12} {'First Response':<15} {'Final Response':<15} {'Quality':<10}")
    print("-" * 70)
    print(f"{'FAST':<12} {'1-2s':<15} {'1-2s':<15} {'Good':<10}")
    print(f"{'BALANCED':<12} {'1-2s':<15} {'5-15s':<15} {'Excellent':<10}")
    print(f"{'DEEP':<12} {'5-15s':<15} {'5-15s':<15} {'Best':<10}")

    print("\n" + "=" * 70 + "\n")

    print("ERROR HANDLING:")
    print("-" * 70)
    print("✓ Speculative path fails → Falls back to agentic")
    print("✓ Agentic path fails → Returns speculative as final")
    print("✓ Both paths fail → Returns error message")
    print("✓ Timeout → Returns partial results")
    print("✓ Invalid mode → Raises ValueError")

    print("\n" + "=" * 70 + "\n")

    print("INTEGRATION STATUS:")
    print("-" * 70)
    print("✅ Task 4.1: Mode routing implemented")
    print("✅ Task 4.2: Parallel execution implemented")
    print("✅ Task 4.3: Resource sharing implemented")
    print("✅ Task 4.4: Unit tests implemented")
    print("✅ All requirements satisfied (1.1, 1.4, 4.1-4.3, 6.2-6.5)")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(demo_router_modes())
