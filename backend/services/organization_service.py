"""Service for organization and team management."""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime
import uuid

from backend.db.models.organization import (
    Organization,
    OrganizationMember,
    OrganizationRole,
    Team,
    TeamMember,
    TeamRole,
)
from backend.db.models.user import User
from backend.models.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    TeamCreate,
    TeamUpdate,
    OrganizationMemberInvite,
    OrganizationMemberUpdate,
    TeamMemberAdd,
    TeamMemberUpdate,
)
from backend.exceptions import (
    ResourceNotFoundException as NotFoundException,
    AuthorizationException as ForbiddenException,
    ValidationException as BadRequestException,
)


class OrganizationService:
    """Service for managing organizations."""

    def __init__(self, db: Session):
        self.db = db

    # Organization CRUD
    def create_organization(
        self, user_id: str, org_data: OrganizationCreate
    ) -> Organization:
        """Create a new organization and add creator as owner."""
        # Check if slug is unique
        existing = self.db.query(Organization).filter(
            Organization.slug == org_data.slug
        ).first()
        if existing:
            raise BadRequestException("Organization slug already exists")

        # Create organization
        org = Organization(
            id=uuid.uuid4(),
            name=org_data.name,
            slug=org_data.slug,
            description=org_data.description,
        )
        self.db.add(org)
        self.db.flush()

        # Add creator as owner
        member = OrganizationMember(
            id=uuid.uuid4(),
            organization_id=org.id,
            user_id=uuid.UUID(user_id),
            role=OrganizationRole.OWNER,
            joined_at=datetime.utcnow(),
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(org)

        return org

    def get_organization(self, org_id: str) -> Organization:
        """Get organization by ID."""
        org = self.db.query(Organization).filter(
            Organization.id == uuid.UUID(org_id)
        ).first()
        if not org:
            raise NotFoundException("Organization not found")
        return org

    def get_user_organizations(self, user_id: str) -> List[Organization]:
        """Get all organizations for a user."""
        orgs = (
            self.db.query(Organization)
            .join(OrganizationMember)
            .filter(
                OrganizationMember.user_id == uuid.UUID(user_id),
                OrganizationMember.is_active == True,
            )
            .all()
        )
        return orgs

    def update_organization(
        self, org_id: str, user_id: str, org_data: OrganizationUpdate
    ) -> Organization:
        """Update organization (requires admin role)."""
        org = self.get_organization(org_id)
        self._check_permission(org_id, user_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN])

        if org_data.name is not None:
            org.name = org_data.name
        if org_data.description is not None:
            org.description = org_data.description
        if org_data.plan is not None:
            org.plan = org_data.plan

        org.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(org)
        return org

    def delete_organization(self, org_id: str, user_id: str):
        """Delete organization (requires owner role)."""
        org = self.get_organization(org_id)
        self._check_permission(org_id, user_id, [OrganizationRole.OWNER])

        self.db.delete(org)
        self.db.commit()

    # Organization Member Management
    def invite_member(
        self, org_id: str, inviter_id: str, invite_data: OrganizationMemberInvite
    ) -> OrganizationMember:
        """Invite a member to organization."""
        self._check_permission(org_id, inviter_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN])

        # Find user by email
        user = self.db.query(User).filter(User.email == invite_data.email).first()
        if not user:
            raise NotFoundException("User not found")

        # Check if already a member
        existing = self.db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == uuid.UUID(org_id),
            OrganizationMember.user_id == user.id,
        ).first()
        if existing:
            raise BadRequestException("User is already a member")

        # Create membership
        member = OrganizationMember(
            id=uuid.uuid4(),
            organization_id=uuid.UUID(org_id),
            user_id=user.id,
            role=invite_data.role,
            invited_by=uuid.UUID(inviter_id),
            joined_at=datetime.utcnow(),  # Auto-join for now
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)

        return member

    def get_organization_members(self, org_id: str) -> List[OrganizationMember]:
        """Get all members of an organization."""
        members = (
            self.db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == uuid.UUID(org_id),
                OrganizationMember.is_active == True,
            )
            .options(joinedload(OrganizationMember.user))
            .all()
        )
        return members

    def update_member_role(
        self, org_id: str, member_id: str, updater_id: str, update_data: OrganizationMemberUpdate
    ) -> OrganizationMember:
        """Update member role."""
        self._check_permission(org_id, updater_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN])

        member = self.db.query(OrganizationMember).filter(
            OrganizationMember.id == uuid.UUID(member_id),
            OrganizationMember.organization_id == uuid.UUID(org_id),
        ).first()
        if not member:
            raise NotFoundException("Member not found")

        member.role = update_data.role
        self.db.commit()
        self.db.refresh(member)
        return member

    def remove_member(self, org_id: str, member_id: str, remover_id: str):
        """Remove a member from organization."""
        self._check_permission(org_id, remover_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN])

        member = self.db.query(OrganizationMember).filter(
            OrganizationMember.id == uuid.UUID(member_id),
            OrganizationMember.organization_id == uuid.UUID(org_id),
        ).first()
        if not member:
            raise NotFoundException("Member not found")

        # Prevent removing the last owner
        if member.role == OrganizationRole.OWNER:
            owner_count = self.db.query(func.count(OrganizationMember.id)).filter(
                OrganizationMember.organization_id == uuid.UUID(org_id),
                OrganizationMember.role == OrganizationRole.OWNER,
                OrganizationMember.is_active == True,
            ).scalar()
            if owner_count <= 1:
                raise BadRequestException("Cannot remove the last owner")

        self.db.delete(member)
        self.db.commit()

    # Team Management
    def create_team(
        self, org_id: str, user_id: str, team_data: TeamCreate
    ) -> Team:
        """Create a new team."""
        self._check_permission(org_id, user_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN])

        # Check if slug is unique within organization
        existing = self.db.query(Team).filter(
            Team.organization_id == uuid.UUID(org_id),
            Team.slug == team_data.slug,
        ).first()
        if existing:
            raise BadRequestException("Team slug already exists in this organization")

        team = Team(
            id=uuid.uuid4(),
            organization_id=uuid.UUID(org_id),
            name=team_data.name,
            slug=team_data.slug,
            description=team_data.description,
        )
        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)

        return team

    def get_organization_teams(self, org_id: str) -> List[Team]:
        """Get all teams in an organization."""
        teams = self.db.query(Team).filter(
            Team.organization_id == uuid.UUID(org_id),
            Team.is_active == True,
        ).all()
        return teams

    def get_team(self, team_id: str) -> Team:
        """Get team by ID."""
        team = self.db.query(Team).filter(Team.id == uuid.UUID(team_id)).first()
        if not team:
            raise NotFoundException("Team not found")
        return team

    def update_team(
        self, team_id: str, user_id: str, team_data: TeamUpdate
    ) -> Team:
        """Update team."""
        team = self.get_team(team_id)
        self._check_permission(
            str(team.organization_id), user_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN]
        )

        if team_data.name is not None:
            team.name = team_data.name
        if team_data.description is not None:
            team.description = team_data.description

        team.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(team)
        return team

    def delete_team(self, team_id: str, user_id: str):
        """Delete team."""
        team = self.get_team(team_id)
        self._check_permission(
            str(team.organization_id), user_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN]
        )

        self.db.delete(team)
        self.db.commit()

    # Team Member Management
    def add_team_member(
        self, team_id: str, user_id: str, member_data: TeamMemberAdd
    ) -> TeamMember:
        """Add a member to a team."""
        team = self.get_team(team_id)
        self._check_permission(
            str(team.organization_id), user_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN]
        )

        # Check if user is organization member
        org_member = self.db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == team.organization_id,
            OrganizationMember.user_id == uuid.UUID(member_data.user_id),
            OrganizationMember.is_active == True,
        ).first()
        if not org_member:
            raise BadRequestException("User must be an organization member first")

        # Check if already a team member
        existing = self.db.query(TeamMember).filter(
            TeamMember.team_id == uuid.UUID(team_id),
            TeamMember.user_id == uuid.UUID(member_data.user_id),
        ).first()
        if existing:
            raise BadRequestException("User is already a team member")

        member = TeamMember(
            id=uuid.uuid4(),
            team_id=uuid.UUID(team_id),
            user_id=uuid.UUID(member_data.user_id),
            role=member_data.role,
            added_by=uuid.UUID(user_id),
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)

        return member

    def get_team_members(self, team_id: str) -> List[TeamMember]:
        """Get all members of a team."""
        members = (
            self.db.query(TeamMember)
            .filter(
                TeamMember.team_id == uuid.UUID(team_id),
                TeamMember.is_active == True,
            )
            .options(joinedload(TeamMember.user))
            .all()
        )
        return members

    def remove_team_member(self, team_id: str, member_id: str, remover_id: str):
        """Remove a member from a team."""
        team = self.get_team(team_id)
        self._check_permission(
            str(team.organization_id), remover_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN]
        )

        member = self.db.query(TeamMember).filter(
            TeamMember.id == uuid.UUID(member_id),
            TeamMember.team_id == uuid.UUID(team_id),
        ).first()
        if not member:
            raise NotFoundException("Team member not found")

        self.db.delete(member)
        self.db.commit()

    # Permission Helpers
    def _check_permission(
        self, org_id: str, user_id: str, required_roles: List[OrganizationRole]
    ):
        """Check if user has required role in organization."""
        member = self.db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == uuid.UUID(org_id),
            OrganizationMember.user_id == uuid.UUID(user_id),
            OrganizationMember.is_active == True,
        ).first()

        if not member or member.role not in required_roles:
            raise ForbiddenException("Insufficient permissions")

    def get_user_role(self, org_id: str, user_id: str) -> Optional[OrganizationRole]:
        """Get user's role in organization."""
        member = self.db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == uuid.UUID(org_id),
            OrganizationMember.user_id == uuid.UUID(user_id),
            OrganizationMember.is_active == True,
        ).first()
        return member.role if member else None
