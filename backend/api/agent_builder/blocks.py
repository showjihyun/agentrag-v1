"""Agent Builder API endpoints for block management."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
from backend.services.agent_builder.block_service import BlockService
from backend.models.agent_builder import (
    BlockCreate,
    BlockUpdate,
    BlockResponse,
    BlockListResponse,
    BlockTestRequest,
    BlockTestResult,
    BlockVersionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/blocks",
    tags=["agent-builder-blocks"],
)


@router.post(
    "",
    response_model=BlockResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new block",
    description="Create a new reusable block (LLM, Tool, Logic, or Composite).",
)
async def create_block(
    block_data: BlockCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new block.
    
    **Requirements:** 24.1, 24.4
    
    **Request Body:**
    - name: Block name (required)
    - description: Block description
    - block_type: Type (llm, tool, logic, composite)
    - input_schema: JSON schema for inputs
    - output_schema: JSON schema for outputs
    - configuration: Block-specific configuration
    - implementation: Code or workflow definition
    
    **Returns:**
    - Block object with ID and metadata
    
    **Errors:**
    - 400: Invalid request data
    - 401: Unauthorized
    - 500: Internal server error
    """
    try:
        logger.info(f"Creating block for user {current_user.id}: {block_data.name}")
        
        block_service = BlockService(db)
        block = block_service.create_block(
            user_id=str(current_user.id),
            block_data=block_data
        )
        
        logger.info(f"Block created successfully: {block.id}")
        
        # Convert Block ORM object to BlockResponse
        from backend.models.agent_builder import BlockResponse
        return BlockResponse(
            id=str(block.id),
            user_id=str(block.user_id),
            name=block.name,
            description=block.description,
            block_type=block.block_type,
            input_schema=block.input_schema or {},
            output_schema=block.output_schema or {},
            configuration=block.configuration or {},
            implementation=block.implementation,
            is_public=block.is_public,
            created_at=block.created_at,
            updated_at=block.updated_at,
            version_count=0
        )
        
    except ValueError as e:
        logger.warning(f"Invalid block data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create block: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create block"
        )


@router.get(
    "/{block_id}",
    response_model=BlockResponse,
    summary="Get block by ID",
    description="Retrieve a specific block by ID.",
)
async def get_block(
    block_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get block by ID.
    
    **Requirements:** 24.1
    
    **Path Parameters:**
    - block_id: Block UUID
    
    **Returns:**
    - Block object with full details
    
    **Errors:**
    - 401: Unauthorized
    - 403: Forbidden (no permission to access)
    - 404: Block not found
    - 500: Internal server error
    """
    try:
        logger.info(f"Fetching block {block_id} for user {current_user.id}")
        
        block_service = BlockService(db)
        block = block_service.get_block(block_id)
        
        if not block:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Block {block_id} not found"
            )
        
        # Check permissions (owner or public)
        if str(block.user_id) != str(current_user.id) and not block.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this block"
            )
        
        # Convert Block ORM object to BlockResponse
        from backend.models.agent_builder import BlockResponse
        return BlockResponse(
            id=str(block.id),
            user_id=str(block.user_id),
            name=block.name,
            description=block.description,
            block_type=block.block_type,
            input_schema=block.input_schema or {},
            output_schema=block.output_schema or {},
            configuration=block.configuration or {},
            implementation=block.implementation,
            is_public=block.is_public,
            created_at=block.created_at,
            updated_at=block.updated_at,
            version_count=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get block: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve block"
        )


@router.put(
    "/{block_id}",
    response_model=BlockResponse,
    summary="Update block",
    description="Update an existing block. Requires ownership.",
)
async def update_block(
    block_id: str,
    block_data: BlockUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update block.
    
    **Requirements:** 24.1, 27.1
    
    **Path Parameters:**
    - block_id: Block UUID
    
    **Request Body:**
    - Fields to update (all optional)
    
    **Returns:**
    - Updated block object
    
    **Errors:**
    - 400: Invalid request data
    - 401: Unauthorized
    - 403: Forbidden (not owner)
    - 404: Block not found
    - 500: Internal server error
    """
    try:
        logger.info(f"Updating block {block_id} for user {current_user.id}")
        
        block_service = BlockService(db)
        
        # Check ownership
        existing_block = block_service.get_block(block_id)
        if not existing_block:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Block {block_id} not found"
            )
        
        if str(existing_block.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this block"
            )
        
        # Update block
        updated_block = block_service.update_block(block_id, block_data)
        
        logger.info(f"Block updated successfully: {block_id}")
        
        # Convert Block ORM object to BlockResponse
        from backend.models.agent_builder import BlockResponse
        return BlockResponse(
            id=str(updated_block.id),
            user_id=str(updated_block.user_id),
            name=updated_block.name,
            description=updated_block.description,
            block_type=updated_block.block_type,
            input_schema=updated_block.input_schema or {},
            output_schema=updated_block.output_schema or {},
            configuration=updated_block.configuration or {},
            implementation=updated_block.implementation,
            is_public=updated_block.is_public,
            created_at=updated_block.created_at,
            updated_at=updated_block.updated_at,
            version_count=0
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid block data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update block: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update block"
        )


