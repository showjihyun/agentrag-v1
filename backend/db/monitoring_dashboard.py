#!/usr/bin/env python3
"""
Database Monitoring Dashboard
Provides real-time monitoring and analytics for the optimized database.

Usage:
    python monitoring_dashboard.py --server    # Start web dashboard
    python monitoring_dashboard.py --report    # Generate performance report
    python monitoring_dashboard.py --alerts    # Check for alerts
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psutil
from flask import Flask, jsonify, render_template_string
from sqlalchemy import create_engine, text

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from config import get_settings
from db.database import get_db_url

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseMonitor:
    """Database monitoring and analytics."""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_url = get_db_url()
        self.engine = create_engine(self.db_url)
    
    def get_performance_metrics(self) -> Dict[str, any]:
        """Get comprehensive performance metrics."""
        metrics = {}
        
        try:
            with self.engine.connect() as conn:
                # Database size and growth
                result = conn.execute(text("""
                    SELECT 
                        pg_size_pretty(pg_database_size(current_database())) as db_size,
                        pg_database_size(current_database()) as db_size_bytes
                """)).fetchone()
                
                metrics["database"] = {
                    "size": result[0],
                    "size_bytes": result[1]
                }
                
                # Connection statistics
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_connections,
                        COUNT(*) FILTER (WHERE state = 'active') as active_connections,
                        COUNT(*) FILTER (WHERE state = 'idle') as idle_connections,
                        COUNT(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction
                    FROM pg_stat_activity
                """)).fetchone()
                
                metrics["connections"] = {
                    "total": result[0],
                    "active": result[1],
                    "idle": result[2],
                    "idle_in_transaction": result[3]
                }
                
                # Cache hit ratios
                result = conn.execute(text("""
                    SELECT 
                        ROUND(
                            sum(heap_blks_hit) / GREATEST(sum(heap_blks_hit + heap_blks_read), 1) * 100, 2
                        ) as cache_hit_ratio
                    FROM pg_statio_user_tables
                """)).scalar()
                
                metrics["cache"] = {
                    "hit_ratio": result or 0
                }
                
                # Index usage statistics
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_indexes,
                        COUNT(*) FILTER (WHERE idx_scan = 0) as unused_indexes,
                        AVG(idx_scan) as avg_index_scans
                    FROM pg_stat_user_indexes
                """)).fetchone()
                
                metrics["indexes"] = {
                    "total": result[0],
                    "unused": result[1],
                    "avg_scans": round(result[2] or 0, 2)
                }
                
                # Table statistics
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_tables,
                        SUM(n_tup_ins) as total_inserts,
                        SUM(n_tup_upd) as total_updates,
                        SUM(n_tup_del) as total_deletes,
                        SUM(seq_scan) as sequential_scans,
                        SUM(idx_scan) as index_scans
                    FROM pg_stat_user_tables
                """)).fetchone()
                
                metrics["tables"] = {
                    "total": result[0],
                    "inserts": result[1] or 0,
                    "updates": result[2] or 0,
                    "deletes": result[3] or 0,
                    "seq_scans": result[4] or 0,
                    "idx_scans": result[5] or 0
                }
                
                # Workflow platform specific metrics
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_workflows,
                        COUNT(*) FILTER (WHERE deleted_at IS NULL) as active_workflows,
                        COUNT(*) FILTER (WHERE is_public = true AND deleted_at IS NULL) as public_workflows
                    FROM workflows
                """)).fetchone()
                
                metrics["workflows"] = {
                    "total": result[0],
                    "active": result[1],
                    "public": result[2]
                }
                
                # Execution metrics (last 24 hours)
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_executions,
                        COUNT(*) FILTER (WHERE status = 'completed') as successful_executions,
                        COUNT(*) FILTER (WHERE status = 'failed') as failed_executions,
                        COUNT(*) FILTER (WHERE status = 'running') as running_executions,
                        AVG(duration_ms) as avg_duration_ms
                    FROM workflow_executions 
                    WHERE started_at > NOW() - INTERVAL '24 hours'
                """)).fetchone()
                
                metrics["executions_24h"] = {
                    "total": result[0],
                    "successful": result[1],
                    "failed": result[2],
                    "running": result[3],
                    "avg_duration_ms": round(result[4] or 0, 2),
                    "success_rate": round((result[1] / max(result[0], 1)) * 100, 2)
                }
                
                # Agent metrics
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_agents,
                        COUNT(*) FILTER (WHERE deleted_at IS NULL) as active_agents,
                        COUNT(*) FILTER (WHERE is_public = true AND deleted_at IS NULL) as public_agents
                    FROM agents
                """)).fetchone()
                
                metrics["agents"] = {
                    "total": result[0],
                    "active": result[1],
                    "public": result[2]
                }
                
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            metrics["error"] = str(e)
        
        return metrics
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, any]]:
        """Get slow query statistics."""
        try:
            with self.engine.connect() as conn:
                # Enable pg_stat_statements if available
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_stat_statements"))
                except:
                    pass
                
                # Get slow queries from pg_stat_statements
                result = conn.execute(text(f"""
                    SELECT 
                        query,
                        calls,
                        total_exec_time,
                        mean_exec_time,
                        rows,
                        100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                    FROM pg_stat_statements 
                    WHERE query NOT LIKE '%pg_stat_statements%'
                    ORDER BY mean_exec_time DESC 
                    LIMIT {limit}
                """)).fetchall()
                
                return [
                    {
                        "query": row[0][:200] + "..." if len(row[0]) > 200 else row[0],
                        "calls": row[1],
                        "total_time": round(row[2], 2),
                        "avg_time": round(row[3], 2),
                        "rows": row[4],
                        "hit_percent": round(row[5] or 0, 2)
                    }
                    for row in result
                ]
        except Exception as e:
            logger.warning(f"Could not get slow queries (pg_stat_statements not available): {e}")
            return []
    
    def get_table_sizes(self, limit: int = 10) -> List[Dict[str, any]]:
        """Get largest tables by size."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes,
                        n_tup_ins + n_tup_upd + n_tup_del as total_operations
                    FROM pg_tables t
                    LEFT JOIN pg_stat_user_tables s ON t.tablename = s.relname
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC 
                    LIMIT {limit}
                """)).fetchall()
                
                return [
                    {
                        "schema": row[0],
                        "table": row[1],
                        "size": row[2],
                        "size_bytes": row[3],
                        "operations": row[4] or 0
                    }
                    for row in result
                ]
        except Exception as e:
            logger.error(f"Error getting table sizes: {e}")
            return []
    
    def get_partition_info(self) -> List[Dict[str, any]]:
        """Get partition information."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT * FROM partition_info ORDER BY table_family, partition_date DESC
                """)).fetchall()
                
                return [
                    {
                        "schema": row[0],
                        "table": row[1],
                        "size": row[2],
                        "size_bytes": row[3],
                        "partition_date": row[4].isoformat() if row[4] else None,
                        "table_family": row[5]
                    }
                    for row in result
                ]
        except Exception as e:
            logger.warning(f"Partition info not available: {e}")
            return []
    
    def check_alerts(self) -> List[Dict[str, any]]:
        """Check for database alerts and issues."""
        alerts = []
        
        try:
            with self.engine.connect() as conn:
                # Check for high connection usage
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active'
                """)).scalar()
                
                if result > 50:  # Threshold for high connection usage
                    alerts.append({
                        "level": "warning",
                        "type": "high_connections",
                        "message": f"High active connection count: {result}",
                        "recommendation": "Check connection pooling configuration"
                    })
                
                # Check for low cache hit ratio
                result = conn.execute(text("""
                    SELECT ROUND(
                        sum(heap_blks_hit) / GREATEST(sum(heap_blks_hit + heap_blks_read), 1) * 100, 2
                    ) FROM pg_statio_user_tables
                """)).scalar()
                
                if result and result < 95:
                    alerts.append({
                        "level": "warning",
                        "type": "low_cache_hit",
                        "message": f"Low cache hit ratio: {result}%",
                        "recommendation": "Consider increasing shared_buffers"
                    })
                
                # Check for unused indexes
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM pg_stat_user_indexes WHERE idx_scan = 0
                """)).scalar()
                
                if result > 10:
                    alerts.append({
                        "level": "info",
                        "type": "unused_indexes",
                        "message": f"Found {result} unused indexes",
                        "recommendation": "Review and consider dropping unused indexes"
                    })
                
                # Check for failed executions in last hour
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM workflow_executions 
                    WHERE status = 'failed' AND started_at > NOW() - INTERVAL '1 hour'
                """)).scalar()
                
                if result > 10:
                    alerts.append({
                        "level": "error",
                        "type": "high_failure_rate",
                        "message": f"High workflow failure rate: {result} failures in last hour",
                        "recommendation": "Check workflow configurations and error logs"
                    })
                
                # Check for long-running executions
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM workflow_executions 
                    WHERE status = 'running' AND started_at < NOW() - INTERVAL '1 hour'
                """)).scalar()
                
                if result > 0:
                    alerts.append({
                        "level": "warning",
                        "type": "long_running_executions",
                        "message": f"Found {result} executions running for over 1 hour",
                        "recommendation": "Check for stuck workflows and consider timeout settings"
                    })
                
        except Exception as e:
            alerts.append({
                "level": "error",
                "type": "monitoring_error",
                "message": f"Error checking alerts: {e}",
                "recommendation": "Check database connectivity and permissions"
            })
        
        return alerts
    
    def get_system_metrics(self) -> Dict[str, any]:
        """Get system-level metrics."""
        try:
            return {
                "cpu": {
                    "usage_percent": psutil.cpu_percent(interval=1),
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent,
                    "used": psutil.virtual_memory().used
                },
                "disk": {
                    "total": psutil.disk_usage('/').total,
                    "used": psutil.disk_usage('/').used,
                    "free": psutil.disk_usage('/').free,
                    "percent": psutil.disk_usage('/').percent
                }
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {"error": str(e)}
    
    def generate_report(self) -> Dict[str, any]:
        """Generate comprehensive performance report."""
        logger.info("Generating database performance report...")
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "performance_metrics": self.get_performance_metrics(),
            "system_metrics": self.get_system_metrics(),
            "table_sizes": self.get_table_sizes(),
            "slow_queries": self.get_slow_queries(),
            "partition_info": self.get_partition_info(),
            "alerts": self.check_alerts()
        }
        
        return report


# Flask web dashboard
app = Flask(__name__)
monitor = None

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Database Monitoring Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #2c3e50; }
        .metric-value { font-size: 24px; font-weight: bold; color: #3498db; }
        .metric-label { font-size: 14px; color: #7f8c8d; }
        .alert { padding: 10px; margin: 5px 0; border-radius: 4px; }
        .alert-error { background: #e74c3c; color: white; }
        .alert-warning { background: #f39c12; color: white; }
        .alert-info { background: #3498db; color: white; }
        .table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        .table th, .table td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        .table th { background: #f8f9fa; }
        .refresh-btn { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .refresh-btn:hover { background: #2980b9; }
    </style>
    <script>
        function refreshData() {
            location.reload();
        }
        
        // Auto-refresh every 30 seconds
        setInterval(refreshData, 30000);
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🗄️ Database Monitoring Dashboard</h1>
            <p>Workflow Platform - Real-time Database Performance</p>
            <button class="refresh-btn" onclick="refreshData()">🔄 Refresh</button>
        </div>
        
        <div id="alerts">
            {% for alert in data.alerts %}
            <div class="alert alert-{{ alert.level }}">
                <strong>{{ alert.type.replace('_', ' ').title() }}:</strong> {{ alert.message }}
                <br><small>💡 {{ alert.recommendation }}</small>
            </div>
            {% endfor %}
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-title">📊 Database</div>
                <div class="metric-value">{{ data.performance_metrics.database.size }}</div>
                <div class="metric-label">Total Size</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">🔗 Connections</div>
                <div class="metric-value">{{ data.performance_metrics.connections.active }}</div>
                <div class="metric-label">Active ({{ data.performance_metrics.connections.total }} total)</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">⚡ Cache Hit Ratio</div>
                <div class="metric-value">{{ data.performance_metrics.cache.hit_ratio }}%</div>
                <div class="metric-label">Buffer Cache Performance</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">🔄 Workflows (24h)</div>
                <div class="metric-value">{{ data.performance_metrics.executions_24h.total }}</div>
                <div class="metric-label">{{ data.performance_metrics.executions_24h.success_rate }}% success rate</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">🤖 Active Workflows</div>
                <div class="metric-value">{{ data.performance_metrics.workflows.active }}</div>
                <div class="metric-label">{{ data.performance_metrics.workflows.public }} public</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">🧠 Active Agents</div>
                <div class="metric-value">{{ data.performance_metrics.agents.active }}</div>
                <div class="metric-label">{{ data.performance_metrics.agents.public }} public</div>
            </div>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-title">📈 System CPU</div>
                <div class="metric-value">{{ "%.1f"|format(data.system_metrics.cpu.usage_percent) }}%</div>
                <div class="metric-label">{{ data.system_metrics.cpu.count }} cores</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">💾 System Memory</div>
                <div class="metric-value">{{ "%.1f"|format(data.system_metrics.memory.percent) }}%</div>
                <div class="metric-label">{{ "%.1f"|format(data.system_metrics.memory.used / 1024**3) }}GB used</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">💿 System Disk</div>
                <div class="metric-value">{{ "%.1f"|format(data.system_metrics.disk.percent) }}%</div>
                <div class="metric-label">{{ "%.1f"|format(data.system_metrics.disk.free / 1024**3) }}GB free</div>
            </div>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">📋 Largest Tables</div>
            <table class="table">
                <thead>
                    <tr>
                        <th>Table</th>
                        <th>Size</th>
                        <th>Operations</th>
                    </tr>
                </thead>
                <tbody>
                    {% for table in data.table_sizes[:10] %}
                    <tr>
                        <td>{{ table.table }}</td>
                        <td>{{ table.size }}</td>
                        <td>{{ "{:,}".format(table.operations) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        {% if data.slow_queries %}
        <div class="metric-card">
            <div class="metric-title">🐌 Slow Queries</div>
            <table class="table">
                <thead>
                    <tr>
                        <th>Query</th>
                        <th>Calls</th>
                        <th>Avg Time (ms)</th>
                        <th>Cache Hit %</th>
                    </tr>
                </thead>
                <tbody>
                    {% for query in data.slow_queries[:5] %}
                    <tr>
                        <td><code>{{ query.query }}</code></td>
                        <td>{{ query.calls }}</td>
                        <td>{{ query.avg_time }}</td>
                        <td>{{ query.hit_percent }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
        
        {% if data.partition_info %}
        <div class="metric-card">
            <div class="metric-title">🗂️ Partition Information</div>
            <table class="table">
                <thead>
                    <tr>
                        <th>Table Family</th>
                        <th>Partition</th>
                        <th>Date</th>
                        <th>Size</th>
                    </tr>
                </thead>
                <tbody>
                    {% for partition in data.partition_info[:10] %}
                    <tr>
                        <td>{{ partition.table_family }}</td>
                        <td>{{ partition.table }}</td>
                        <td>{{ partition.partition_date or 'N/A' }}</td>
                        <td>{{ partition.size }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
        
        <div class="metric-card">
            <div class="metric-title">ℹ️ Report Generated</div>
            <p>{{ data.timestamp }}</p>
            <p><small>Auto-refreshes every 30 seconds</small></p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Main dashboard route."""
    try:
        data = monitor.generate_report()
        return render_template_string(DASHBOARD_HTML, data=data)
    except Exception as e:
        return f"Error generating dashboard: {e}", 500

