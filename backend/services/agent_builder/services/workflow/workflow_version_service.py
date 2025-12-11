"""Workflow Version Service for managing workflow versions."""

import logging
import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from datetime import datetime

from backend.db.models.agent_builder import Workflow, AgentBlock, AgentEdge

logger = logging.getLogger(__name__)


class WorkflowVersion:
    """Workflow version data structure."""
    
    def __init__(
        self,
        id: str,
        workflow_id: str,
        version_number: int,
        version_tag: Optional[str],
        snapshot: Dict[str, Any],
        change_description: Optional[str],
        created_by: str,
        created_at: datetime,
    ):
        self.id = id
        self.workflow_id = workflow_id
        self.version_number = version_number
        self.version_tag = version_tag
        self.snapshot = snapshot
        self.change_description = change_description
        self.created_by = created_by
        self.created_at = created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "version_number": self.version_number,
            "version_tag": self.version_tag,
            "snapshot": self.snapshot,
            "change_description": self.change_description,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
        }


class WorkflowVersionService:
    """Service for managing workflow versions."""
    
    def __init__(self, db: Session):
        """
        Initialize Workflow Version Service.
        
        Args:
            db: Database session
        """
        self.db = db
        # In-memory storage for versions (in production, use a dedicated table)
        self._versions: Dict[str, List[WorkflowVersion]] = {}
    
    def create_version(
        self,
        workflow_id: UUID,
        user_id: UUID,
        change_description: Optional[str] = None,
        version_tag: Optional[str] = None
    ) -> WorkflowVersion:
        """
        Create a new version of a workflow.
        
        Args:
            workflow_id: Workflow ID
            user_id: User ID creating the version
            change_description: Description of changes
            version_tag: Optional tag (e.g., "v1.0", "stable")
            
        Returns:
            Created WorkflowVersion
            
        Raises:
            ValueError: If workflow not found
        """
        # Load workflow
        workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Load blocks and edges
        blocks = self.db.query(AgentBlock).filter(
            AgentBlock.workflow_id == workflow_id
        ).all()
        
        edges = self.db.query(AgentEdge).filter(
            AgentEdge.workflow_id == workflow_id
        ).all()
        
        # Create snapshot
        snapshot = {
            "workflow": {
                "name": workflow.name,
                "description": workflow.description,
                "graph_definition": workflow.graph_definition,
                "is_public": workflow.is_public,
            },
            "blocks": [
                {
                    "id": str(block.id),
                    "type": block.type,
                    "name": block.name,
                    "position_x": block.position_x,
                    "position_y": block.position_y,
                    "config": block.config,
                    "sub_blocks": block.sub_blocks,
                    "inputs": block.inputs,
                    "outputs": block.outputs,
                    "enabled": block.enabled,
                }
                for block in blocks
            ],
            "edges": [
                {
                    "id": str(edge.id),
                    "source_block_id": str(edge.source_block_id),
                    "target_block_id": str(edge.target_block_id),
                    "source_handle": edge.source_handle,
                    "target_handle": edge.target_handle,
                }
                for edge in edges
            ],
        }
        
        # Get version number
        workflow_id_str = str(workflow_id)
        existing_versions = self._versions.get(workflow_id_str, [])
        version_number = len(existing_versions) + 1
        
        # Create version
        version = WorkflowVersion(
            id=str(uuid4()),
            workflow_id=workflow_id_str,
            version_number=version_number,
            version_tag=version_tag,
            snapshot=snapshot,
            change_description=change_description,
            created_by=str(user_id),
            created_at=datetime.utcnow(),
        )
        
        # Store version
        if workflow_id_str not in self._versions:
            self._versions[workflow_id_str] = []
        self._versions[workflow_id_str].append(version)
        
        logger.info(f"Created version {version_number} for workflow {workflow_id}")
        
        return version
    
    def list_versions(self, workflow_id: UUID) -> List[WorkflowVersion]:
        """
        List all versions of a workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            List of workflow versions (newest first)
        """
        workflow_id_str = str(workflow_id)
        versions = self._versions.get(workflow_id_str, [])
        
        # Sort by version number descending
        return sorted(versions, key=lambda v: v.version_number, reverse=True)
    
    def get_version(self, workflow_id: UUID, version_number: int) -> Optional[WorkflowVersion]:
        """
        Get a specific version of a workflow.
        
        Args:
            workflow_id: Workflow ID
            version_number: Version number
            
        Returns:
            WorkflowVersion or None
        """
        workflow_id_str = str(workflow_id)
        versions = self._versions.get(workflow_id_str, [])
        
        for version in versions:
            if version.version_number == version_number:
                return version
        
        return None
    
    def get_version_by_tag(self, workflow_id: UUID, version_tag: str) -> Optional[WorkflowVersion]:
        """
        Get a version by tag.
        
        Args:
            workflow_id: Workflow ID
            version_tag: Version tag
            
        Returns:
            WorkflowVersion or None
        """
        workflow_id_str = str(workflow_id)
        versions = self._versions.get(workflow_id_str, [])
        
        for version in versions:
            if version.version_tag == version_tag:
                return version
        
        return None
    
    def rollback_to_version(
        self,
        workflow_id: UUID,
        version_number: int,
        user_id: UUID
    ) -> Workflow:
        """
        Rollback workflow to a specific version.
        
        Args:
            workflow_id: Workflow ID
            version_number: Version number to rollback to
            user_id: User ID performing rollback
            
        Returns:
            Updated Workflow
            
        Raises:
            ValueError: If workflow or version not found
        """
        # Get version
        version = self.get_version(workflow_id, version_number)
        if not version:
            raise ValueError(f"Version {version_number} not found for workflow {workflow_id}")
        
        # Load workflow
        workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Create a new version before rollback
        self.create_version(
            workflow_id=workflow_id,
            user_id=user_id,
            change_description=f"Rollback to version {version_number}"
        )
        
        # Delete existing blocks and edges
        self.db.query(AgentBlock).filter(AgentBlock.workflow_id == workflow_id).delete()
        self.db.query(AgentEdge).filter(AgentEdge.workflow_id == workflow_id).delete()
        
        # Restore workflow metadata
        snapshot = version.snapshot
        workflow.name = snapshot["workflow"]["name"]
        workflow.description = snapshot["workflow"]["description"]
        workflow.graph_definition = snapshot["workflow"]["graph_definition"]
        workflow.is_public = snapshot["workflow"]["is_public"]
        workflow.updated_at = datetime.utcnow()
        
        # Restore blocks
        block_id_map = {}  # Map old ID to new ID
        for block_data in snapshot["blocks"]:
            old_id = UUID(block_data["id"])
            new_id = uuid4()
            block_id_map[old_id] = new_id
            
            block = AgentBlock(
                id=new_id,
                workflow_id=workflow_id,
                type=block_data["type"],
                name=block_data["name"],
                position_x=block_data["position_x"],
                position_y=block_data["position_y"],
                config=block_data["config"],
                sub_blocks=block_data["sub_blocks"],
                inputs=block_data["inputs"],
                outputs=block_data["outputs"],
                enabled=block_data["enabled"],
            )
            self.db.add(block)
        
        # Restore edges
        for edge_data in snapshot["edges"]:
            old_source_id = UUID(edge_data["source_block_id"])
            old_target_id = UUID(edge_data["target_block_id"])
            
            if old_source_id in block_id_map and old_target_id in block_id_map:
                edge = AgentEdge(
                    id=uuid4(),
                    workflow_id=workflow_id,
                    source_block_id=block_id_map[old_source_id],
                    target_block_id=block_id_map[old_target_id],
                    source_handle=edge_data["source_handle"],
                    target_handle=edge_data["target_handle"],
                )
                self.db.add(edge)
        
        self.db.commit()
        self.db.refresh(workflow)
        
        logger.info(f"Rolled back workflow {workflow_id} to version {version_number}")
        
        return workflow
    
    def compare_versions(
        self,
        workflow_id: UUID,
        version1: int,
        version2: int
    ) -> Dict[str, Any]:
        """
        Compare two versions of a workflow.
        
        Args:
            workflow_id: Workflow ID
            version1: First version number
            version2: Second version number
            
        Returns:
            Comparison result with differences
            
        Raises:
            ValueError: If versions not found
        """
        v1 = self.get_version(workflow_id, version1)
        v2 = self.get_version(workflow_id, version2)
        
        if not v1:
            raise ValueError(f"Version {version1} not found")
        if not v2:
            raise ValueError(f"Version {version2} not found")
        
        # Compare snapshots
        differences = {
            "workflow_changes": self._compare_dicts(
                v1.snapshot["workflow"],
                v2.snapshot["workflow"]
            ),
            "blocks_added": [],
            "blocks_removed": [],
            "blocks_modified": [],
            "edges_added": [],
            "edges_removed": [],
        }
        
        # Compare blocks
        v1_blocks = {b["id"]: b for b in v1.snapshot["blocks"]}
        v2_blocks = {b["id"]: b for b in v2.snapshot["blocks"]}
        
        for block_id, block in v2_blocks.items():
            if block_id not in v1_blocks:
                differences["blocks_added"].append(block["name"])
            elif v1_blocks[block_id] != block:
                differences["blocks_modified"].append(block["name"])
        
        for block_id, block in v1_blocks.items():
            if block_id not in v2_blocks:
                differences["blocks_removed"].append(block["name"])
        
        # Compare edges
        v1_edges = set((e["source_block_id"], e["target_block_id"]) for e in v1.snapshot["edges"])
        v2_edges = set((e["source_block_id"], e["target_block_id"]) for e in v2.snapshot["edges"])
        
        differences["edges_added"] = list(v2_edges - v1_edges)
        differences["edges_removed"] = list(v1_edges - v2_edges)
        
        return differences
    
    def _compare_dicts(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare two dictionaries and return differences.
        
        Args:
            dict1: First dictionary
            dict2: Second dictionary
            
        Returns:
            Dictionary of differences
        """
        differences = {}
        
        all_keys = set(dict1.keys()) | set(dict2.keys())
        
        for key in all_keys:
            val1 = dict1.get(key)
            val2 = dict2.get(key)
            
            if val1 != val2:
                differences[key] = {
                    "old": val1,
                    "new": val2
                }
        
        return differences