@router.delete(
    "/{block_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete block",
    description="Delete a block. Requires ownership.",
)
async def delete_block(
    block_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete block.
    
    **Requirements:** 24.4
    
    **Path Parameters:**
    - block_id: Block UUID
    
    **Returns:**
    - 204 No Content on success
    
    **Errors:**
    - 401: Unauthorized
    - 403: Forbidden (not owner)
    - 404: Block not found
    - 500: Internal server error
    """
    try:
        logger.info(f"Deleting block {block_id} for user {current_user.id}")
        
        block_service = BlockService(db)
        
        # Check ownership
        existing_block = block_service.get_block(block_id)
        if not existing_block:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Block {block_id} not found"
            )
        
        if existing_block.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this block"
            )
        
        # Delete block
        block_service.delete_block(block_id)
        
        logger.info(f"Block deleted successfully: {block_id}")
        from fastapi.responses import Response
        return Response(status_code=status.HTTP_204_NO_CONTENT)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete block: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete block"
        )


@router.get(
    "",
    response_model=BlockListResponse,
    summary="List blocks",
    description="List blocks with filtering by type and search.",
)
async def list_blocks(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    block_type: Optional[str] = Query(None, description="Filter by block type (llm, tool, logic, composite)"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    include_public: bool = Query(True, description="Include public blocks"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List blocks with filtering.
    
    **Requirements:** 24.1, 25.1
    
    **Query Parameters:**
    - skip: Number of records to skip (default: 0)
    - limit: Maximum records to return (default: 50, max: 100)
    - block_type: Filter by type (llm, tool, logic, composite)
    - search: Search in name and description
    - include_public: Include public blocks (default: true)
    
    **Returns:**
    - List of blocks with pagination metadata
    
    **Errors:**
    - 401: Unauthorized
    - 500: Internal server error
    """
    try:
        logger.info(f"Listing blocks for user {current_user.id}")
        
        block_service = BlockService(db)
        
        # Get blocks with proper parameters
        if include_public:
            # Get user's blocks + public blocks
            user_blocks = block_service.list_blocks(
                user_id=str(current_user.id),
                block_type=block_type,
                limit=limit,
                offset=skip
            )
            public_blocks = block_service.list_blocks(
                is_public=True,
                block_type=block_type,
                limit=limit,
                offset=skip
            )
            # Combine and deduplicate
            blocks_dict = {b.id: b for b in user_blocks + public_blocks}
            blocks = list(blocks_dict.values())
        else:
            # Get only user's blocks
            blocks = block_service.list_blocks(
                user_id=str(current_user.id),
                block_type=block_type,
                limit=limit,
                offset=skip
            )
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            blocks = [
                b for b in blocks
                if search_lower in b.name.lower() or
                (b.description and search_lower in b.description.lower())
            ]
        
        total = len(blocks)
        
        # Convert Block ORM objects to BlockResponse objects
        from backend.models.agent_builder import BlockResponse
        block_responses = []
        for block in blocks:
            block_responses.append(BlockResponse(
                id=str(block.id),
                user_id=str(block.user_id),
                name=block.name,
                description=block.description,
                block_type=block.block_type,
                input_schema=block.input_schema or {},
                output_schema=block.output_schema or {},
                configuration=block.configuration or {},
                implementation=block.implementation,
                is_public=block.is_public,
                created_at=block.created_at,
                updated_at=block.updated_at,
                version_count=0
            ))
        
        return BlockListResponse(
            blocks=block_responses,
            total=total,
            limit=limit,
            offset=skip
        )
        
    except Exception as e:
        logger.error(f"Failed to list blocks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list blocks"
        )


@router.post(
    "/{block_id}/test",
    response_model=BlockTestResult,
    summary="Test block execution",
    description="Execute a block with test inputs to verify functionality.",
)
async def test_block(
    block_id: str,
    test_request: BlockTestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Test block execution.
    
    **Requirements:** 28.1, 28.2
    
    **Path Parameters:**
    - block_id: Block UUID
    
    **Request Body:**
    - test_input: Input data matching block's input schema
    
    **Returns:**
    - Test result with output and execution metrics
    
    **Errors:**
    - 400: Invalid test input
    - 401: Unauthorized
    - 403: Forbidden (no permission to test)
    - 404: Block not found
    - 500: Internal server error
    """
    try:
        logger.info(f"Testing block {block_id} for user {current_user.id}")
        
        block_service = BlockService(db)
        
        # Check if block exists and user has access
        block = block_service.get_block(block_id)
        if not block:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Block {block_id} not found"
            )
        
        # Check permissions (owner or public)
        if block.user_id != str(current_user.id) and not block.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to test this block"
            )
        
        # Test block
        result = await block_service.test_block(
            block_id=block_id,
            test_input=test_request
        )
        
        logger.info(f"Block tested successfully: {block_id}")
        return result
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid test input: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to test block: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test block"
        )





@router.get(
    "/{block_id}/versions",
    response_model=List[BlockVersionResponse],
    summary="Get block version history",
    description="Retrieve version history for a block.",
)
async def get_block_versions(
    block_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get block version history.
    
    **Requirements:** 27.1
    
    **Path Parameters:**
    - block_id: Block UUID
    
    **Returns:**
    - List of block versions
    
    **Errors:**
    - 401: Unauthorized
    - 403: Forbidden (no permission to access)
    - 404: Block not found
    - 500: Internal server error
    """
    try:
        logger.info(f"Fetching versions for block {block_id}")
        
        block_service = BlockService(db)
        
        # Check if block exists and user has access
        block = block_service.get_block(block_id)
        if not block:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Block {block_id} not found"
            )
        
        # Check permissions (owner or public)
        if block.user_id != str(current_user.id) and not block.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this block"
            )
        
        # Get versions
        versions = block_service.get_block_versions(block_id)
        
        return versions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get block versions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve block versions"
        )
