"""
User management routes for the knowledge base API.

This module provides routes for user and API key management.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.exceptions import AuthorizationError
from src.knowledge_base.api.auth.store import AuthStore
from src.knowledge_base.api.models.auth import (
    User, APIKey, Role, Permission,
    UserCreate, UserUpdate, APIKeyCreate, APIKeyResponse, UserResponse
)
from ..dependencies import get_config

router = APIRouter(prefix="/admin", tags=["User Management"])


def get_auth_store(config: Config = Depends(get_config)) -> AuthStore:
    """Get the auth store instance.
    
    Args:
        config: The configuration instance.
        
    Returns:
        The auth store instance.
    """
    return AuthStore(config)


def get_current_user(request) -> User:
    """Get the current authenticated user.
    
    Args:
        request: The request object.
        
    Returns:
        The current user.
        
    Raises:
        HTTPException: If no user is authenticated.
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    auth_store: AuthStore = Depends(get_auth_store)
):
    """List all users.
    
    Args:
        auth_store: The auth store instance.
        
    Returns:
        A list of all users.
    """
    return auth_store.list_users()


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str = Path(..., description="The user ID"),
    auth_store: AuthStore = Depends(get_auth_store)
):
    """Get a user by ID.
    
    Args:
        user_id: The user ID.
        auth_store: The auth store instance.
        
    Returns:
        The user.
        
    Raises:
        HTTPException: If the user does not exist.
    """
    user = auth_store.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID '{user_id}' not found")
    return user


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_create: UserCreate,
    auth_store: AuthStore = Depends(get_auth_store)
):
    """Create a new user.
    
    Args:
        user_create: The user creation data.
        auth_store: The auth store instance.
        
    Returns:
        The created user.
        
    Raises:
        HTTPException: If a user with the same username already exists.
    """
    try:
        user = auth_store.create_user(
            username=user_create.username,
            email=user_create.email,
            full_name=user_create.full_name,
            roles=user_create.roles,
            custom_permissions=user_create.custom_permissions
        )
        return user
    except AuthorizationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_update: UserUpdate,
    user_id: str = Path(..., description="The user ID"),
    auth_store: AuthStore = Depends(get_auth_store)
):
    """Update a user.
    
    Args:
        user_update: The user update data.
        user_id: The user ID.
        auth_store: The auth store instance.
        
    Returns:
        The updated user.
        
    Raises:
        HTTPException: If the user does not exist.
    """
    try:
        user = auth_store.update_user(
            user_id=user_id,
            email=user_update.email,
            full_name=user_update.full_name,
            disabled=user_update.disabled,
            roles=user_update.roles,
            custom_permissions=user_update.custom_permissions
        )
        return user
    except AuthorizationError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/users/{user_id}", response_model=Dict[str, str])
async def delete_user(
    user_id: str = Path(..., description="The user ID"),
    auth_store: AuthStore = Depends(get_auth_store)
):
    """Delete a user.
    
    Args:
        user_id: The user ID.
        auth_store: The auth store instance.
        
    Returns:
        A success message.
        
    Raises:
        HTTPException: If the user does not exist.
    """
    try:
        auth_store.delete_user(user_id)
        return {"message": f"User with ID '{user_id}' deleted successfully"}
    except AuthorizationError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    auth_store: AuthStore = Depends(get_auth_store)
):
    """List API keys.
    
    Args:
        user_id: Filter by user ID.
        auth_store: The auth store instance.
        
    Returns:
        A list of API keys.
    """
    return auth_store.list_api_keys(user_id)


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    api_key_create: APIKeyCreate,
    auth_store: AuthStore = Depends(get_auth_store)
):
    """Create a new API key.
    
    Args:
        api_key_create: The API key creation data.
        auth_store: The auth store instance.
        
    Returns:
        The created API key.
        
    Raises:
        HTTPException: If the user does not exist.
    """
    try:
        api_key = auth_store.create_api_key(
            name=api_key_create.name,
            user_id=api_key_create.user_id,
            expires_at=api_key_create.expires_at
        )
        return api_key
    except AuthorizationError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/api-keys/{api_key_id}", response_model=APIKeyResponse)
async def update_api_key(
    name: Optional[str] = Query(None, description="New API key name"),
    enabled: Optional[bool] = Query(None, description="Whether the API key is enabled"),
    expires_in_days: Optional[int] = Query(None, description="Days until expiration"),
    api_key_id: str = Path(..., description="The API key ID"),
    auth_store: AuthStore = Depends(get_auth_store)
):
    """Update an API key.
    
    Args:
        name: The new API key name.
        enabled: Whether the API key is enabled.
        expires_in_days: Days until expiration.
        api_key_id: The API key ID.
        auth_store: The auth store instance.
        
    Returns:
        The updated API key.
        
    Raises:
        HTTPException: If the API key does not exist.
    """
    # Calculate expiration date if specified
    expires_at = None
    if expires_in_days is not None:
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
    
    try:
        api_key = auth_store.update_api_key(
            api_key_id=api_key_id,
            name=name,
            enabled=enabled,
            expires_at=expires_at
        )
        return api_key
    except AuthorizationError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/api-keys/{api_key_id}", response_model=Dict[str, str])
async def delete_api_key(
    api_key_id: str = Path(..., description="The API key ID"),
    auth_store: AuthStore = Depends(get_auth_store)
):
    """Delete an API key.
    
    Args:
        api_key_id: The API key ID.
        auth_store: The auth store instance.
        
    Returns:
        A success message.
        
    Raises:
        HTTPException: If the API key does not exist.
    """
    try:
        auth_store.delete_api_key(api_key_id)
        return {"message": f"API key with ID '{api_key_id}' deleted successfully"}
    except AuthorizationError as e:
        raise HTTPException(status_code=404, detail=str(e))