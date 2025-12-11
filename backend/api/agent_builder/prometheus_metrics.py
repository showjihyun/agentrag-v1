"""
Prometheus Metrics Export API

Exposes metrics in Prometheus format for monitoring and alerting.
"""

import logging
from typing import Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.db.database import get_db
from backend.db.models.flows import TokenUsage
from backend.db.models.agent_builder import WorkflowExecution, AgentExecution

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/metrics",
    tags=["prometheus-metrics"],
)


class PrometheusMetricsCollector:
    """Collects and formats metrics for Prometheus."""
    
    def __init__(self, db: Session):
        self.db = db
        self.metrics: list = []
    
    def add_metric(
        self,
        name: str,
        value: float,
        metric_type: str = "gauge",
        help_text: str = "",
        labels: Dict[str, str] = None,
    ):
        """Add a metric to the collection."""
        self.metrics.append({
            "name": name,
            "value": value,
            "type": metric_type,
            "help": help_text,
            "labels": labels or {},
        })
    
    def format_prometheus(self) -> str:
        """Format metrics in Prometheus exposition format."""
        lines = []
        seen_metrics = set()
        
        for metric in self.metrics:
            name = metric["name"]
            
            # Add HELP and TYPE only once per metric name
            if name not in seen_metrics:
                if metric["help"]:
                    lines.append(f"# HELP {name} {metric['help']}")
                lines.append(f"# TYPE {name} {metric['type']}")
                seen_metrics.add(name)
            
            # Format labels
            if metric["labels"]:
                label_str = ",".join(f'{k}="{v}"' for k, v in metric["labels"].items())
                lines.append(f"{name}{{{label_str}}} {metric['value']}")
            else:
                lines.append(f"{name} {metric['value']}")
        
        return "\n".join(lines) + "\n"
    
    def collect_workflow_metrics(self):
        """Collect workflow execution metrics."""
        try:
            # Total executions
            total = self.db.query(func.count(WorkflowExecution.id)).scalar() or 0
            self.add_metric(
                "agenticrag_workflow_executions_total",
                total,
                "counter",
                "Total number of workflow executions",
            )
            
            # Executions by status
            status_counts = self.db.query(
                WorkflowExecution.status,
                func.count(WorkflowExecution.id)
            ).group_by(WorkflowExecution.status).all()
            
            for status, count in status_counts:
                self.add_metric(
                    "agenticrag_workflow_executions_by_status",
                    count,
                    "gauge",
                    "Workflow executions by status",
                    {"status": status or "unknown"},
                )
            
            # Recent executions (last hour)
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            recent = self.db.query(func.count(WorkflowExecution.id)).filter(
                WorkflowExecution.started_at >= one_hour_ago
            ).scalar() or 0
            self.add_metric(
                "agenticrag_workflow_executions_last_hour",
                recent,
                "gauge",
                "Workflow executions in the last hour",
            )
            
            # Average execution duration (completed workflows)
            avg_duration = self.db.query(
                func.avg(
                    func.extract('epoch', WorkflowExecution.completed_at) -
                    func.extract('epoch', WorkflowExecution.started_at)
                )
            ).filter(
                WorkflowExecution.status == "completed",
                WorkflowExecution.completed_at.isnot(None),
            ).scalar()
            
            if avg_duration:
                self.add_metric(
                    "agenticrag_workflow_execution_duration_seconds_avg",
                    float(avg_duration),
                    "gauge",
                    "Average workflow execution duration in seconds",
                )
            
        except Exception as e:
            logger.error(f"Failed to collect workflow metrics: {e}")
    
    def collect_agent_metrics(self):
        """Collect agent execution metrics."""
        try:
            # Total agent executions
            total = self.db.query(func.count(AgentExecution.id)).scalar() or 0
            self.add_metric(
                "agenticrag_agent_executions_total",
                total,
                "counter",
                "Total number of agent executions",
            )
            
            # Agent executions by status
            status_counts = self.db.query(
                AgentExecution.status,
                func.count(AgentExecution.id)
            ).group_by(AgentExecution.status).all()
            
            for status, count in status_counts:
                self.add_metric(
                    "agenticrag_agent_executions_by_status",
                    count,
                    "gauge",
                    "Agent executions by status",
                    {"status": status or "unknown"},
                )
            
            # Average agent execution duration
            avg_duration = self.db.query(func.avg(AgentExecution.duration_ms)).filter(
                AgentExecution.status == "completed",
                AgentExecution.duration_ms.isnot(None),
            ).scalar()
            
            if avg_duration:
                self.add_metric(
                    "agenticrag_agent_execution_duration_ms_avg",
                    float(avg_duration),
                    "gauge",
                    "Average agent execution duration in milliseconds",
                )
            
        except Exception as e:
            logger.error(f"Failed to collect agent metrics: {e}")
    
    def collect_token_usage_metrics(self):
        """Collect LLM token usage metrics."""
        try:
            # Total tokens used
            totals = self.db.query(
                func.sum(TokenUsage.input_tokens),
                func.sum(TokenUsage.output_tokens),
                func.sum(TokenUsage.total_tokens),
                func.sum(TokenUsage.cost_usd),
            ).first()
            
            if totals:
                input_tokens, output_tokens, total_tokens, total_cost = totals
                
                self.add_metric(
                    "agenticrag_llm_input_tokens_total",
                    float(input_tokens or 0),
                    "counter",
                    "Total LLM input tokens used",
                )
                self.add_metric(
                    "agenticrag_llm_output_tokens_total",
                    float(output_tokens or 0),
                    "counter",
                    "Total LLM output tokens used",
                )
                self.add_metric(
                    "agenticrag_llm_tokens_total",
                    float(total_tokens or 0),
                    "counter",
                    "Total LLM tokens used",
                )
                self.add_metric(
                    "agenticrag_llm_cost_usd_total",
                    float(total_cost or 0),
                    "counter",
                    "Total LLM cost in USD",
                )
            
            # Tokens by provider
            provider_usage = self.db.query(
                TokenUsage.provider,
                func.sum(TokenUsage.total_tokens),
                func.sum(TokenUsage.cost_usd),
            ).group_by(TokenUsage.provider).all()
            
            for provider, tokens, cost in provider_usage:
                self.add_metric(
                    "agenticrag_llm_tokens_by_provider",
                    float(tokens or 0),
                    "gauge",
                    "LLM tokens by provider",
                    {"provider": provider or "unknown"},
                )
                self.add_metric(
                    "agenticrag_llm_cost_by_provider",
                    float(cost or 0),
                    "gauge",
                    "LLM cost by provider in USD",
                    {"provider": provider or "unknown"},
                )
            
            # Tokens by model
            model_usage = self.db.query(
                TokenUsage.model,
                TokenUsage.provider,
                func.sum(TokenUsage.total_tokens),
                func.count(TokenUsage.id),
            ).group_by(TokenUsage.model, TokenUsage.provider).all()
            
            for model, provider, tokens, count in model_usage:
                self.add_metric(
                    "agenticrag_llm_tokens_by_model",
                    float(tokens or 0),
                    "gauge",
                    "LLM tokens by model",
                    {"model": model or "unknown", "provider": provider or "unknown"},
                )
                self.add_metric(
                    "agenticrag_llm_requests_by_model",
                    float(count or 0),
                    "gauge",
                    "LLM requests by model",
                    {"model": model or "unknown", "provider": provider or "unknown"},
                )
            
            # Last 24 hours usage
            one_day_ago = datetime.utcnow() - timedelta(days=1)
            daily_totals = self.db.query(
                func.sum(TokenUsage.total_tokens),
                func.sum(TokenUsage.cost_usd),
                func.count(TokenUsage.id),
            ).filter(TokenUsage.created_at >= one_day_ago).first()
            
            if daily_totals:
                tokens_24h, cost_24h, requests_24h = daily_totals
                self.add_metric(
                    "agenticrag_llm_tokens_last_24h",
                    float(tokens_24h or 0),
                    "gauge",
                    "LLM tokens used in last 24 hours",
                )
                self.add_metric(
                    "agenticrag_llm_cost_last_24h",
                    float(cost_24h or 0),
                    "gauge",
                    "LLM cost in last 24 hours (USD)",
                )
                self.add_metric(
                    "agenticrag_llm_requests_last_24h",
                    float(requests_24h or 0),
                    "gauge",
                    "LLM requests in last 24 hours",
                )
            
        except Exception as e:
            logger.error(f"Failed to collect token usage metrics: {e}")
    
    def collect_system_metrics(self):
        """Collect system-level metrics."""
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.add_metric(
                "agenticrag_system_cpu_percent",
                cpu_percent,
                "gauge",
                "System CPU usage percentage",
            )
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.add_metric(
                "agenticrag_system_memory_percent",
                memory.percent,
                "gauge",
                "System memory usage percentage",
            )
            self.add_metric(
                "agenticrag_system_memory_used_bytes",
                memory.used,
                "gauge",
                "System memory used in bytes",
            )
            self.add_metric(
                "agenticrag_system_memory_available_bytes",
                memory.available,
                "gauge",
                "System memory available in bytes",
            )
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.add_metric(
                "agenticrag_system_disk_percent",
                disk.percent,
                "gauge",
                "System disk usage percentage",
            )
            
        except ImportError:
            logger.warning("psutil not installed, skipping system metrics")
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    def collect_all(self):
        """Collect all metrics."""
        self.collect_workflow_metrics()
        self.collect_agent_metrics()
        self.collect_token_usage_metrics()
        self.collect_system_metrics()


