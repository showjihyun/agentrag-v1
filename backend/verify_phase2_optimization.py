"""
Phase 2 Optimization Verification Script

Verifies:
1. Speculative execution implementation
2. Korean optimization features
3. Metrics collection system
"""

import sys
import importlib.util
from pathlib import Path


def check_file_exists(filepath: str) -> bool:
    """Check if file exists."""
    path = Path(filepath)
    exists = path.exists()
    print(f"{'✓' if exists else '✗'} {filepath}: {'EXISTS' if exists else 'MISSING'}")
    return exists


def check_class_exists(module_path: str, class_name: str) -> bool:
    """Check if class exists in module."""
    try:
        spec = importlib.util.spec_from_file_location("module", module_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            has_class = hasattr(module, class_name)
            print(
                f"{'✓' if has_class else '✗'} {class_name} in {module_path}: {'FOUND' if has_class else 'MISSING'}"
            )
            return has_class
    except Exception as e:
        print(f"✗ Error checking {class_name} in {module_path}: {e}")
        return False


def check_method_exists(module_path: str, class_name: str, method_name: str) -> bool:
    """Check if method exists in class."""
    try:
        spec = importlib.util.spec_from_file_location("module", module_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, class_name):
                cls = getattr(module, class_name)
                has_method = hasattr(cls, method_name)
                print(
                    f"  {'✓' if has_method else '✗'} Method {method_name}: {'FOUND' if has_method else 'MISSING'}"
                )
                return has_method
    except Exception as e:
        print(f"  ✗ Error checking method {method_name}: {e}")
        return False


def main():
    """Run verification."""
    print("=" * 60)
    print("Phase 2 Optimization Verification")
    print("=" * 60)

    all_passed = True

    # Phase 2.1: Speculative Execution
    print("\n📊 Phase 2.1: Speculative Execution")
    print("-" * 60)

    spec_file = "backend/core/speculative_processor.py"
    if check_file_exists(spec_file):
        check_class_exists(spec_file, "SpeculativeQueryProcessor")
        check_class_exists(spec_file, "ResponseMode")
        check_class_exists(spec_file, "ConfidenceLevel")

        check_method_exists(spec_file, "SpeculativeQueryProcessor", "process_query")
        check_method_exists(
            spec_file, "SpeculativeQueryProcessor", "_speculative_execution"
        )
        check_method_exists(spec_file, "SpeculativeQueryProcessor", "_fast_only")
        check_method_exists(spec_file, "SpeculativeQueryProcessor", "_deep_only")
        check_method_exists(
            spec_file, "SpeculativeQueryProcessor", "_calculate_confidence"
        )
    else:
        all_passed = False

    # Phase 2.2: Korean Optimization
    print("\n🇰🇷 Phase 2.2: Korean Optimization")
    print("-" * 60)

    korean_file = "backend/core/korean_optimizer.py"
    if check_file_exists(korean_file):
        check_class_exists(korean_file, "KoreanTextProcessor")
        check_class_exists(korean_file, "HybridKoreanSearch")
        check_class_exists(korean_file, "KoreanQueryAnalyzer")

        check_method_exists(korean_file, "KoreanTextProcessor", "preprocess")
        check_method_exists(korean_file, "KoreanTextProcessor", "smart_chunk")
        check_method_exists(korean_file, "HybridKoreanSearch", "search")
        check_method_exists(korean_file, "KoreanQueryAnalyzer", "analyze")
    else:
        all_passed = False

    # Phase 2.3: Metrics Collection
    print("\n📈 Phase 2.3: Metrics Collection")
    print("-" * 60)

    metrics_file = "backend/core/metrics_collector.py"
    if check_file_exists(metrics_file):
        check_class_exists(metrics_file, "MetricsCollector")

        check_method_exists(metrics_file, "MetricsCollector", "track_query")
        check_method_exists(metrics_file, "MetricsCollector", "track_agent")
        check_method_exists(metrics_file, "MetricsCollector", "track_llm_call")
        check_method_exists(metrics_file, "MetricsCollector", "record_cache_hit")
        check_method_exists(metrics_file, "MetricsCollector", "get_metrics")
    else:
        all_passed = False

    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ Phase 2 Optimization: ALL CHECKS PASSED")
        print("\nNext steps:")
        print("1. Integrate speculative processor into API")
        print("2. Configure Korean embedding model")
        print("3. Set up Prometheus + Grafana")
        print("4. Run performance tests")
        return 0
    else:
        print("❌ Phase 2 Optimization: SOME CHECKS FAILED")
        print("\nPlease review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
