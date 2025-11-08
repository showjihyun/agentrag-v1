"""
ML-based Anomaly Detection for System Monitoring

Provides real-time anomaly detection and predictive maintenance.
"""

import logging
import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import redis.asyncio as redis


logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System metrics data."""
    
    timestamp: str
    response_time: float  # milliseconds
    error_rate: float  # percentage
    cpu_usage: float  # percentage
    memory_usage: float  # percentage
    request_rate: float  # requests per second
    cache_hit_rate: float  # percentage
    db_connections: int
    active_users: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_feature_vector(self) -> np.ndarray:
        """Convert to feature vector for ML."""
        return np.array([
            self.response_time,
            self.error_rate,
            self.cpu_usage,
            self.memory_usage,
            self.request_rate,
            self.cache_hit_rate,
            self.db_connections,
            self.active_users
        ])


@dataclass
class Anomaly:
    """Anomaly detection result."""
    
    timestamp: str
    severity: str  # low, medium, high, critical
    score: float  # anomaly score
    metrics: SystemMetrics
    affected_metrics: List[str]
    recommendation: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        data["metrics"] = self.metrics.to_dict()
        return data


class AnomalyDetector:
    """
    ML-based anomaly detection for system monitoring.
    
    Features:
    - Real-time anomaly detection
    - Automatic alerting
    - Pattern learning
    - Predictive maintenance
    - Root cause analysis
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        contamination: float = 0.1,
        training_window_hours: int = 24,
        detection_interval_seconds: int = 60
    ):
        """
        Initialize Anomaly Detector.
        
        Args:
            redis_client: Redis client
            contamination: Expected proportion of anomalies
            training_window_hours: Hours of data for training
            detection_interval_seconds: Detection interval
        """
        self.redis = redis_client
        self.contamination = contamination
        self.training_window_hours = training_window_hours
        self.detection_interval = detection_interval_seconds
        
        # ML models
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.trained = False
        
        # Detection state
        self.running = False
        self._detection_task: Optional[asyncio.Task] = None
        
        # Baseline metrics
        self.baseline = {
            "response_time": {"mean": 0, "std": 0},
            "error_rate": {"mean": 0, "std": 0},
            "cpu_usage": {"mean": 0, "std": 0},
            "memory_usage": {"mean": 0, "std": 0},
            "request_rate": {"mean": 0, "std": 0},
            "cache_hit_rate": {"mean": 0, "std": 0}
        }
    
    async def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        
        # Get metrics from Redis
        # In production, integrate with actual monitoring system
        
        metrics = SystemMetrics(
            timestamp=datetime.utcnow().isoformat(),
            response_time=await self._get_avg_response_time(),
            error_rate=await self._get_error_rate(),
            cpu_usage=await self._get_cpu_usage(),
            memory_usage=await self._get_memory_usage(),
            request_rate=await self._get_request_rate(),
            cache_hit_rate=await self._get_cache_hit_rate(),
            db_connections=await self._get_db_connections(),
            active_users=await self._get_active_users()
        )
        
        # Store metrics
        await self._store_metrics(metrics)
        
        return metrics
    
    async def _get_avg_response_time(self) -> float:
        """Get average response time."""
        # Get from monitoring system
        value = await self.redis.get("metrics:response_time:avg")
        return float(value) if value else 100.0
    
    async def _get_error_rate(self) -> float:
        """Get error rate."""
        value = await self.redis.get("metrics:error_rate")
        return float(value) if value else 0.5
    
    async def _get_cpu_usage(self) -> float:
        """Get CPU usage."""
        value = await self.redis.get("metrics:cpu_usage")
        return float(value) if value else 50.0
    
    async def _get_memory_usage(self) -> float:
        """Get memory usage."""
        value = await self.redis.get("metrics:memory_usage")
        return float(value) if value else 60.0
    
    async def _get_request_rate(self) -> float:
        """Get request rate."""
        value = await self.redis.get("metrics:request_rate")
        return float(value) if value else 10.0
    
    async def _get_cache_hit_rate(self) -> float:
        """Get cache hit rate."""
        value = await self.redis.get("metrics:cache_hit_rate")
        return float(value) if value else 85.0
    
    async def _get_db_connections(self) -> int:
        """Get database connections."""
        value = await self.redis.get("metrics:db_connections")
        return int(value) if value else 20
    
    async def _get_active_users(self) -> int:
        """Get active users."""
        value = await self.redis.get("metrics:active_users")
        return int(value) if value else 100
    
    async def _store_metrics(self, metrics: SystemMetrics):
        """Store metrics in time series."""
        key = f"metrics:history:{datetime.utcnow().strftime('%Y-%m-%d-%H')}"
        
        await self.redis.lpush(key, json.dumps(metrics.to_dict()))
        await self.redis.ltrim(key, 0, 999)  # Keep last 1000 entries
        await self.redis.expire(key, 86400 * 7)  # 7 days
    
    async def train(self, historical_data: Optional[List[SystemMetrics]] = None):
        """
        Train anomaly detection model.
        
        Args:
            historical_data: Historical metrics (if None, load from Redis)
        """
        if historical_data is None:
            historical_data = await self._load_historical_data()
        
        if len(historical_data) < 100:
            logger.warning(
                f"Insufficient training data: {len(historical_data)} samples. "
                "Need at least 100 samples."
            )
            return
        
        # Convert to feature matrix
        X = np.array([m.to_feature_vector() for m in historical_data])
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled)
        self.trained = True
        
        # Calculate baseline statistics
        self._calculate_baseline(historical_data)
        
        logger.info(
            f"Anomaly detector trained on {len(historical_data)} samples",
            extra={"samples": len(historical_data), "contamination": self.contamination}
        )
    
    def _calculate_baseline(self, data: List[SystemMetrics]):
        """Calculate baseline statistics."""
        
        metrics_arrays = {
            "response_time": [m.response_time for m in data],
            "error_rate": [m.error_rate for m in data],
            "cpu_usage": [m.cpu_usage for m in data],
            "memory_usage": [m.memory_usage for m in data],
            "request_rate": [m.request_rate for m in data],
            "cache_hit_rate": [m.cache_hit_rate for m in data]
        }
        
        for metric_name, values in metrics_arrays.items():
            self.baseline[metric_name] = {
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
                "min": float(np.min(values)),
                "max": float(np.max(values))
            }
    
    async def _load_historical_data(self) -> List[SystemMetrics]:
        """Load historical data from Redis."""
        
        historical_data = []
        
        # Load last N hours of data
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=self.training_window_hours)
        
        current = start_time
        while current <= end_time:
            key = f"metrics:history:{current.strftime('%Y-%m-%d-%H')}"
            
            data = await self.redis.lrange(key, 0, -1)
            
            for item in data:
                try:
                    metrics_dict = json.loads(item)
                    metrics = SystemMetrics(**metrics_dict)
                    historical_data.append(metrics)
                except Exception as e:
                    logger.error(f"Failed to parse metrics: {e}")
            
            current += timedelta(hours=1)
        
        return historical_data
    
    async def detect_anomaly(
        self,
        metrics: Optional[SystemMetrics] = None
    ) -> Tuple[bool, Optional[Anomaly]]:
        """
        Detect anomaly in current metrics.
        
        Args:
            metrics: System metrics (if None, collect current)
            
        Returns:
            Tuple of (is_anomaly, anomaly_details)
        """
        if not self.trained:
            logger.warning("Model not trained, skipping anomaly detection")
            return False, None
        
        if metrics is None:
            metrics = await self.collect_metrics()
        
        # Convert to feature vector
        X = metrics.to_feature_vector().reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        
        # Predict
        prediction = self.model.predict(X_scaled)[0]
        score = self.model.score_samples(X_scaled)[0]
        
        is_anomaly = prediction == -1
        
        if is_anomaly:
            # Analyze anomaly
            anomaly = await self._analyze_anomaly(metrics, score)
            
            # Send alert
            await self._send_alert(anomaly)
            
            return True, anomaly
        
        return False, None
    
    async def _analyze_anomaly(
        self,
        metrics: SystemMetrics,
        score: float
    ) -> Anomaly:
        """Analyze anomaly and determine severity."""
        
        # Identify affected metrics
        affected_metrics = []
        
        for metric_name, baseline in self.baseline.items():
            value = getattr(metrics, metric_name)
            mean = baseline["mean"]
            std = baseline["std"]
            
            # Check if value is outside 3 standard deviations
            if abs(value - mean) > 3 * std:
                affected_metrics.append(metric_name)
        
        # Determine severity
        severity = self._determine_severity(score, affected_metrics)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(affected_metrics, metrics)
        
        return Anomaly(
            timestamp=metrics.timestamp,
            severity=severity,
            score=float(score),
            metrics=metrics,
            affected_metrics=affected_metrics,
            recommendation=recommendation
        )
    
    def _determine_severity(
        self,
        score: float,
        affected_metrics: List[str]
    ) -> str:
        """Determine anomaly severity."""
        
        # Score-based severity
        if score < -0.5:
            severity = "critical"
        elif score < -0.3:
            severity = "high"
        elif score < -0.1:
            severity = "medium"
        else:
            severity = "low"
        
        # Adjust based on affected metrics
        critical_metrics = ["error_rate", "response_time"]
        if any(m in affected_metrics for m in critical_metrics):
            if severity == "medium":
                severity = "high"
            elif severity == "low":
                severity = "medium"
        
        return severity
    
    def _generate_recommendation(
        self,
        affected_metrics: List[str],
        metrics: SystemMetrics
    ) -> str:
        """Generate recommendation based on anomaly."""
        
        recommendations = []
        
        if "response_time" in affected_metrics:
            if metrics.response_time > self.baseline["response_time"]["mean"] * 2:
                recommendations.append(
                    "High response time detected. Check database queries and cache performance."
                )
        
        if "error_rate" in affected_metrics:
            if metrics.error_rate > 5:
                recommendations.append(
                    "High error rate detected. Check application logs and external service status."
                )
        
        if "cpu_usage" in affected_metrics:
            if metrics.cpu_usage > 80:
                recommendations.append(
                    "High CPU usage detected. Consider scaling horizontally or optimizing code."
                )
        
        if "memory_usage" in affected_metrics:
            if metrics.memory_usage > 85:
                recommendations.append(
                    "High memory usage detected. Check for memory leaks and optimize caching."
                )
        
        if "cache_hit_rate" in affected_metrics:
            if metrics.cache_hit_rate < 70:
                recommendations.append(
                    "Low cache hit rate detected. Review cache strategy and TTL settings."
                )
        
        if not recommendations:
            recommendations.append("Anomaly detected. Monitor system closely.")
        
        return " ".join(recommendations)
    
    async def _send_alert(self, anomaly: Anomaly):
        """Send anomaly alert."""
        
        # Store alert
        alert_key = f"alert:anomaly:{datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')}"
        await self.redis.setex(
            alert_key,
            86400 * 7,  # 7 days
            json.dumps(anomaly.to_dict())
        )
        
        # Log alert
        logger.warning(
            f"Anomaly detected: {anomaly.severity}",
            extra={
                "severity": anomaly.severity,
                "score": anomaly.score,
                "affected_metrics": anomaly.affected_metrics,
                "recommendation": anomaly.recommendation
            }
        )
        
        # TODO: Send actual notification (email, Slack, PagerDuty, etc.)
    
    async def start_monitoring(self):
        """Start continuous anomaly monitoring."""
        
        if self.running:
            logger.warning("Anomaly monitoring already running")
            return
        
        if not self.trained:
            logger.info("Training model before starting monitoring...")
            await self.train()
        
        self.running = True
        self._detection_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Anomaly monitoring started")
    
    async def stop_monitoring(self):
        """Stop anomaly monitoring."""
        
        self.running = False
        
        if self._detection_task:
            self._detection_task.cancel()
            try:
                await self._detection_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Anomaly monitoring stopped")
    
    async def _monitoring_loop(self):
        """Continuous monitoring loop."""
        
        while self.running:
            try:
                # Detect anomaly
                is_anomaly, anomaly = await self.detect_anomaly()
                
                if is_anomaly:
                    logger.info(f"Anomaly detected: {anomaly.severity}")
                
                # Wait for next interval
                await asyncio.sleep(self.detection_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(1)
    
    async def get_recent_anomalies(
        self,
        hours: int = 24,
        severity: Optional[str] = None
    ) -> List[Anomaly]:
        """
        Get recent anomalies.
        
        Args:
            hours: Hours to look back
            severity: Filter by severity
            
        Returns:
            List of anomalies
        """
        anomalies = []
        
        # Get alert keys
        keys = await self.redis.keys("alert:anomaly:*")
        
        for key in keys:
            data = await self.redis.get(key)
            if data:
                try:
                    anomaly_dict = json.loads(data)
                    
                    # Reconstruct Anomaly object
                    metrics_dict = anomaly_dict["metrics"]
                    anomaly_dict["metrics"] = SystemMetrics(**metrics_dict)
                    
                    anomaly = Anomaly(**anomaly_dict)
                    
                    # Filter by time
                    timestamp = datetime.fromisoformat(anomaly.timestamp)
                    if datetime.utcnow() - timestamp <= timedelta(hours=hours):
                        # Filter by severity
                        if severity is None or anomaly.severity == severity:
                            anomalies.append(anomaly)
                
                except Exception as e:
                    logger.error(f"Failed to parse anomaly: {e}")
        
        # Sort by timestamp (newest first)
        anomalies.sort(key=lambda x: x.timestamp, reverse=True)
        
        return anomalies


# Global anomaly detector instance
_anomaly_detector: Optional[AnomalyDetector] = None


def get_anomaly_detector() -> AnomalyDetector:
    """Get global anomaly detector instance."""
    global _anomaly_detector
    if _anomaly_detector is None:
        raise RuntimeError("Anomaly detector not initialized")
    return _anomaly_detector


async def initialize_anomaly_detector(
    redis_client: redis.Redis,
    contamination: float = 0.1
) -> AnomalyDetector:
    """
    Initialize global anomaly detector.
    
    Args:
        redis_client: Redis client
        contamination: Expected anomaly proportion
        
    Returns:
        Anomaly detector instance
    """
    global _anomaly_detector
    if _anomaly_detector is None:
        _anomaly_detector = AnomalyDetector(
            redis_client=redis_client,
            contamination=contamination
        )
    return _anomaly_detector


async def cleanup_anomaly_detector():
    """Cleanup global anomaly detector."""
    global _anomaly_detector
    if _anomaly_detector is not None:
        await _anomaly_detector.stop_monitoring()
        _anomaly_detector = None