@router.get("/prometheus")
async def get_prometheus_metrics(db: Session = Depends(get_db)):
    """
    Export metrics in Prometheus format.
    
    This endpoint is designed to be scraped by Prometheus.
    Configure your prometheus.yml to scrape this endpoint:
    
    ```yaml
    scrape_configs:
      - job_name: 'agenticrag'
        static_configs:
          - targets: ['localhost:8000']
        metrics_path: '/api/agent-builder/metrics/prometheus'
    ```
    """
    collector = PrometheusMetricsCollector(db)
    collector.collect_all()
    
    return Response(
        content=collector.format_prometheus(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@router.get("/json")
async def get_metrics_json(db: Session = Depends(get_db)):
    """
    Export metrics in JSON format.
    
    Useful for debugging and custom dashboards.
    """
    collector = PrometheusMetricsCollector(db)
    collector.collect_all()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": collector.metrics,
    }


@router.get("/summary")
async def get_metrics_summary(db: Session = Depends(get_db)):
    """
    Get a human-readable metrics summary.
    """
    try:
        # Workflow stats
        workflow_total = db.query(func.count(WorkflowExecution.id)).scalar() or 0
        workflow_completed = db.query(func.count(WorkflowExecution.id)).filter(
            WorkflowExecution.status == "completed"
        ).scalar() or 0
        workflow_failed = db.query(func.count(WorkflowExecution.id)).filter(
            WorkflowExecution.status == "failed"
        ).scalar() or 0
        
        # Agent stats
        agent_total = db.query(func.count(AgentExecution.id)).scalar() or 0
        agent_completed = db.query(func.count(AgentExecution.id)).filter(
            AgentExecution.status == "completed"
        ).scalar() or 0
        
        # Token usage stats
        token_stats = db.query(
            func.sum(TokenUsage.total_tokens),
            func.sum(TokenUsage.cost_usd),
            func.count(TokenUsage.id),
        ).first()
        
        total_tokens = token_stats[0] or 0 if token_stats else 0
        total_cost = token_stats[1] or 0 if token_stats else 0
        total_requests = token_stats[2] or 0 if token_stats else 0
        
        # Calculate success rates
        workflow_success_rate = (workflow_completed / workflow_total * 100) if workflow_total > 0 else 0
        agent_success_rate = (agent_completed / agent_total * 100) if agent_total > 0 else 0
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "workflows": {
                "total": workflow_total,
                "completed": workflow_completed,
                "failed": workflow_failed,
                "success_rate": round(workflow_success_rate, 1),
            },
            "agents": {
                "total": agent_total,
                "completed": agent_completed,
                "success_rate": round(agent_success_rate, 1),
            },
            "llm_usage": {
                "total_tokens": total_tokens,
                "total_cost_usd": round(total_cost, 4),
                "total_requests": total_requests,
                "avg_tokens_per_request": round(total_tokens / total_requests, 1) if total_requests > 0 else 0,
            },
        }
        
    except Exception as e:
        logger.error(f"Failed to get metrics summary: {e}", exc_info=True)
        return {"error": str(e)}
