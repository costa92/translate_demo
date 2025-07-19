"""
User and API key store for the knowledge base API.

This module provides storage and management for users and API keys.
"""

import json
import os
import logging
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
import threading
from pathlib import Path

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.exceptions import AuthenticationError, AuthorizationError
from src.knowledge_base.api.models.auth import User, APIKey, Role, Permission

logger = logging.getLogger(__name__)


class AuthStore:
    """Store for users and API keys."""
    
    def __init__(self, config: Config):
        """Initialize the auth store.
        
        Args:
            config: The configuration instance.
        """
        self.config = config
        self.users: Dict[str, User] = {}
        self.api_keys: Dict[str, APIKey] = {}
        self.username_to_id: Dict[str, str] = {}
        self.api_key_to_id: Dict[str, str] = {}
        self._lock = threading.RLock()
        
        # Create default data directory if it doesn't exist
        self.data_dir = Path(os.environ.get("KB_AUTH_DATA_DIR", "./.kb_auth"))
        self.data_dir.mkdir(exist_ok=True, parents=True)
        
        # Load existing data
        self._load_data()
        
        # Create default admin user if no users exist
        if not self.users:
            self._create_default_admin()
    
    def _load_data(self) -> None:
        """Load user and API key data from files."""
        try:
            # Load users
            users_file = self.data_dir / "users.json"
            if users_file.exists():
                with open(users_file, "r") as f:
                    users_data = json.load(f)
                    for user_data in users_data:
                        # Convert datetime strings to datetime objects
                        user_data["created_at"] = datetime.fromisoformat(user_data["created_at"])
                        user_data["updated_at"] = datetime.fromisoformat(user_data["updated_at"])
                        user = User(**user_data)
                        self.users[user.id] = user
                        self.username_to_id[user.username] = user.id
            
            # Load API keys
            api_keys_file = self.data_dir / "api_keys.json"
            if api_keys_file.exists():
                with open(api_keys_file, "r") as f:
                    api_keys_data = json.load(f)
                    for api_key_data in api_keys_data:
                        # Convert datetime strings to datetime objects
                        api_key_data["created_at"] = datetime.fromisoformat(api_key_data["created_at"])
                        if api_key_data.get("expires_at"):
                            api_key_data["expires_at"] = datetime.fromisoformat(api_key_data["expires_at"])
                        if api_key_data.get("last_used_at"):
                            api_key_data["last_used_at"] = datetime.fromisoformat(api_key_data["last_used_at"])
                        api_key = APIKey(**api_key_data)
                        self.api_keys[api_key.id] = api_key
                        self.api_key_to_id[api_key.key] = api_key.id
            
            logger.info(f"Loaded {len(self.users)} users and {len(self.api_keys)} API keys")
        except Exception as e:
            logger.error(f"Error loading auth data: {e}")
    
    def _save_data(self) -> None:
        """Save user and API key data to files."""
        try:
            # Save users
            users_file = self.data_dir / "users.json"
            with open(users_file, "w") as f:
                users_data = [user.dict() for user in self.users.values()]
                # Convert datetime objects to ISO format strings
                for user_data in users_data:
                    user_data["created_at"] = user_data["created_at"].isoformat()
                    user_data["updated_at"] = user_data["updated_at"].isoformat()
                json.dump(users_data, f, indent=2)
            
            # Save API keys
            api_keys_file = self.data_dir / "api_keys.json"
            with open(api_keys_file, "w") as f:
                api_keys_data = [api_key.dict() for api_key in self.api_keys.values()]
                # Convert datetime objects to ISO format strings
                for api_key_data in api_keys_data:
                    api_key_data["created_at"] = api_key_data["created_at"].isoformat()
                    if api_key_data.get("expires_at"):
                        api_key_data["expires_at"] = api_key_data["expires_at"].isoformat()
                    if api_key_data.get("last_used_at"):
                        api_key_data["last_used_at"] = api_key_data["last_used_at"].isoformat()
                json.dump(api_keys_data, f, indent=2)
            
            logger.debug("Auth data saved successfully")
        except Exception as e:
            logger.error(f"Error saving auth data: {e}")
    
    def _create_default_admin(self) -> None:
        """Create a default admin user and API key."""
        with self._lock:
            # Create admin user
            admin_user = User(
                username="admin",
                email="admin@example.com",
                full_name="System Administrator",
                roles=[Role.ADMIN]
            )
            self.users[admin_user.id] = admin_user
            self.username_to_id[admin_user.username] = admin_user.id
            
            # Create admin API key
            admin_api_key = APIKey(
                name="Default Admin Key",
                user_id=admin_user.id
            )
            self.api_keys[admin_api_key.id] = admin_api_key
            self.api_key_to_id[admin_api_key.key] = admin_api_key.id
            
            logger.info(f"Created default admin user with API key: {admin_api_key.key}")
            
            # Save data
            self._save_data()
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID.
        
        Args:
            user_id: The user ID.
            
        Returns:
            The user, or None if not found.
        """
        return self.users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username.
        
        Args:
            username: The username.
            
        Returns:
            The user, or None if not found.
        """
        user_id = self.username_to_id.get(username)
        if user_id:
            return self.users.get(user_id)
        return None
    
    def get_api_key(self, key: str) -> Optional[APIKey]:
        """Get an API key by key value.
        
        Args:
            key: The API key value.
            
        Returns:
            The API key, or None if not found.
        """
        api_key_id = self.api_key_to_id.get(key)
        if api_key_id:
            return self.api_keys.get(api_key_id)
        return None
    
    def authenticate_api_key(self, key: str) -> Optional[User]:
        """Authenticate an API key and return the associated user.
        
        Args:
            key: The API key value.
            
        Returns:
            The user associated with the API key, or None if authentication fails.
        """
        api_key = self.get_api_key(key)
        if not api_key or not api_key.is_valid():
            return None
        
        # Update last used timestamp
        with self._lock:
            api_key.last_used_at = datetime.utcnow()
            self._save_data()
        
        # Get associated user
        user = self.get_user_by_id(api_key.user_id)
        if not user or user.disabled:
            return None
        
        return user
    
    def create_user(self, username: str, email: Optional[str] = None, 
                   full_name: Optional[str] = None, roles: List[Role] = None,
                   custom_permissions: List[Permission] = None) -> User:
        """Create a new user.
        
        Args:
            username: The username.
            email: The email address.
            full_name: The full name.
            roles: The roles.
            custom_permissions: Custom permissions.
            
        Returns:
            The created user.
            
        Raises:
            AuthorizationError: If a user with the same username already exists.
        """
        with self._lock:
            # Check if username already exists
            if username in self.username_to_id:
                raise AuthorizationError(f"User with username '{username}' already exists")
            
            # Create user
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                roles=roles or [Role.READER],
                custom_permissions=custom_permissions or []
            )
            
            # Add user to store
            self.users[user.id] = user
            self.username_to_id[user.username] = user.id
            
            # Save data
            self._save_data()
            
            return user
    
    def update_user(self, user_id: str, email: Optional[str] = None,
                   full_name: Optional[str] = None, disabled: Optional[bool] = None,
                   roles: Optional[List[Role]] = None,
                   custom_permissions: Optional[List[Permission]] = None) -> User:
        """Update a user.
        
        Args:
            user_id: The user ID.
            email: The email address.
            full_name: The full name.
            disabled: Whether the user is disabled.
            roles: The roles.
            custom_permissions: Custom permissions.
            
        Returns:
            The updated user.
            
        Raises:
            AuthorizationError: If the user does not exist.
        """
        with self._lock:
            # Check if user exists
            user = self.get_user_by_id(user_id)
            if not user:
                raise AuthorizationError(f"User with ID '{user_id}' not found")
            
            # Update user
            if email is not None:
                user.email = email
            if full_name is not None:
                user.full_name = full_name
            if disabled is not None:
                user.disabled = disabled
            if roles is not None:
                user.roles = roles
            if custom_permissions is not None:
                user.custom_permissions = custom_permissions
            
            user.updated_at = datetime.utcnow()
            
            # Save data
            self._save_data()
            
            return user
    
    def delete_user(self, user_id: str) -> None:
        """Delete a user.
        
        Args:
            user_id: The user ID.
            
        Raises:
            AuthorizationError: If the user does not exist.
        """
        with self._lock:
            # Check if user exists
            user = self.get_user_by_id(user_id)
            if not user:
                raise AuthorizationError(f"User with ID '{user_id}' not found")
            
            # Remove user
            username = user.username
            del self.users[user_id]
            del self.username_to_id[username]
            
            # Remove associated API keys
            api_keys_to_remove = []
            for api_key_id, api_key in self.api_keys.items():
                if api_key.user_id == user_id:
                    api_keys_to_remove.append(api_key_id)
                    if api_key.key in self.api_key_to_id:
                        del self.api_key_to_id[api_key.key]
            
            for api_key_id in api_keys_to_remove:
                del self.api_keys[api_key_id]
            
            # Save data
            self._save_data()
    
    def create_api_key(self, name: str, user_id: str, expires_at: Optional[datetime] = None) -> APIKey:
        """Create a new API key.
        
        Args:
            name: The API key name.
            user_id: The user ID.
            expires_at: The expiration date.
            
        Returns:
            The created API key.
            
        Raises:
            AuthorizationError: If the user does not exist.
        """
        with self._lock:
            # Check if user exists
            user = self.get_user_by_id(user_id)
            if not user:
                raise AuthorizationError(f"User with ID '{user_id}' not found")
            
            # Create API key
            api_key = APIKey(
                name=name,
                user_id=user_id,
                expires_at=expires_at
            )
            
            # Add API key to store
            self.api_keys[api_key.id] = api_key
            self.api_key_to_id[api_key.key] = api_key.id
            
            # Save data
            self._save_data()
            
            return api_key
    
    def update_api_key(self, api_key_id: str, name: Optional[str] = None,
                      enabled: Optional[bool] = None, expires_at: Optional[datetime] = None) -> APIKey:
        """Update an API key.
        
        Args:
            api_key_id: The API key ID.
            name: The API key name.
            enabled: Whether the API key is enabled.
            expires_at: The expiration date.
            
        Returns:
            The updated API key.
            
        Raises:
            AuthorizationError: If the API key does not exist.
        """
        with self._lock:
            # Check if API key exists
            api_key = self.api_keys.get(api_key_id)
            if not api_key:
                raise AuthorizationError(f"API key with ID '{api_key_id}' not found")
            
            # Update API key
            if name is not None:
                api_key.name = name
            if enabled is not None:
                api_key.enabled = enabled
            if expires_at is not None:
                api_key.expires_at = expires_at
            
            # Save data
            self._save_data()
            
            return api_key
    
    def delete_api_key(self, api_key_id: str) -> None:
        """Delete an API key.
        
        Args:
            api_key_id: The API key ID.
            
        Raises:
            AuthorizationError: If the API key does not exist.
        """
        with self._lock:
            # Check if API key exists
            api_key = self.api_keys.get(api_key_id)
            if not api_key:
                raise AuthorizationError(f"API key with ID '{api_key_id}' not found")
            
            # Remove API key
            key = api_key.key
            del self.api_keys[api_key_id]
            if key in self.api_key_to_id:
                del self.api_key_to_id[key]
            
            # Save data
            self._save_data()
    
    def list_users(self) -> List[User]:
        """List all users.
        
        Returns:
            A list of all users.
        """
        return list(self.users.values())
    
    def list_api_keys(self, user_id: Optional[str] = None) -> List[APIKey]:
        """List API keys.
        
        Args:
            user_id: Filter by user ID.
            
        Returns:
            A list of API keys.
        """
        if user_id:
            return [api_key for api_key in self.api_keys.values() if api_key.user_id == user_id]
        return list(self.api_keys.values())