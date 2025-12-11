"""
Agent Version Management

Provides version control for agents:
- Version creation and tracking
- Version comparison (diff)
- Rollback functionality
- Version history
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import hashlib
import difflib

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class VersionChangeType(str, Enum):
    """Types of changes between versions."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    UNCHANGED = "unchanged"


@dataclass
class VersionChange:
    """Single change in a version."""
    field: str
    change_type: VersionChangeType
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "change_type": self.change_type.value,
            "old_value": self.old_value,
            "new_value": self.new_value,
        }


@dataclass
class VersionDiff:
    """Diff between two versions."""
    from_version: int
    to_version: int
    changes: List[VersionChange] = field(default_factory=list)
    summary: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "changes": [c.to_dict() for c in self.changes],
            "summary": self.summary,
            "total_changes": len(self.changes),
        }


@dataclass
class AgentVersion:
    """Agent version snapshot."""
    version_id: str
    agent_id: str
    version_number: int
    
    # Snapshot data
    name: str
    description: str
    system_prompt: str
    llm_provider: str
    llm_model: str
    configuration: Dict[str, Any]
    tools: List[Dict[str, Any]]
    knowledgebases: List[Dict[str, Any]]
    
    # Metadata
    created_at: str
    created_by: str
    commit_message: str = ""
    is_published: bool = False
    
    # Hash for quick comparison
    content_hash: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_agent(
        cls,
        agent: Any,
        version_number: int,
        created_by: str,
        commit_message: str = "",
    ) -> "AgentVersion":
        """Create version from agent object."""
        import uuid
        
        # Extract configuration
        config = agent.configuration or {}
        
        # Build version
        version = cls(
            version_id=str(uuid.uuid4()),
            agent_id=str(agent.id),
            version_number=version_number,
            name=agent.name,
            description=agent.description or "",
            system_prompt=config.get("system_prompt", ""),
            llm_provider=agent.llm_provider or "",
            llm_model=agent.llm_model or "",
            configuration=config,
            tools=[
                {"tool_id": str(t.tool_id), "order": t.order, "configuration": t.configuration or {}}
                for t in (agent.tools or [])
            ],
            knowledgebases=[
                {"knowledgebase_id": str(k.knowledgebase_id), "order": k.order}
                for k in (agent.knowledgebases or [])
            ],
            created_at=datetime.utcnow().isoformat(),
            created_by=created_by,
            commit_message=commit_message,
        )
        
        # Calculate content hash
        version.content_hash = version._calculate_hash()
        
        return version
    
    def _calculate_hash(self) -> str:
        """Calculate hash of version content."""
        content = {
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "configuration": self.configuration,
            "tools": self.tools,
            "knowledgebases": self.knowledgebases,
        }
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]


