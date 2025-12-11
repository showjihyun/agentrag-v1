"""
Workflow Versioning System

Manages workflow definition versions with semantic versioning,
change tracking, and rollback capabilities.
"""

import logging
import json
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class VersionChangeType(str, Enum):
    """Types of version changes."""
    MAJOR = "major"  # Breaking changes
    MINOR = "minor"  # New features, backward compatible
    PATCH = "patch"  # Bug fixes


@dataclass
class WorkflowVersion:
    """Represents a workflow version."""
    version_id: str
    workflow_id: str
    version_number: str  # Semantic version: major.minor.patch
    graph_definition: Dict[str, Any]
    change_type: VersionChangeType
    change_description: str
    created_by: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    is_published: bool = False
    published_at: Optional[str] = None
    content_hash: str = ""
    
    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute hash of graph definition."""
        content = json.dumps(self.graph_definition, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version_id": self.version_id,
            "workflow_id": self.workflow_id,
            "version_number": self.version_number,
            "graph_definition": self.graph_definition,
            "change_type": self.change_type.value,
            "change_description": self.change_description,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "is_published": self.is_published,
            "published_at": self.published_at,
            "content_hash": self.content_hash,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowVersion":
        """Create from dictionary."""
        data["change_type"] = VersionChangeType(data["change_type"])
        return cls(**data)


@dataclass
class VersionDiff:
    """Represents differences between two versions."""
    from_version: str
    to_version: str
    added_nodes: List[str]
    removed_nodes: List[str]
    modified_nodes: List[str]
    added_edges: List[str]
    removed_edges: List[str]
    config_changes: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "added_nodes": self.added_nodes,
            "removed_nodes": self.removed_nodes,
            "modified_nodes": self.modified_nodes,
            "added_edges": self.added_edges,
            "removed_edges": self.removed_edges,
            "config_changes": self.config_changes,
            "summary": self.get_summary(),
        }
    
    def get_summary(self) -> str:
        """Get human-readable summary."""
        parts = []
        if self.added_nodes:
            parts.append(f"+{len(self.added_nodes)} nodes")
        if self.removed_nodes:
            parts.append(f"-{len(self.removed_nodes)} nodes")
        if self.modified_nodes:
            parts.append(f"~{len(self.modified_nodes)} nodes modified")
        if self.added_edges:
            parts.append(f"+{len(self.added_edges)} edges")
        if self.removed_edges:
            parts.append(f"-{len(self.removed_edges)} edges")
        return ", ".join(parts) if parts else "No changes"


class WorkflowVersionManager:
    """
    Manages workflow versions.
    
    Features:
    - Semantic versioning (major.minor.patch)
    - Version comparison and diff
    - Rollback capability
    - Published version tracking
    - Change history
    """
    
    def __init__(self, db_session=None, redis_client=None):
        """
        Initialize version manager.
        
        Args:
            db_session: Database session for persistence
            redis_client: Redis client for caching
        """
        self.db = db_session
        self.redis = redis_client
        self._versions: Dict[str, List[WorkflowVersion]] = {}
        self._published: Dict[str, str] = {}  # workflow_id -> version_id
    
    async def create_version(
        self,
        workflow_id: str,
        graph_definition: Dict[str, Any],
        change_type: VersionChangeType,
        change_description: str,
        created_by: Optional[str] = None,
    ) -> WorkflowVersion:
        """
        Create a new version.
        
        Args:
            workflow_id: Workflow ID
            graph_definition: New graph definition
            change_type: Type of change
            change_description: Description of changes
            created_by: User who created the version
            
        Returns:
            Created version
        """
        # Get current version
        current = await self.get_latest_version(workflow_id)
        
        # Calculate new version number
        if current:
            new_version = self._increment_version(
                current.version_number,
                change_type,
            )
        else:
            new_version = "1.0.0"
        
        # Create version
        version = WorkflowVersion(
            version_id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            version_number=new_version,
            graph_definition=graph_definition,
            change_type=change_type,
            change_description=change_description,
            created_by=created_by,
        )
        
        # Store version
        if workflow_id not in self._versions:
            self._versions[workflow_id] = []
        self._versions[workflow_id].append(version)
        
        # Persist to Redis
        await self._persist_version(version)
        
        logger.info(f"Created version {new_version} for workflow {workflow_id}")
        
        return version
    
    async def get_version(
        self,
        workflow_id: str,
        version_id: Optional[str] = None,
        version_number: Optional[str] = None,
    ) -> Optional[WorkflowVersion]:
        """
        Get a specific version.
        
        Args:
            workflow_id: Workflow ID
            version_id: Version ID (optional)
            version_number: Version number (optional)
            
        Returns:
            Version or None
        """
        versions = self._versions.get(workflow_id, [])
        
        if version_id:
            return next((v for v in versions if v.version_id == version_id), None)
        
        if version_number:
            return next((v for v in versions if v.version_number == version_number), None)
        
        return None
    
    async def get_latest_version(
        self,
        workflow_id: str,
        published_only: bool = False,
    ) -> Optional[WorkflowVersion]:
        """
        Get the latest version.
        
        Args:
            workflow_id: Workflow ID
            published_only: Only return published versions
            
        Returns:
            Latest version or None
        """
        versions = self._versions.get(workflow_id, [])
        
        if published_only:
            versions = [v for v in versions if v.is_published]
        
        if not versions:
            return None
        
        # Sort by version number and return latest
        return sorted(
            versions,
            key=lambda v: self._parse_version(v.version_number),
            reverse=True,
        )[0]
    
    async def list_versions(
        self,
        workflow_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[WorkflowVersion]:
        """
        List all versions for a workflow.
        
        Args:
            workflow_id: Workflow ID
            limit: Max versions to return
            offset: Pagination offset
            
        Returns:
            List of versions
        """
        versions = self._versions.get(workflow_id, [])
        
        # Sort by version number descending
        sorted_versions = sorted(
            versions,
            key=lambda v: self._parse_version(v.version_number),
            reverse=True,
        )
        
        return sorted_versions[offset:offset + limit]
    
    async def publish_version(
        self,
        workflow_id: str,
        version_id: str,
    ) -> WorkflowVersion:
        """
        Publish a version (make it the active version).
        
        Args:
            workflow_id: Workflow ID
            version_id: Version ID to publish
            
        Returns:
            Published version
        """
        version = await self.get_version(workflow_id, version_id=version_id)
        if not version:
            raise ValueError(f"Version {version_id} not found")
        
        # Unpublish current published version
        current_published = self._published.get(workflow_id)
        if current_published:
            old_version = await self.get_version(workflow_id, version_id=current_published)
            if old_version:
                old_version.is_published = False
        
        # Publish new version
        version.is_published = True
        version.published_at = datetime.utcnow().isoformat()
        self._published[workflow_id] = version_id
        
        await self._persist_version(version)
        
        logger.info(f"Published version {version.version_number} for workflow {workflow_id}")
        
        return version
    
    async def rollback(
        self,
        workflow_id: str,
        target_version_id: str,
        reason: str,
        created_by: Optional[str] = None,
    ) -> WorkflowVersion:
        """
        Rollback to a previous version.
        
        Creates a new version with the old graph definition.
        
        Args:
            workflow_id: Workflow ID
            target_version_id: Version to rollback to
            reason: Reason for rollback
            created_by: User performing rollback
            
        Returns:
            New version created from rollback
        """
        target = await self.get_version(workflow_id, version_id=target_version_id)
        if not target:
            raise ValueError(f"Target version {target_version_id} not found")
        
        # Create new version with old definition
        new_version = await self.create_version(
            workflow_id=workflow_id,
            graph_definition=target.graph_definition,
            change_type=VersionChangeType.PATCH,
            change_description=f"Rollback to {target.version_number}: {reason}",
            created_by=created_by,
        )
        
        # Auto-publish rollback
        await self.publish_version(workflow_id, new_version.version_id)
        
        logger.info(f"Rolled back workflow {workflow_id} to version {target.version_number}")
        
        return new_version
    
    async def compare_versions(
        self,
        workflow_id: str,
        from_version_id: str,
        to_version_id: str,
    ) -> VersionDiff:
        """
        Compare two versions.
        
        Args:
            workflow_id: Workflow ID
            from_version_id: Source version
            to_version_id: Target version
            
        Returns:
            Version diff
        """
        from_ver = await self.get_version(workflow_id, version_id=from_version_id)
        to_ver = await self.get_version(workflow_id, version_id=to_version_id)
        
        if not from_ver or not to_ver:
            raise ValueError("One or both versions not found")
        
        from_graph = from_ver.graph_definition
        to_graph = to_ver.graph_definition
        
        # Compare nodes
        from_nodes = {n["id"]: n for n in from_graph.get("nodes", [])}
        to_nodes = {n["id"]: n for n in to_graph.get("nodes", [])}
        
        added_nodes = list(set(to_nodes.keys()) - set(from_nodes.keys()))
        removed_nodes = list(set(from_nodes.keys()) - set(to_nodes.keys()))
        
        modified_nodes = []
        for node_id in set(from_nodes.keys()) & set(to_nodes.keys()):
            if from_nodes[node_id] != to_nodes[node_id]:
                modified_nodes.append(node_id)
        
        # Compare edges
        from_edges = {e["id"]: e for e in from_graph.get("edges", [])}
        to_edges = {e["id"]: e for e in to_graph.get("edges", [])}
        
        added_edges = list(set(to_edges.keys()) - set(from_edges.keys()))
        removed_edges = list(set(from_edges.keys()) - set(to_edges.keys()))
        
        # Compare settings
        from_settings = from_graph.get("settings", {})
        to_settings = to_graph.get("settings", {})
        
        config_changes = {}
        all_keys = set(from_settings.keys()) | set(to_settings.keys())
        for key in all_keys:
            if from_settings.get(key) != to_settings.get(key):
                config_changes[key] = {
                    "from": from_settings.get(key),
                    "to": to_settings.get(key),
                }
        
        return VersionDiff(
            from_version=from_ver.version_number,
            to_version=to_ver.version_number,
            added_nodes=added_nodes,
            removed_nodes=removed_nodes,
            modified_nodes=modified_nodes,
            added_edges=added_edges,
            removed_edges=removed_edges,
            config_changes=config_changes,
        )
    
    def _increment_version(
        self,
        current: str,
        change_type: VersionChangeType,
    ) -> str:
        """Increment version number based on change type."""
        major, minor, patch = self._parse_version(current)
        
        if change_type == VersionChangeType.MAJOR:
            return f"{major + 1}.0.0"
        elif change_type == VersionChangeType.MINOR:
            return f"{major}.{minor + 1}.0"
        else:  # PATCH
            return f"{major}.{minor}.{patch + 1}"
    
    def _parse_version(self, version: str) -> Tuple[int, int, int]:
        """Parse version string to tuple."""
        parts = version.split(".")
        return (
            int(parts[0]) if len(parts) > 0 else 0,
            int(parts[1]) if len(parts) > 1 else 0,
            int(parts[2]) if len(parts) > 2 else 0,
        )
    
    async def _persist_version(self, version: WorkflowVersion) -> None:
        """Persist version to storage."""
        if self.redis:
            try:
                key = f"workflow:versions:{version.workflow_id}"
                await self.redis.hset(
                    key,
                    version.version_id,
                    json.dumps(version.to_dict(), default=str),
                )
                await self.redis.expire(key, 86400 * 90)  # 90 days
            except Exception as e:
                logger.warning(f"Version persistence failed: {e}")


# Global version manager
_version_manager: Optional[WorkflowVersionManager] = None


def get_version_manager(db_session=None, redis_client=None) -> WorkflowVersionManager:
    """Get or create global version manager."""
    global _version_manager
    if _version_manager is None:
        _version_manager = WorkflowVersionManager(db_session, redis_client)
    return _version_manager
