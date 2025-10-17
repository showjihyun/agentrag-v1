"""Permission and Group models for ACL."""

from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from backend.db.database import Base


class PermissionType(str, enum.Enum):
    """Permission types with hierarchy: admin > write > read."""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class DocumentPermission(Base):
    """Document access control permissions."""

    __tablename__ = "document_permissions"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    granted_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Permission Details
    permission_type = Column(
        SQLEnum(PermissionType), nullable=False, default=PermissionType.READ
    )

    # Timestamps
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    document = relationship("Document", foreign_keys=[document_id])
    user = relationship("User", foreign_keys=[user_id])
    group = relationship("Group", foreign_keys=[group_id])
    granter = relationship("User", foreign_keys=[granted_by])

    # Constraints
    __table_args__ = (
        # Either user_id or group_id must be set, but not both
        UniqueConstraint("document_id", "user_id", name="uq_document_user_permission"),
        UniqueConstraint(
            "document_id", "group_id", name="uq_document_group_permission"
        ),
        Index("ix_document_permissions_document", "document_id"),
        Index("ix_document_permissions_user", "user_id"),
        Index("ix_document_permissions_group", "group_id"),
    )

    def __repr__(self):
        target = f"user={self.user_id}" if self.user_id else f"group={self.group_id}"
        return f"<DocumentPermission(id={self.id}, document={self.document_id}, {target}, type={self.permission_type})>"


class Group(Base):
    """User groups for permission management."""

    __tablename__ = "groups"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Group Information
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(String(500), nullable=True)

    # Foreign Keys
    created_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    members = relationship(
        "GroupMember", back_populates="group", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Group(id={self.id}, name={self.name})>"


class GroupMember(Base):
    """Group membership."""

    __tablename__ = "group_members"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    added_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Timestamps
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    group = relationship("Group", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])
    adder = relationship("User", foreign_keys=[added_by])

    # Constraints
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_user_membership"),
        Index("ix_group_members_group", "group_id"),
        Index("ix_group_members_user", "user_id"),
    )

    def __repr__(self):
        return (
            f"<GroupMember(id={self.id}, group={self.group_id}, user={self.user_id})>"
        )
