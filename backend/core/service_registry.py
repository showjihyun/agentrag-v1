"""
Service Registry for Service Discovery

Provides service registration and discovery for microservices architecture.
"""

import logging
import asyncio
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

import redis.asyncio as redis


logger = logging.getLogger(__name__)


@dataclass
class ServiceInstance:
    """Service instance information."""
    
    service_name: str
    instance_id: str
    host: str
    port: int
    protocol: str = "http"
    metadata: Dict[str, Any] = None
    health_check_url: Optional[str] = None
    registered_at: str = None
    last_heartbeat: str = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.registered_at is None:
            self.registered_at = datetime.utcnow().isoformat()
        if self.last_heartbeat is None:
            self.last_heartbeat = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServiceInstance":
        """Create from dictionary."""
        return cls(**data)
    
    def get_url(self) -> str:
        """Get service URL."""
        return f"{self.protocol}://{self.host}:{self.port}"


class ServiceRegistry:
    """
    Service Registry using Redis.
    
    Provides:
    - Service registration
    - Service discovery
    - Health checking
    - Load balancing
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        ttl: int = 30,  # Service TTL in seconds
        health_check_interval: int = 10  # Health check interval
    ):
        """
        Initialize Service Registry.
        
        Args:
            redis_client: Redis client
            ttl: Service instance TTL
            health_check_interval: Health check interval in seconds
        """
        self.redis = redis_client
        self.ttl = ttl
        self.health_check_interval = health_check_interval
        self.running = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._registered_instances: List[ServiceInstance] = []
    
    async def register(
        self,
        service_name: str,
        instance_id: str,
        host: str,
        port: int,
        protocol: str = "http",
        metadata: Optional[Dict[str, Any]] = None,
        health_check_url: Optional[str] = None
    ) -> ServiceInstance:
        """
        Register a service instance.
        
        Args:
            service_name: Service name
            instance_id: Unique instance ID
            host: Host address
            port: Port number
            protocol: Protocol (http, https, grpc)
            metadata: Additional metadata
            health_check_url: Health check endpoint
            
        Returns:
            Service instance
        """
        instance = ServiceInstance(
            service_name=service_name,
            instance_id=instance_id,
            host=host,
            port=port,
            protocol=protocol,
            metadata=metadata or {},
            health_check_url=health_check_url
        )
        
        # Store in Redis
        key = f"service:{service_name}:{instance_id}"
        await self.redis.setex(
            key,
            self.ttl,
            json.dumps(instance.to_dict())
        )
        
        # Add to service list
        await self.redis.sadd(f"services:{service_name}", instance_id)
        
        # Track locally for heartbeat
        self._registered_instances.append(instance)
        
        logger.info(
            f"Service registered: {service_name}/{instance_id} at {instance.get_url()}"
        )
        
        return instance
    
    async def deregister(
        self,
        service_name: str,
        instance_id: str
    ):
        """
        Deregister a service instance.
        
        Args:
            service_name: Service name
            instance_id: Instance ID
        """
        key = f"service:{service_name}:{instance_id}"
        
        # Remove from Redis
        await self.redis.delete(key)
        await self.redis.srem(f"services:{service_name}", instance_id)
        
        # Remove from local tracking
        self._registered_instances = [
            inst for inst in self._registered_instances
            if not (inst.service_name == service_name and inst.instance_id == instance_id)
        ]
        
        logger.info(f"Service deregistered: {service_name}/{instance_id}")
    
    async def discover(
        self,
        service_name: str
    ) -> List[ServiceInstance]:
        """
        Discover all instances of a service.
        
        Args:
            service_name: Service name
            
        Returns:
            List of service instances
        """
        # Get all instance IDs
        instance_ids = await self.redis.smembers(f"services:{service_name}")
        
        if not instance_ids:
            return []
        
        # Get instance details
        instances = []
        for instance_id in instance_ids:
            instance_id = instance_id.decode() if isinstance(instance_id, bytes) else instance_id
            key = f"service:{service_name}:{instance_id}"
            
            data = await self.redis.get(key)
            if data:
                instance_dict = json.loads(data)
                instances.append(ServiceInstance.from_dict(instance_dict))
        
        return instances
    
    async def get_instance(
        self,
        service_name: str,
        strategy: str = "round_robin"
    ) -> Optional[ServiceInstance]:
        """
        Get a service instance using load balancing strategy.
        
        Args:
            service_name: Service name
            strategy: Load balancing strategy (round_robin, random, least_connections)
            
        Returns:
            Service instance or None
        """
        instances = await self.discover(service_name)
        
        if not instances:
            logger.warning(f"No instances found for service: {service_name}")
            return None
        
        if strategy == "round_robin":
            # Simple round-robin (stateless)
            # In production, maintain state in Redis
            return instances[0]
        
        elif strategy == "random":
            import random
            return random.choice(instances)
        
        elif strategy == "least_connections":
            # Simplified: return first instance
            # In production, track actual connection counts
            return instances[0]
        
        else:
            return instances[0]
    
    async def heartbeat(
        self,
        service_name: str,
        instance_id: str
    ):
        """
        Send heartbeat to keep service alive.
        
        Args:
            service_name: Service name
            instance_id: Instance ID
        """
        key = f"service:{service_name}:{instance_id}"
        
        # Get current instance data
        data = await self.redis.get(key)
        if data:
            instance_dict = json.loads(data)
            instance_dict["last_heartbeat"] = datetime.utcnow().isoformat()
            
            # Update with new TTL
            await self.redis.setex(
                key,
                self.ttl,
                json.dumps(instance_dict)
            )
            
            logger.debug(f"Heartbeat sent: {service_name}/{instance_id}")
    
    async def start_heartbeat(self):
        """Start automatic heartbeat for registered instances."""
        if self.running:
            logger.warning("Heartbeat already running")
            return
        
        self.running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        logger.info("Heartbeat started")
    
    async def stop_heartbeat(self):
        """Stop automatic heartbeat."""
        self.running = False
        
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Heartbeat stopped")
    
    async def _heartbeat_loop(self):
        """Heartbeat loop."""
        while self.running:
            try:
                # Send heartbeat for all registered instances
                for instance in self._registered_instances:
                    await self.heartbeat(
                        instance.service_name,
                        instance.instance_id
                    )
                
                # Wait for next interval
                await asyncio.sleep(self.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}", exc_info=True)
                await asyncio.sleep(1)
    
    async def get_all_services(self) -> Dict[str, List[ServiceInstance]]:
        """
        Get all registered services.
        
        Returns:
            Dictionary of service name to instances
        """
        # Get all service names
        keys = await self.redis.keys("services:*")
        
        services = {}
        for key in keys:
            key_str = key.decode() if isinstance(key, bytes) else key
            service_name = key_str.replace("services:", "")
            
            instances = await self.discover(service_name)
            if instances:
                services[service_name] = instances
        
        return services
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all services.
        
        Returns:
            Health check results
        """
        services = await self.get_all_services()
        
        results = {
            "total_services": len(services),
            "total_instances": sum(len(instances) for instances in services.values()),
            "services": {}
        }
        
        for service_name, instances in services.items():
            results["services"][service_name] = {
                "instance_count": len(instances),
                "instances": [
                    {
                        "instance_id": inst.instance_id,
                        "url": inst.get_url(),
                        "last_heartbeat": inst.last_heartbeat
                    }
                    for inst in instances
                ]
            }
        
        return results


# Global service registry instance
_service_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """Get global service registry instance."""
    global _service_registry
    if _service_registry is None:
        raise RuntimeError("Service registry not initialized")
    return _service_registry


async def initialize_service_registry(
    redis_client: redis.Redis,
    ttl: int = 30,
    health_check_interval: int = 10
) -> ServiceRegistry:
    """
    Initialize global service registry.
    
    Args:
        redis_client: Redis client
        ttl: Service TTL
        health_check_interval: Health check interval
        
    Returns:
        Service registry instance
    """
    global _service_registry
    if _service_registry is None:
        _service_registry = ServiceRegistry(
            redis_client=redis_client,
            ttl=ttl,
            health_check_interval=health_check_interval
        )
    return _service_registry


async def cleanup_service_registry():
    """Cleanup global service registry."""
    global _service_registry
    if _service_registry is not None:
        await _service_registry.stop_heartbeat()
        _service_registry = None