@app.route('/api/metrics')
def api_metrics():
    """API endpoint for metrics."""
    try:
        return jsonify(monitor.generate_report())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health')
def api_health():
    """Health check endpoint."""
    try:
        alerts = monitor.check_alerts()
        error_alerts = [a for a in alerts if a['level'] == 'error']
        
        return jsonify({
            "status": "error" if error_alerts else "healthy",
            "alerts": len(alerts),
            "errors": len(error_alerts)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Database Monitoring Dashboard")
    parser.add_argument("--server", action="store_true", 
                       help="Start web dashboard server")
    parser.add_argument("--port", type=int, default=5001,
                       help="Web server port (default: 5001)")
    parser.add_argument("--report", action="store_true", 
                       help="Generate performance report")
    parser.add_argument("--alerts", action="store_true", 
                       help="Check for alerts")
    parser.add_argument("--json", action="store_true", 
                       help="Output in JSON format")
    
    args = parser.parse_args()
    
    global monitor
    monitor = DatabaseMonitor()
    
    try:
        if args.server:
            logger.info(f"Starting database monitoring dashboard on port {args.port}")
            logger.info(f"Access dashboard at: http://localhost:{args.port}")
            app.run(host='0.0.0.0', port=args.port, debug=False)
        
        elif args.report:
            report = monitor.generate_report()
            if args.json:
                print(json.dumps(report, indent=2, default=str))
            else:
                print("=== DATABASE PERFORMANCE REPORT ===")
                print(f"Generated: {report['timestamp']}")
                print()
                
                # Performance metrics
                perf = report['performance_metrics']
                print("📊 Database Metrics:")
                print(f"  Size: {perf['database']['size']}")
                print(f"  Active Connections: {perf['connections']['active']}")
                print(f"  Cache Hit Ratio: {perf['cache']['hit_ratio']}%")
                print()
                
                # Workflow metrics
                print("🔄 Workflow Platform Metrics (24h):")
                exec_24h = perf['executions_24h']
                print(f"  Total Executions: {exec_24h['total']}")
                print(f"  Success Rate: {exec_24h['success_rate']}%")
                print(f"  Average Duration: {exec_24h['avg_duration_ms']}ms")
                print(f"  Active Workflows: {perf['workflows']['active']}")
                print(f"  Active Agents: {perf['agents']['active']}")
                print()
                
                # Alerts
                if report['alerts']:
                    print("🚨 Alerts:")
                    for alert in report['alerts']:
                        level_icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}
                        print(f"  {level_icon.get(alert['level'], '•')} {alert['message']}")
                    print()
                
                # Top tables
                print("📋 Largest Tables:")
                for table in report['table_sizes'][:5]:
                    print(f"  {table['table']}: {table['size']}")
        
        elif args.alerts:
            alerts = monitor.check_alerts()
            if args.json:
                print(json.dumps(alerts, indent=2))
            else:
                if alerts:
                    print("🚨 Database Alerts:")
                    for alert in alerts:
                        level_icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}
                        print(f"{level_icon.get(alert['level'], '•')} {alert['message']}")
                        print(f"   💡 {alert['recommendation']}")
                        print()
                else:
                    print("✅ No alerts found - database is healthy!")
        
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()