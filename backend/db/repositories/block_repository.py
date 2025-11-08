"""Block Repository for data access layer."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.db.models.agent_builder import (
    Block,
    BlockVersion,
    BlockTestCase,
    BlockDependency
)

logger = logging.getLogger(__name__)


class BlockRepository:
    """Repository for Block data access."""
    
    def __init__(self, db: Session):
        """
        Initialize Block Repository.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create(self, block: Block) -> Block:
        """
        Create a new block.
        
        Args:
            block: Block model to create
            
        Returns:
            Created Block model
        """
        self.db.add(block)
        self.db.flush()
        return block
    
    def find_by_id(self, block_id: str) -> Optional[Block]:
        """
        Find block by ID.
        
        Args:
            block_id: Block ID
            
        Returns:
            Block model or None if not found
        """
        return self.db.query(Block).filter(Block.id == block_id).first()
    
    def find_by_user(
        self,
        user_id: str,
        block_type: Optional[str] = None,
        is_public: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Block]:
        """
        Find blocks by user ID with filters.
        
        Args:
            user_id: User ID
            block_type: Filter by block type (optional)
            is_public: Filter by public status (optional)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of Block models
        """
        query = self.db.query(Block).filter(Block.user_id == user_id)
        
        if block_type:
            query = query.filter(Block.block_type == block_type)
        
        if is_public is not None:
            query = query.filter(Block.is_public == is_public)
        
        query = query.order_by(Block.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def find_public(
        self,
        block_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Block]:
        """
        Find public blocks.
        
        Args:
            block_type: Filter by block type (optional)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of public Block models
        """
        query = self.db.query(Block).filter(Block.is_public == True)
        
        if block_type:
            query = query.filter(Block.block_type == block_type)
        
        query = query.order_by(Block.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def update(self, block: Block) -> Block:
        """
        Update a block.
        
        Args:
            block: Block model to update
            
        Returns:
            Updated Block model
        """
        block.updated_at = datetime.utcnow()
        self.db.flush()
        return block
    
    def delete(self, block: Block) -> None:
        """
        Delete a block.
        
        Args:
            block: Block model to delete
        """
        self.db.delete(block)
        self.db.flush()
    
    def exists(self, block_id: str) -> bool:
        """
        Check if block exists.
        
        Args:
            block_id: Block ID
            
        Returns:
            True if exists, False otherwise
        """
        return self.db.query(Block).filter(Block.id == block_id).count() > 0
    
    def count_by_user(self, user_id: str, block_type: Optional[str] = None) -> int:
        """
        Count blocks by user.
        
        Args:
            user_id: User ID
            block_type: Filter by block type (optional)
            
        Returns:
            Count of blocks
        """
        query = self.db.query(Block).filter(Block.user_id == user_id)
        
        if block_type:
            query = query.filter(Block.block_type == block_type)
        
        return query.count()
    
    def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        block_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Block]:
        """
        Search blocks by name or description.
        
        Args:
            query: Search query
            user_id: Filter by user ID (optional)
            block_type: Filter by block type (optional)
            limit: Maximum number of results
            
        Returns:
            List of Block models
        """
        search_filter = or_(
            Block.name.ilike(f"%{query}%"),
            Block.description.ilike(f"%{query}%")
        )
        
        db_query = self.db.query(Block).filter(search_filter)
        
        if user_id:
            db_query = db_query.filter(
                or_(
                    Block.user_id == user_id,
                    Block.is_public == True
                )
            )
        else:
            db_query = db_query.filter(Block.is_public == True)
        
        if block_type:
            db_query = db_query.filter(Block.block_type == block_type)
        
        return db_query.order_by(Block.created_at.desc()).limit(limit).all()


class BlockVersionRepository:
    """Repository for BlockVersion data access."""
    
    def __init__(self, db: Session):
        """
        Initialize BlockVersion Repository.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create(self, version: BlockVersion) -> BlockVersion:
        """
        Create a new block version.
        
        Args:
            version: BlockVersion model to create
            
        Returns:
            Created BlockVersion model
        """
        self.db.add(version)
        self.db.flush()
        return version
    
    def find_by_block(self, block_id: str) -> List[BlockVersion]:
        """
        Find versions by block ID.
        
        Args:
            block_id: Block ID
            
        Returns:
            List of BlockVersion models
        """
        return self.db.query(BlockVersion).filter(
            BlockVersion.block_id == block_id
        ).order_by(BlockVersion.created_at.desc()).all()
    
    def find_latest(self, block_id: str) -> Optional[BlockVersion]:
        """
        Find latest version for a block.
        
        Args:
            block_id: Block ID
            
        Returns:
            Latest BlockVersion model or None
        """
        return self.db.query(BlockVersion).filter(
            BlockVersion.block_id == block_id
        ).order_by(BlockVersion.created_at.desc()).first()
    
    def find_by_version_number(
        self,
        block_id: str,
        version_number: str
    ) -> Optional[BlockVersion]:
        """
        Find version by version number.
        
        Args:
            block_id: Block ID
            version_number: Version number
            
        Returns:
            BlockVersion model or None
        """
        return self.db.query(BlockVersion).filter(
            BlockVersion.block_id == block_id,
            BlockVersion.version_number == version_number
        ).first()


class BlockTestCaseRepository:
    """Repository for BlockTestCase data access."""
    
    def __init__(self, db: Session):
        """
        Initialize BlockTestCase Repository.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create(self, test_case: BlockTestCase) -> BlockTestCase:
        """
        Create a new block test case.
        
        Args:
            test_case: BlockTestCase model to create
            
        Returns:
            Created BlockTestCase model
        """
        self.db.add(test_case)
        self.db.flush()
        return test_case
    
    def find_by_id(self, test_case_id: str) -> Optional[BlockTestCase]:
        """
        Find test case by ID.
        
        Args:
            test_case_id: Test case ID
            
        Returns:
            BlockTestCase model or None if not found
        """
        return self.db.query(BlockTestCase).filter(
            BlockTestCase.id == test_case_id
        ).first()
    
    def find_by_block(self, block_id: str) -> List[BlockTestCase]:
        """
        Find test cases by block ID.
        
        Args:
            block_id: Block ID
            
        Returns:
            List of BlockTestCase models
        """
        return self.db.query(BlockTestCase).filter(
            BlockTestCase.block_id == block_id
        ).order_by(BlockTestCase.created_at.desc()).all()
    
    def update(self, test_case: BlockTestCase) -> BlockTestCase:
        """
        Update a test case.
        
        Args:
            test_case: BlockTestCase model to update
            
        Returns:
            Updated BlockTestCase model
        """
        test_case.updated_at = datetime.utcnow()
        self.db.flush()
        return test_case
    
    def delete(self, test_case: BlockTestCase) -> None:
        """
        Delete a test case.
        
        Args:
            test_case: BlockTestCase model to delete
        """
        self.db.delete(test_case)
        self.db.flush()
    
    def count_by_block(self, block_id: str) -> int:
        """
        Count test cases by block.
        
        Args:
            block_id: Block ID
            
        Returns:
            Count of test cases
        """
        return self.db.query(BlockTestCase).filter(
            BlockTestCase.block_id == block_id
        ).count()


class BlockDependencyRepository:
    """Repository for BlockDependency data access."""
    
    def __init__(self, db: Session):
        """
        Initialize BlockDependency Repository.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create(self, dependency: BlockDependency) -> BlockDependency:
        """
        Create a new block dependency.
        
        Args:
            dependency: BlockDependency model to create
            
        Returns:
            Created BlockDependency model
        """
        self.db.add(dependency)
        self.db.flush()
        return dependency
    
    def find_by_parent(self, parent_block_id: str) -> List[BlockDependency]:
        """
        Find dependencies by parent block ID.
        
        Args:
            parent_block_id: Parent block ID
            
        Returns:
            List of BlockDependency models
        """
        return self.db.query(BlockDependency).filter(
            BlockDependency.parent_block_id == parent_block_id
        ).all()
    
    def find_by_child(self, child_block_id: str) -> List[BlockDependency]:
        """
        Find dependencies by child block ID.
        
        Args:
            child_block_id: Child block ID
            
        Returns:
            List of BlockDependency models
        """
        return self.db.query(BlockDependency).filter(
            BlockDependency.child_block_id == child_block_id
        ).all()
    
    def delete(self, dependency: BlockDependency) -> None:
        """
        Delete a dependency.
        
        Args:
            dependency: BlockDependency model to delete
        """
        self.db.delete(dependency)
        self.db.flush()
    
    def exists(self, parent_block_id: str, child_block_id: str) -> bool:
        """
        Check if dependency exists.
        
        Args:
            parent_block_id: Parent block ID
            child_block_id: Child block ID
            
        Returns:
            True if exists, False otherwise
        """
        return self.db.query(BlockDependency).filter(
            BlockDependency.parent_block_id == parent_block_id,
            BlockDependency.child_block_id == child_block_id
        ).count() > 0
