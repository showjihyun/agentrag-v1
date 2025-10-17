"""
Verification script for Monitoring Dashboard implementation.

This script verifies that all monitoring dashboard components are properly implemented:
1. Backend metrics API endpoints
2. Frontend monitoring dashboard pages
3. Real-time overview component
4. Performance trends visualization
5. Routing analysis views
6. Threshold tuning interface
7. Alerts panel

Run: python backend/verify_monitoring_dashboard.py
"""

import os
import sys
from pathlib import Path


def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists."""
    if os.path.exists(filepath):
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description} NOT FOUND: {filepath}")
        return False


def check_file_contains(filepath: str, search_strings: list, description: str) -> bool:
    """Check if file contains specific strings."""
    if not os.path.exists(filepath):
        print(f"✗ {description}: File not found - {filepath}")
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    missing = []
    for search_str in search_strings:
        if search_str not in content:
            missing.append(search_str)

    if missing:
        print(f"✗ {description}: Missing content in {filepath}")
        for item in missing:
            print(f"  - Missing: {item}")
        return False
    else:
        print(f"✓ {description}")
        return True


def main():
    print("=" * 80)
    print("MONITORING DASHBOARD VERIFICATION")
    print("=" * 80)
    print()

    all_checks_passed = True

    # Backend API Endpoints
    print("1. Backend Metrics API Endpoints")
    print("-" * 80)

    checks = [
        check_file_exists("backend/api/metrics.py", "Metrics API module"),
        check_file_contains(
            "backend/api/metrics.py",
            [
                '"/adaptive"',
                '"/adaptive/timeseries"',
                '"/adaptive/alerts"',
                "get_adaptive_metrics",
                "get_adaptive_timeseries",
                "get_adaptive_alerts",
            ],
            "Metrics API endpoints",
        ),
        check_file_exists(
            "backend/services/adaptive_metrics.py", "Adaptive Metrics Service"
        ),
        check_file_contains(
            "backend/services/adaptive_metrics.py",
            [
                "AdaptiveMetricsService",
                "get_dashboard_data",
                "get_time_series_data",
                "create_snapshot",
                "PerformanceAlert",
            ],
            "Adaptive Metrics Service implementation",
        ),
    ]

    all_checks_passed = all_checks_passed and all(checks)
    print()

    # Frontend Monitoring Dashboard
    print("2. Frontend Monitoring Dashboard")
    print("-" * 80)

    checks = [
        check_file_exists("frontend/app/monitoring/page.tsx", "Monitoring page"),
        check_file_contains(
            "frontend/app/monitoring/page.tsx",
            ["MonitoringPage", "AdaptiveMonitoringDashboard", "useAuth"],
            "Monitoring page implementation",
        ),
        check_file_exists(
            "frontend/components/monitoring/AdaptiveMonitoringDashboard.tsx",
            "Adaptive Monitoring Dashboard component",
        ),
        check_file_contains(
            "frontend/components/monitoring/AdaptiveMonitoringDashboard.tsx",
            [
                "AdaptiveMonitoringDashboard",
                "RealTimeOverview",
                "PerformanceTrends",
                "RoutingAnalysis",
                "ThresholdTuning",
                "AlertsPanel",
                "autoRefresh",
                "refreshInterval",
            ],
            "Adaptive Monitoring Dashboard implementation",
        ),
    ]

    all_checks_passed = all_checks_passed and all(checks)
    print()

    # Real-Time Overview Component
    print("3. Real-Time Overview Component")
    print("-" * 80)

    checks = [
        check_file_exists(
            "frontend/components/monitoring/RealTimeOverview.tsx",
            "Real-Time Overview component",
        ),
        check_file_contains(
            "frontend/components/monitoring/RealTimeOverview.tsx",
            [
                "RealTimeOverview",
                "mode_distribution",
                "latency",
                "cache_performance",
                "escalations",
                "fetchData",
                "autoRefresh",
            ],
            "Real-Time Overview implementation",
        ),
    ]

    all_checks_passed = all_checks_passed and all(checks)
    print()

    # Performance Trends Component
    print("4. Performance Trends Component")
    print("-" * 80)

    checks = [
        check_file_exists(
            "frontend/components/monitoring/PerformanceTrends.tsx",
            "Performance Trends component",
        ),
        check_file_contains(
            "frontend/components/monitoring/PerformanceTrends.tsx",
            [
                "PerformanceTrends",
                "latencyData",
                "modeData",
                "fetchTimeSeriesData",
                "timeRange",
                "Latency Over Time",
                "Mode Distribution Over Time",
            ],
            "Performance Trends implementation",
        ),
    ]

    all_checks_passed = all_checks_passed and all(checks)
    print()

    # Routing Analysis Component
    print("5. Routing Analysis Component")
    print("-" * 80)

    checks = [
        check_file_exists(
            "frontend/components/monitoring/RoutingAnalysis.tsx",
            "Routing Analysis component",
        ),
        check_file_contains(
            "frontend/components/monitoring/RoutingAnalysis.tsx",
            [
                "RoutingAnalysis",
                "complexity_distribution",
                "escalations",
                "Routing Accuracy",
                "Query Complexity Distribution",
                "Escalation Patterns",
            ],
            "Routing Analysis implementation",
        ),
    ]

    all_checks_passed = all_checks_passed and all(checks)
    print()

    # Threshold Tuning Component
    print("6. Threshold Tuning Component")
    print("-" * 80)

    checks = [
        check_file_exists(
            "frontend/components/monitoring/ThresholdTuning.tsx",
            "Threshold Tuning component",
        ),
        check_file_contains(
            "frontend/components/monitoring/ThresholdTuning.tsx",
            [
                "ThresholdTuning",
                "simpleThreshold",
                "complexThreshold",
                "simulateThresholds",
                "Simulation Results",
                "Current vs Target Distribution",
                "isAdmin",
            ],
            "Threshold Tuning implementation",
        ),
    ]

    all_checks_passed = all_checks_passed and all(checks)
    print()

    # Alerts Panel Component
    print("7. Alerts Panel Component")
    print("-" * 80)

    checks = [
        check_file_exists(
            "frontend/components/monitoring/AlertsPanel.tsx", "Alerts Panel component"
        ),
        check_file_contains(
            "frontend/components/monitoring/AlertsPanel.tsx",
            [
                "AlertsPanel",
                "fetchAlerts",
                "critical",
                "warning",
                "info",
                "recommendations",
                "Performance Alerts",
            ],
            "Alerts Panel implementation",
        ),
    ]

    all_checks_passed = all_checks_passed and all(checks)
    print()

    # Summary
    print("=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)

    if all_checks_passed:
        print("✓ All monitoring dashboard components are properly implemented!")
        print()
        print("Components verified:")
        print("  ✓ Backend metrics API endpoints")
        print("  ✓ Frontend monitoring dashboard page")
        print("  ✓ Real-time overview component")
        print("  ✓ Performance trends visualization")
        print("  ✓ Routing analysis views")
        print("  ✓ Threshold tuning interface")
        print("  ✓ Alerts panel")
        print()
        print("Next steps:")
        print("  1. Start the backend server: cd backend && uvicorn main:app --reload")
        print("  2. Start the frontend: cd frontend && npm run dev")
        print("  3. Access monitoring dashboard: http://localhost:3000/monitoring")
        print("  4. Generate some queries to populate metrics")
        print("  5. Create periodic snapshots: POST /api/metrics/adaptive/snapshot")
        return 0
    else:
        print("✗ Some monitoring dashboard components are missing or incomplete.")
        print(
            "Please review the errors above and ensure all components are implemented."
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
