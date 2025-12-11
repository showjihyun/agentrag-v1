"""
Agent Collaboration System

Provides team collaboration features for agents:
- Team sharing
- Permission management
- Collaborative editing
- Activity tracking
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """Agent permissions."""
    VIEW = "view"
    EXECUTE = "execute"
    EDIT = "edit"
    ADMIN = "admin"
    OWNER = "owner"


class ShareType(str, Enum):
    """Types of sharing."""
    USER = "user"
    TEAM = "team"
    PUBLIC = "public"
    LINK = "link"


@dataclass
class AgentShare:
    """Agent sharing configuration."""
    id: str
    agent_id: str
    share_type: ShareType
    target_id: Optional[str]  # user_id or team_id
    target_name: Optional[str]
    permission: Permission
    created_at: str
    created_by: str
    expires_at: Optional[str] = None
    share_link: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "share_type": self.share_type.value,
            "permission": self.permission.value,
        }


@dataclass
class ActivityLog:
    """Activity log entry."""
    id: str
    agent_id: str
    user_id: str
    user_name: str
    action: str
    details: Dict[str, Any]
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Team:
    """Team definition."""
    id: str
    name: str
    description: str
    owner_id: str
    members: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AgentCollaborationService:
    """
    Service for agent collaboration features.
    
    Features:
    - Share agents with users/teams
    - Manage permissions
    - Track activity
    - Team management
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._shares: Dict[str, List[AgentShare]] = {}
        self._activities: Dict[str, List[ActivityLog]] = {}
        self._teams: Dict[str, Team] = {}
    
    # ========================================================================
    # Sharing
    # ========================================================================
    
    async def share_with_user(
        self,
        agent_id: str,
        owner_id: str,
        target_user_id: str,
        target_user_name: str,
        permission: Permission,
    ) -> AgentShare:
        """Share agent with a specific user."""
        share = AgentShare(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            share_type=ShareType.USER,
            target_id=target_user_id,
            target_name=target_user_name,
            permission=permission,
            created_at=datetime.utcnow().isoformat(),
            created_by=owner_id,
        )
        
        self._add_share(share)
        await self._log_activity(
            agent_id=agent_id,
            user_id=owner_id,
            user_name="Owner",
            action="shared",
            details={"target": target_user_name, "permission": permission.value},
        )
        
        logger.info(f"Shared agent {agent_id} with user {target_user_id}")
        return share
    
    async def share_with_team(
        self,
        agent_id: str,
        owner_id: str,
        team_id: str,
        permission: Permission,
    ) -> AgentShare:
        """Share agent with a team."""
        team = self._teams.get(team_id)
        team_name = team.name if team else "Unknown Team"
        
        share = AgentShare(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            share_type=ShareType.TEAM,
            target_id=team_id,
            target_name=team_name,
            permission=permission,
            created_at=datetime.utcnow().isoformat(),
            created_by=owner_id,
        )
        
        self._add_share(share)
        await self._log_activity(
            agent_id=agent_id,
            user_id=owner_id,
            user_name="Owner",
            action="shared_with_team",
            details={"team": team_name, "permission": permission.value},
        )
        
        logger.info(f"Shared agent {agent_id} with team {team_id}")
        return share
    
    async def create_share_link(
        self,
        agent_id: str,
        owner_id: str,
        permission: Permission = Permission.VIEW,
        expires_hours: Optional[int] = None,
    ) -> AgentShare:
        """Create a shareable link for the agent."""
        share_token = str(uuid.uuid4()).replace("-", "")[:16]
        
        expires_at = None
        if expires_hours:
            from datetime import timedelta
            expires_at = (datetime.utcnow() + timedelta(hours=expires_hours)).isoformat()
        
        share = AgentShare(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            share_type=ShareType.LINK,
            target_id=None,
            target_name=None,
            permission=permission,
            created_at=datetime.utcnow().isoformat(),
            created_by=owner_id,
            expires_at=expires_at,
            share_link=f"/shared/agent/{share_token}",
        )
        
        self._add_share(share)
        logger.info(f"Created share link for agent {agent_id}")
        return share
    
    async def revoke_share(
        self,
        agent_id: str,
        share_id: str,
        user_id: str,
    ) -> bool:
        """Revoke a share."""
        shares = self._shares.get(agent_id, [])
        
        for i, share in enumerate(shares):
            if share.id == share_id:
                shares.pop(i)
                await self._log_activity(
                    agent_id=agent_id,
                    user_id=user_id,
                    user_name="User",
                    action="revoked_share",
                    details={"share_id": share_id},
                )
                logger.info(f"Revoked share {share_id} for agent {agent_id}")
                return True
        
        return False
    
    async def get_shares(self, agent_id: str) -> List[AgentShare]:
        """Get all shares for an agent."""
        return self._shares.get(agent_id, [])
    
    # ========================================================================
    # Permissions
    # ========================================================================
    
    async def check_permission(
        self,
        agent_id: str,
        user_id: str,
        required_permission: Permission,
    ) -> bool:
        """Check if user has required permission."""
        # Get user's permission level
        user_permission = await self.get_user_permission(agent_id, user_id)
        
        if not user_permission:
            return False
        
        # Permission hierarchy
        hierarchy = {
            Permission.VIEW: 1,
            Permission.EXECUTE: 2,
            Permission.EDIT: 3,
            Permission.ADMIN: 4,
            Permission.OWNER: 5,
        }
        
        return hierarchy.get(user_permission, 0) >= hierarchy.get(required_permission, 0)
    
    async def get_user_permission(
        self,
        agent_id: str,
        user_id: str,
    ) -> Optional[Permission]:
        """Get user's permission level for an agent."""
        shares = self._shares.get(agent_id, [])
        
        # Check direct user shares
        for share in shares:
            if share.share_type == ShareType.USER and share.target_id == user_id:
                return share.permission
        
        # Check team shares
        user_teams = await self._get_user_teams(user_id)
        for share in shares:
            if share.share_type == ShareType.TEAM and share.target_id in user_teams:
                return share.permission
        
        # Check public shares
        for share in shares:
            if share.share_type == ShareType.PUBLIC:
                return share.permission
        
        return None
    
    async def get_collaborators(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all collaborators for an agent."""
        shares = self._shares.get(agent_id, [])
        collaborators = []
        
        for share in shares:
            if share.share_type in (ShareType.USER, ShareType.TEAM):
                collaborators.append({
                    "id": share.target_id,
                    "name": share.target_name,
                    "type": share.share_type.value,
                    "permission": share.permission.value,
                    "shared_at": share.created_at,
                })
        
        return collaborators
    
    # ========================================================================
    # Activity Tracking
    # ========================================================================
    
    async def get_activity_log(
        self,
        agent_id: str,
        limit: int = 50,
    ) -> List[ActivityLog]:
        """Get activity log for an agent."""
        activities = self._activities.get(agent_id, [])
        return sorted(activities, key=lambda a: a.timestamp, reverse=True)[:limit]
    
    async def _log_activity(
        self,
        agent_id: str,
        user_id: str,
        user_name: str,
        action: str,
        details: Dict[str, Any],
    ):
        """Log an activity."""
        activity = ActivityLog(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            user_name=user_name,
            action=action,
            details=details,
            timestamp=datetime.utcnow().isoformat(),
        )
        
        if agent_id not in self._activities:
            self._activities[agent_id] = []
        
        self._activities[agent_id].append(activity)
    
    # ========================================================================
    # Team Management
    # ========================================================================
    
    async def create_team(
        self,
        name: str,
        description: str,
        owner_id: str,
    ) -> Team:
        """Create a new team."""
        team = Team(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            owner_id=owner_id,
            members=[{"user_id": owner_id, "role": "owner"}],
        )
        
        self._teams[team.id] = team
        logger.info(f"Created team {team.id}: {name}")
        return team
    
    async def add_team_member(
        self,
        team_id: str,
        user_id: str,
        role: str = "member",
    ) -> bool:
        """Add a member to a team."""
        team = self._teams.get(team_id)
        if not team:
            return False
        
        # Check if already a member
        for member in team.members:
            if member["user_id"] == user_id:
                return False
        
        team.members.append({"user_id": user_id, "role": role})
        logger.info(f"Added user {user_id} to team {team_id}")
        return True
    
    async def remove_team_member(
        self,
        team_id: str,
        user_id: str,
    ) -> bool:
        """Remove a member from a team."""
        team = self._teams.get(team_id)
        if not team:
            return False
        
        for i, member in enumerate(team.members):
            if member["user_id"] == user_id:
                team.members.pop(i)
                logger.info(f"Removed user {user_id} from team {team_id}")
                return True
        
        return False
    
    async def get_team(self, team_id: str) -> Optional[Team]:
        """Get team by ID."""
        return self._teams.get(team_id)
    
    async def get_user_teams(self, user_id: str) -> List[Team]:
        """Get all teams a user belongs to."""
        teams = []
        for team in self._teams.values():
            for member in team.members:
                if member["user_id"] == user_id:
                    teams.append(team)
                    break
        return teams
    
    # ========================================================================
    # Helpers
    # ========================================================================
    
    def _add_share(self, share: AgentShare):
        """Add a share to storage."""
        if share.agent_id not in self._shares:
            self._shares[share.agent_id] = []
        self._shares[share.agent_id].append(share)
    
    async def _get_user_teams(self, user_id: str) -> List[str]:
        """Get team IDs for a user."""
        teams = await self.get_user_teams(user_id)
        return [t.id for t in teams]