class AgentVersioningService:
    """
    Service for managing agent versions.
    
    Features:
    - Create versions on save
    - Compare versions (diff)
    - Rollback to previous versions
    - Version history
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._versions_cache: Dict[str, List[AgentVersion]] = {}
    
    async def create_version(
        self,
        agent: Any,
        user_id: str,
        commit_message: str = "",
        auto_version: bool = True,
    ) -> AgentVersion:
        """
        Create a new version of an agent.
        
        Args:
            agent: Agent object
            user_id: User creating the version
            commit_message: Description of changes
            auto_version: If True, only create if content changed
            
        Returns:
            Created version
        """
        agent_id = str(agent.id)
        
        # Get current version number
        versions = await self.get_version_history(agent_id)
        current_version = len(versions)
        
        # Create new version
        new_version = AgentVersion.from_agent(
            agent=agent,
            version_number=current_version + 1,
            created_by=user_id,
            commit_message=commit_message,
        )
        
        # Check if content actually changed (for auto-versioning)
        if auto_version and versions:
            latest = versions[0]
            if latest.content_hash == new_version.content_hash:
                logger.debug(f"No changes detected for agent {agent_id}, skipping version")
                return latest
        
        # Store version
        await self._store_version(new_version)
        
        logger.info(f"Created version {new_version.version_number} for agent {agent_id}")
        return new_version
    
    async def get_version(
        self,
        agent_id: str,
        version_number: int,
    ) -> Optional[AgentVersion]:
        """Get a specific version."""
        versions = await self.get_version_history(agent_id)
        
        for version in versions:
            if version.version_number == version_number:
                return version
        
        return None
    
    async def get_version_history(
        self,
        agent_id: str,
        limit: int = 50,
    ) -> List[AgentVersion]:
        """
        Get version history for an agent.
        
        Returns versions in descending order (newest first).
        """
        # Check cache
        if agent_id in self._versions_cache:
            return self._versions_cache[agent_id][:limit]
        
        # Load from database
        versions = await self._load_versions(agent_id)
        
        # Sort by version number descending
        versions.sort(key=lambda v: v.version_number, reverse=True)
        
        # Cache
        self._versions_cache[agent_id] = versions
        
        return versions[:limit]
    
    async def compare_versions(
        self,
        agent_id: str,
        from_version: int,
        to_version: int,
    ) -> VersionDiff:
        """
        Compare two versions and return diff.
        
        Args:
            agent_id: Agent ID
            from_version: Source version number
            to_version: Target version number
            
        Returns:
            VersionDiff with changes
        """
        v1 = await self.get_version(agent_id, from_version)
        v2 = await self.get_version(agent_id, to_version)
        
        if not v1 or not v2:
            raise ValueError(f"Version not found")
        
        changes = []
        
        # Compare simple fields
        simple_fields = ["name", "description", "llm_provider", "llm_model"]
        for field in simple_fields:
            old_val = getattr(v1, field)
            new_val = getattr(v2, field)
            
            if old_val != new_val:
                changes.append(VersionChange(
                    field=field,
                    change_type=VersionChangeType.MODIFIED,
                    old_value=old_val,
                    new_value=new_val,
                ))
        
        # Compare system prompt (with diff)
        if v1.system_prompt != v2.system_prompt:
            diff = self._text_diff(v1.system_prompt, v2.system_prompt)
            changes.append(VersionChange(
                field="system_prompt",
                change_type=VersionChangeType.MODIFIED,
                old_value=v1.system_prompt[:500] if v1.system_prompt else None,
                new_value={"preview": v2.system_prompt[:500] if v2.system_prompt else None, "diff": diff},
            ))
        
        # Compare configuration
        config_changes = self._compare_dicts(v1.configuration, v2.configuration, "configuration")
        changes.extend(config_changes)
        
        # Compare tools
        tool_changes = self._compare_lists(v1.tools, v2.tools, "tools", "tool_id")
        changes.extend(tool_changes)
        
        # Compare knowledgebases
        kb_changes = self._compare_lists(v1.knowledgebases, v2.knowledgebases, "knowledgebases", "knowledgebase_id")
        changes.extend(kb_changes)
        
        # Generate summary
        summary = self._generate_summary(changes)
        
        return VersionDiff(
            from_version=from_version,
            to_version=to_version,
            changes=changes,
            summary=summary,
        )
    
    async def rollback(
        self,
        agent_id: str,
        target_version: int,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Rollback agent to a previous version.
        
        Args:
            agent_id: Agent ID
            target_version: Version number to rollback to
            user_id: User performing rollback
            
        Returns:
            Rollback result with new agent configuration
        """
        version = await self.get_version(agent_id, target_version)
        if not version:
            raise ValueError(f"Version {target_version} not found")
        
        # Build agent configuration from version
        agent_config = {
            "name": version.name,
            "description": version.description,
            "llm_provider": version.llm_provider,
            "llm_model": version.llm_model,
            "configuration": {
                **version.configuration,
                "system_prompt": version.system_prompt,
            },
            "tools": version.tools,
            "knowledgebases": version.knowledgebases,
        }
        
        logger.info(f"Prepared rollback for agent {agent_id} to version {target_version}")
        
        return {
            "agent_id": agent_id,
            "target_version": target_version,
            "agent_config": agent_config,
            "rollback_message": f"Rolled back to version {target_version}",
        }
    
    async def publish_version(
        self,
        agent_id: str,
        version_number: int,
    ) -> bool:
        """Mark a version as published/stable."""
        version = await self.get_version(agent_id, version_number)
        if not version:
            return False
        
        version.is_published = True
        await self._store_version(version)
        
        logger.info(f"Published version {version_number} for agent {agent_id}")
        return True
    
    def _text_diff(self, old_text: str, new_text: str) -> List[str]:
        """Generate text diff."""
        old_lines = (old_text or "").splitlines()
        new_lines = (new_text or "").splitlines()
        
        diff = list(difflib.unified_diff(
            old_lines, new_lines,
            lineterm="",
            n=2
        ))
        
        return diff[:50]  # Limit diff size
    
    def _compare_dicts(
        self,
        old_dict: Dict,
        new_dict: Dict,
        prefix: str,
    ) -> List[VersionChange]:
        """Compare two dictionaries."""
        changes = []
        all_keys = set(old_dict.keys()) | set(new_dict.keys())
        
        for key in all_keys:
            field = f"{prefix}.{key}"
            old_val = old_dict.get(key)
            new_val = new_dict.get(key)
            
            if key not in old_dict:
                changes.append(VersionChange(
                    field=field,
                    change_type=VersionChangeType.CREATED,
                    new_value=new_val,
                ))
            elif key not in new_dict:
                changes.append(VersionChange(
                    field=field,
                    change_type=VersionChangeType.DELETED,
                    old_value=old_val,
                ))
            elif old_val != new_val:
                changes.append(VersionChange(
                    field=field,
                    change_type=VersionChangeType.MODIFIED,
                    old_value=old_val,
                    new_value=new_val,
                ))
        
        return changes
    
    def _compare_lists(
        self,
        old_list: List[Dict],
        new_list: List[Dict],
        field_name: str,
        id_field: str,
    ) -> List[VersionChange]:
        """Compare two lists of dictionaries."""
        changes = []
        
        old_by_id = {item.get(id_field): item for item in old_list}
        new_by_id = {item.get(id_field): item for item in new_list}
        
        all_ids = set(old_by_id.keys()) | set(new_by_id.keys())
        
        added = []
        removed = []
        modified = []
        
        for item_id in all_ids:
            if item_id not in old_by_id:
                added.append(item_id)
            elif item_id not in new_by_id:
                removed.append(item_id)
            elif old_by_id[item_id] != new_by_id[item_id]:
                modified.append(item_id)
        
        if added:
            changes.append(VersionChange(
                field=f"{field_name}_added",
                change_type=VersionChangeType.CREATED,
                new_value=added,
            ))
        
        if removed:
            changes.append(VersionChange(
                field=f"{field_name}_removed",
                change_type=VersionChangeType.DELETED,
                old_value=removed,
            ))
        
        if modified:
            changes.append(VersionChange(
                field=f"{field_name}_modified",
                change_type=VersionChangeType.MODIFIED,
                old_value=modified,
                new_value=[new_by_id[id] for id in modified],
            ))
        
        return changes
    
    def _generate_summary(self, changes: List[VersionChange]) -> str:
        """Generate human-readable summary of changes."""
        if not changes:
            return "No changes"
        
        parts = []
        
        field_changes = [c for c in changes if c.change_type == VersionChangeType.MODIFIED and "." not in c.field]
        if field_changes:
            fields = [c.field for c in field_changes]
            parts.append(f"Modified: {', '.join(fields)}")
        
        added = [c for c in changes if c.change_type == VersionChangeType.CREATED]
        if added:
            parts.append(f"Added {len(added)} item(s)")
        
        removed = [c for c in changes if c.change_type == VersionChangeType.DELETED]
        if removed:
            parts.append(f"Removed {len(removed)} item(s)")
        
        return "; ".join(parts) if parts else f"{len(changes)} change(s)"
    
    async def _store_version(self, version: AgentVersion):
        """Store version in database."""
        # In production, this would store to a versions table
        # For now, update cache
        agent_id = version.agent_id
        if agent_id not in self._versions_cache:
            self._versions_cache[agent_id] = []
        
        # Update or add
        existing_idx = None
        for i, v in enumerate(self._versions_cache[agent_id]):
            if v.version_number == version.version_number:
                existing_idx = i
                break
        
        if existing_idx is not None:
            self._versions_cache[agent_id][existing_idx] = version
        else:
            self._versions_cache[agent_id].append(version)
            self._versions_cache[agent_id].sort(key=lambda v: v.version_number, reverse=True)
    
    async def _load_versions(self, agent_id: str) -> List[AgentVersion]:
        """Load versions from database."""
        # In production, query from database
        return self._versions_cache.get(agent_id, [])
