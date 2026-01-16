"""API endpoints for organization and team management."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from backend.db.database import get_db
from backend.services.organization_service import OrganizationService
from backend.models.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationListResponse,
    OrganizationMemberInvite,
    OrganizationMemberUpdate,
    OrganizationMemberResponse,
    MemberListResponse,
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamListResponse,
    TeamMemberAdd,
    TeamMemberResponse,
)
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User

router = APIRouter(prefix="/organizations", tags=["organizations"])


# Organization Endpoints
@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    org_data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new organization."""
    service = OrganizationService(db)
    org = service.create_organization(str(current_user.id), org_data)
    return org


@router.get("", response_model=OrganizationListResponse)
def list_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all organizations for current user."""
    service = OrganizationService(db)
    orgs = service.get_user_organizations(str(current_user.id))
    return {"organizations": orgs, "total": len(orgs)}


@router.get("/{org_id}", response_model=OrganizationResponse)
def get_organization(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get organization by ID."""
    service = OrganizationService(db)
    org = service.get_organization(org_id)
    return org


@router.put("/{org_id}", response_model=OrganizationResponse)
def update_organization(
    org_id: str,
    org_data: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update organization."""
    service = OrganizationService(db)
    org = service.update_organization(org_id, str(current_user.id), org_data)
    return org


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete organization."""
    service = OrganizationService(db)
    service.delete_organization(org_id, str(current_user.id))


# Organization Member Endpoints
@router.post("/{org_id}/members", response_model=OrganizationMemberResponse, status_code=status.HTTP_201_CREATED)
def invite_member(
    org_id: str,
    invite_data: OrganizationMemberInvite,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Invite a member to organization."""
    service = OrganizationService(db)
    member = service.invite_member(org_id, str(current_user.id), invite_data)
    return member


@router.get("/{org_id}/members", response_model=MemberListResponse)
def list_members(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all members of an organization."""
    service = OrganizationService(db)
    members = service.get_organization_members(org_id)
    return {"members": members, "total": len(members)}


@router.put("/{org_id}/members/{member_id}", response_model=OrganizationMemberResponse)
def update_member(
    org_id: str,
    member_id: str,
    update_data: OrganizationMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update member role."""
    service = OrganizationService(db)
    member = service.update_member_role(org_id, member_id, str(current_user.id), update_data)
    return member


@router.delete("/{org_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    org_id: str,
    member_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a member from organization."""
    service = OrganizationService(db)
    service.remove_member(org_id, member_id, str(current_user.id))


# Team Endpoints
@router.post("/{org_id}/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    org_id: str,
    team_data: TeamCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new team."""
    service = OrganizationService(db)
    team = service.create_team(org_id, str(current_user.id), team_data)
    return team


@router.get("/{org_id}/teams", response_model=TeamListResponse)
def list_teams(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all teams in an organization."""
    service = OrganizationService(db)
    teams = service.get_organization_teams(org_id)
    return {"teams": teams, "total": len(teams)}


@router.get("/teams/{team_id}", response_model=TeamResponse)
def get_team(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get team by ID."""
    service = OrganizationService(db)
    team = service.get_team(team_id)
    return team


@router.put("/teams/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: str,
    team_data: TeamUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update team."""
    service = OrganizationService(db)
    team = service.update_team(team_id, str(current_user.id), team_data)
    return team


@router.delete("/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete team."""
    service = OrganizationService(db)
    service.delete_team(team_id, str(current_user.id))


# Team Member Endpoints
@router.post("/teams/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
def add_team_member(
    team_id: str,
    member_data: TeamMemberAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a member to a team."""
    service = OrganizationService(db)
    member = service.add_team_member(team_id, str(current_user.id), member_data)
    return member


@router.get("/teams/{team_id}/members", response_model=List[TeamMemberResponse])
def list_team_members(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all members of a team."""
    service = OrganizationService(db)
    members = service.get_team_members(team_id)
    return members


@router.delete("/teams/{team_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_team_member(
    team_id: str,
    member_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a member from a team."""
    service = OrganizationService(db)
    service.remove_team_member(team_id, member_id, str(current_user.id))
