"""
Verification script for Performance Optimization Phase 1
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def verify_files_exist():
    """Verify all new files are created."""
    print("=" * 70)
    print("VERIFICATION: Performance Optimization Phase 1")
    print("=" * 70)
    print()

    files_to_check = [
        "core/milvus_pool.py",
        "core/cache_manager.py",
        "core/query_optimizer.py",
        "PERFORMANCE_OPTIMIZATION_PHASE1.md",
    ]

    print("1. Checking file creation...")
    all_exist = True

    for file_path in files_to_check:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        exists = os.path.exists(full_path)
        status = "✓" if exists else "✗"
        print(f"   {status} {file_path}")

        if not exists:
            all_exist = False

    print()
    return all_exist


def verify_imports():
    """Verify all modules can be imported."""
    print("2. Checking module imports...")

    modules = [
        ("core.milvus_pool", ["MilvusConnectionPool", "get_milvus_pool"]),
        ("core.cache_manager", ["MultiLevelCache", "LRUCache", "get_cache_manager"]),
        ("core.query_optimizer", ["BatchLoader", "QueryOptimizer", "monitor_query"]),
    ]

    all_imported = True

    for module_name, classes in modules:
        try:
            module = __import__(module_name, fromlist=classes)

            for class_name in classes:
                if hasattr(module, class_name):
                    print(f"   ✓ {module_name}.{class_name}")
                else:
                    print(f"   ✗ {module_name}.{class_name} not found")
                    all_imported = False

        except Exception as e:
            print(f"   ✗ Failed to import {module_name}: {e}")
            all_imported = False

    print()
    return all_imported


def verify_config_updates():
    """Verify config.py has new settings."""
    print("3. Checking configuration updates...")

    try:
        from config import settings

        checks = [
            ("MILVUS_POOL_SIZE", hasattr(settings, "MILVUS_POOL_SIZE")),
            ("MILVUS_MAX_IDLE_TIME", hasattr(settings, "MILVUS_MAX_IDLE_TIME")),
        ]

        all_updated = True
        for setting_name, exists in checks:
            status = "✓" if exists else "✗"
            print(f"   {status} {setting_name}")

            if not exists:
                all_updated = False

        print()
        return all_updated

    except Exception as e:
        print(f"   ✗ Failed to check config: {e}")
        print()
        return False


def verify_main_integration():
    """Verify main.py integrates new components."""
    print("4. Checking main.py integration...")

    main_file = os.path.join(os.path.dirname(__file__), "main.py")

    try:
        with open(main_file, "r", encoding="utf-8") as f:
            content = f.read()

        checks = [
            ("Milvus pool import", "milvus_pool import"),
            ("Cache manager import", "cache_manager import"),
            ("Milvus pool init", "milvus_pool = get_milvus_pool"),
            ("Cache manager init", "cache_manager = get_cache_manager"),
            ("Milvus pool cleanup", "cleanup_milvus_pool"),
            ("Cache manager cleanup", "cleanup_cache_manager"),
        ]

        all_integrated = True
        for check_name, check_string in checks:
            exists = check_string in content
            status = "✓" if exists else "✗"
            print(f"   {status} {check_name}")

            if not exists:
                all_integrated = False

        print()
        return all_integrated

    except Exception as e:
        print(f"   ✗ Failed to check main.py: {e}")
        print()
        return False


def print_summary(results):
    """Print verification summary."""
    print("=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    print()

    all_passed = all(results.values())

    for check_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"   {status}: {check_name}")

    print()
    print("=" * 70)

    if all_passed:
        print("✓ ALL CHECKS PASSED")
        print()
        print("Performance Optimization Phase 1 is complete!")
        print()
        print("New Features:")
        print("  • Milvus Connection Pool - Efficient connection management")
        print("  • Multi-Level Cache - L1 (memory) + L2 (Redis) caching")
        print("  • Query Optimizer - N+1 prevention, batch loading")
        print("  • Performance Monitoring - Query performance tracking")
        print()
        print("Next Steps:")
        print("  1. Test the new connection pools under load")
        print("  2. Monitor cache hit rates")
        print("  3. Review query performance metrics")
        print("  4. Proceed to Phase 2: Monitoring & Observability")
    else:
        print("✗ SOME CHECKS FAILED")
        print()
        print("Please review the failed checks above and fix any issues.")

    print("=" * 70)

    return all_passed


def main():
    """Run all verifications."""
    results = {
        "File Creation": verify_files_exist(),
        "Module Imports": verify_imports(),
        "Config Updates": verify_config_updates(),
        "Main Integration": verify_main_integration(),
    }

    success = print_summary(results)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
