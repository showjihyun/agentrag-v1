"""Pydantic models for organization and team management."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class OrganizationRole(str, Enum):
    """Organization-level roles."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class TeamRole(str, Enum):
    """Team-level roles."""
    LEAD = "lead"
    MEMBER = "member"
    VIEWER = "viewer"


class OrganizationPlan(str, Enum):
    """Subscription plans."""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# Organization Schemas
class OrganizationBase(BaseModel):
    """Base organization schema."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization."""
    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    plan: Optional[OrganizationPlan] = None


class OrganizationResponse(OrganizationBase):
    """Schema for organization response."""
    id: str
    plan: str
    max_members: int
    max_agents: int
    max_workflows: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    member_count: Optional[int] = None
    team_count: Optional[int] = None

    class Config:
        from_attributes = True


# Organization Member Schemas
class OrganizationMemberBase(BaseModel):
    """Base organization member schema."""
    user_id: str
    role: OrganizationRole


class OrganizationMemberInvite(BaseModel):
    """Schema for inviting a member."""
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    role: OrganizationRole = OrganizationRole.MEMBER


class OrganizationMemberUpdate(BaseModel):
    """Schema for updating a member."""
    role: OrganizationRole


class OrganizationMemberResponse(BaseModel):
    """Schema for organization member response."""
    id: str
    organization_id: str
    user_id: str
    role: OrganizationRole
    invited_at: datetime
    joined_at: Optional[datetime]
    is_active: bool
    user_email: Optional[str] = None
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


# Team Schemas
class TeamBase(BaseModel):
    """Base team schema."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = None


class TeamCreate(TeamBase):
    """Schema for creating a team."""
    pass


class TeamUpdate(BaseModel):
    """Schema for updating a team."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class TeamResponse(TeamBase):
    """Schema for team response."""
    id: str
    organization_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    member_count: Optional[int] = None

    class Config:
        from_attributes = True


# Team Member Schemas
class TeamMemberBase(BaseModel):
    """Base team member schema."""
    user_id: str
    role: TeamRole


class TeamMemberAdd(BaseModel):
    """Schema for adding a team member."""
    user_id: str
    role: TeamRole = TeamRole.MEMBER


class TeamMemberUpdate(BaseModel):
    """Schema for updating a team member."""
    role: TeamRole


class TeamMemberResponse(BaseModel):
    """Schema for team member response."""
    id: str
    team_id: str
    user_id: str
    role: TeamRole
    added_at: datetime
    is_active: bool
    user_email: Optional[str] = None
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


# List Responses
class OrganizationListResponse(BaseModel):
    """Schema for organization list response."""
    organizations: List[OrganizationResponse]
    total: int


class TeamListResponse(BaseModel):
    """Schema for team list response."""
    teams: List[TeamResponse]
    total: int


class MemberListResponse(BaseModel):
    """Schema for member list response."""
    members: List[OrganizationMemberResponse]
    total: int
