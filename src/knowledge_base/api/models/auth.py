"""
Authentication and authorization models for the knowledge base API.

This module provides models for users, permissions, and API keys.
"""

from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field, validator


class Permission(str, Enum):
    """Permission types for the knowledge base API."""
    # Knowledge management permissions
    KNOWLEDGE_READ = "knowledge:read"
    KNOWLEDGE_WRITE = "knowledge:write"
    KNOWLEDGE_DELETE = "knowledge:delete"
    
    # Query permissions
    QUERY_BASIC = "query:basic"
    QUERY_ADVANCED = "query:advanced"
    
    # Admin permissions
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    ADMIN_SYSTEM = "admin:system"
    
    # User management permissions
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"


class Role(str, Enum):
    """Predefined roles with associated permissions."""
    READER = "reader"  # Can only read knowledge and perform basic queries
    CONTRIBUTOR = "contributor"  # Can read and write knowledge, perform queries
    ADMIN = "admin"  # Full access to all features
    SYSTEM = "system"  # Special role for system operations


# Define permission sets for each role
ROLE_PERMISSIONS = {
    Role.READER: {
        Permission.KNOWLEDGE_READ,
        Permission.QUERY_BASIC,
    },
    Role.CONTRIBUTOR: {
        Permission.KNOWLEDGE_READ,
        Permission.KNOWLEDGE_WRITE,
        Permission.QUERY_BASIC,
        Permission.QUERY_ADVANCED,
    },
    Role.ADMIN: {
        Permission.KNOWLEDGE_READ,
        Permission.KNOWLEDGE_WRITE,
        Permission.KNOWLEDGE_DELETE,
        Permission.QUERY_BASIC,
        Permission.QUERY_ADVANCED,
        Permission.ADMIN_READ,
        Permission.ADMIN_WRITE,
        Permission.USER_READ,
        Permission.USER_WRITE,
    },
    Role.SYSTEM: {
        Permission.KNOWLEDGE_READ,
        Permission.KNOWLEDGE_WRITE,
        Permission.KNOWLEDGE_DELETE,
        Permission.QUERY_BASIC,
        Permission.QUERY_ADVANCED,
        Permission.ADMIN_READ,
        Permission.ADMIN_WRITE,
        Permission.ADMIN_SYSTEM,
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.USER_DELETE,
    }
}


class User(BaseModel):
    """User model for authentication and authorization."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: bool = False
    roles: List[Role] = Field(default_factory=lambda: [Role.READER])
    custom_permissions: List[Permission] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if the user has a specific permission.
        
        Args:
            permission: The permission to check.
            
        Returns:
            True if the user has the permission, False otherwise.
        """
        if self.disabled:
            return False
            
        # Check custom permissions
        if permission in self.custom_permissions:
            return True
            
        # Check role-based permissions
        for role in self.roles:
            if permission in ROLE_PERMISSIONS.get(role, set()):
                return True
                
        return False
    
    def get_permissions(self) -> Set[Permission]:
        """Get all permissions for the user.
        
        Returns:
            A set of all permissions the user has.
        """
        if self.disabled:
            return set()
            
        permissions = set(self.custom_permissions)
        
        # Add role-based permissions
        for role in self.roles:
            permissions.update(ROLE_PERMISSIONS.get(role, set()))
            
        return permissions


class APIKey(BaseModel):
    """API key model for authentication."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    key: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    user_id: str
    enabled: bool = True
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None
    
    def is_valid(self) -> bool:
        """Check if the API key is valid.
        
        Returns:
            True if the API key is valid, False otherwise.
        """
        if not self.enabled:
            return False
            
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
            
        return True


class UserCreate(BaseModel):
    """Model for creating a new user."""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    roles: List[Role] = Field(default_factory=lambda: [Role.READER])
    custom_permissions: List[Permission] = Field(default_factory=list)
    
    @validator('username')
    def username_must_be_valid(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if not v.isalnum() and '_' not in v and '-' not in v:
            raise ValueError('Username must contain only alphanumeric characters, underscores, or hyphens')
        return v


class UserUpdate(BaseModel):
    """Model for updating a user."""
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    roles: Optional[List[Role]] = None
    custom_permissions: Optional[List[Permission]] = None


class APIKeyCreate(BaseModel):
    """Model for creating a new API key."""
    name: str
    user_id: str
    expires_at: Optional[datetime] = None
    
    @validator('name')
    def name_must_be_valid(cls, v):
        if len(v) < 3:
            raise ValueError('API key name must be at least 3 characters')
        return v


class APIKeyResponse(BaseModel):
    """Response model for API key creation."""
    id: str
    key: str
    name: str
    user_id: str
    enabled: bool
    expires_at: Optional[datetime] = None
    created_at: datetime


class UserResponse(BaseModel):
    """Response model for user information."""
    id: str
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: bool
    roles: List[Role]
    custom_permissions: List[Permission]
    created_at: datetime
    updated_at: datetime