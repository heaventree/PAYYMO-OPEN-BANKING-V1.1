"""
Key Rotation Utility
-------------------
Provides secure key rotation functionality for production environments.
This allows for safe rotation of encryption keys, JWT secrets, and other
sensitive credentials without service disruption.
"""

import os
import logging
import datetime
from typing import Dict, Any, Optional, List, Tuple

# Logger
logger = logging.getLogger(__name__)

class KeyRotationManager:
    """Manages secure key rotation for the application"""
    
    def __init__(self):
        """Initialize the key rotation manager"""
        self.rotation_history = {}
        self.active_versions = {}
        self.initialized = False
        
    def init_app(self, app):
        """
        Initialize the key rotation manager with a Flask app
        
        Args:
            app: Flask application instance
        """
        self.app = app
        self._load_rotation_history()
        self.initialized = True
        logger.info("Key rotation manager initialized")
        
    def _load_rotation_history(self):
        """Load key rotation history from database or file"""
        # In a real implementation, this would load from a secure location
        # For now, we'll initialize with empty history
        self.rotation_history = {}
        self.active_versions = {}
        
    def register_key(self, key_name: str, current_value: str, version: int = 1) -> bool:
        """
        Register a key for rotation management
        
        Args:
            key_name: Name of the key to register
            current_value: Current value of the key
            version: Version number for this key
            
        Returns:
            Success status
        """
        if not self.initialized:
            logger.error("Key rotation manager not initialized")
            return False
            
        if key_name not in self.rotation_history:
            self.rotation_history[key_name] = []
            
        # Add current key to history
        self.rotation_history[key_name].append({
            'version': version,
            'value': current_value,
            'created_at': datetime.datetime.utcnow(),
            'retired_at': None,
            'is_active': True
        })
        
        # Set as active version
        self.active_versions[key_name] = version
        
        logger.info(f"Registered key '{key_name}' (version {version})")
        return True
        
    def rotate_key(self, key_name: str, new_value: str) -> Optional[int]:
        """
        Rotate a key to a new value
        
        Args:
            key_name: Name of the key to rotate
            new_value: New value for the key
            
        Returns:
            New version number or None if failed
        """
        if not self.initialized:
            logger.error("Key rotation manager not initialized")
            return None
            
        if key_name not in self.rotation_history:
            logger.error(f"Cannot rotate unknown key: {key_name}")
            return None
            
        # Get current version
        current_version = self.active_versions.get(key_name, 0)
        new_version = current_version + 1
        
        # Mark previous version as retired
        for entry in self.rotation_history[key_name]:
            if entry['version'] == current_version:
                entry['retired_at'] = datetime.datetime.utcnow()
                entry['is_active'] = False
                break
                
        # Add new version to history
        self.rotation_history[key_name].append({
            'version': new_version,
            'value': new_value,
            'created_at': datetime.datetime.utcnow(),
            'retired_at': None,
            'is_active': True
        })
        
        # Update active version
        self.active_versions[key_name] = new_version
        
        logger.info(f"Rotated key '{key_name}' to version {new_version}")
        return new_version
        
    def get_active_key(self, key_name: str) -> Optional[str]:
        """
        Get the active version of a key
        
        Args:
            key_name: Name of the key to retrieve
            
        Returns:
            Active key value or None if not found
        """
        if not self.initialized:
            logger.error("Key rotation manager not initialized")
            return None
            
        if key_name not in self.rotation_history:
            logger.error(f"Unknown key: {key_name}")
            return None
            
        # Get active version
        active_version = self.active_versions.get(key_name)
        if not active_version:
            logger.error(f"No active version for key: {key_name}")
            return None
            
        # Find active key in history
        for entry in self.rotation_history[key_name]:
            if entry['version'] == active_version:
                return entry['value']
                
        logger.error(f"Active key version {active_version} not found for {key_name}")
        return None
        
    def get_key_by_version(self, key_name: str, version: int) -> Optional[str]:
        """
        Get a specific version of a key
        
        Args:
            key_name: Name of the key to retrieve
            version: Version of the key to retrieve
            
        Returns:
            Key value or None if not found
        """
        if not self.initialized:
            logger.error("Key rotation manager not initialized")
            return None
            
        if key_name not in self.rotation_history:
            logger.error(f"Unknown key: {key_name}")
            return None
            
        # Find requested version in history
        for entry in self.rotation_history[key_name]:
            if entry['version'] == version:
                return entry['value']
                
        logger.error(f"Key version {version} not found for {key_name}")
        return None
        
    def get_all_versions(self, key_name: str) -> List[Dict[str, Any]]:
        """
        Get all versions of a key
        
        Args:
            key_name: Name of the key to retrieve
            
        Returns:
            List of key version entries
        """
        if not self.initialized:
            logger.error("Key rotation manager not initialized")
            return []
            
        if key_name not in self.rotation_history:
            logger.error(f"Unknown key: {key_name}")
            return []
            
        # Return sanitized history (without actual key values)
        sanitized_history = []
        for entry in self.rotation_history[key_name]:
            sanitized_entry = entry.copy()
            sanitized_entry['value'] = '<redacted>'
            sanitized_history.append(sanitized_entry)
            
        return sanitized_history
        
    def has_key(self, key_name: str) -> bool:
        """
        Check if a key exists
        
        Args:
            key_name: Name of the key to check
            
        Returns:
            True if key exists, False otherwise
        """
        return key_name in self.rotation_history
        
    def get_key_info(self, key_name: str) -> Dict[str, Any]:
        """
        Get information about a key
        
        Args:
            key_name: Name of the key to retrieve
            
        Returns:
            Key information dictionary
        """
        if not self.initialized:
            logger.error("Key rotation manager not initialized")
            return {}
            
        if key_name not in self.rotation_history:
            logger.error(f"Unknown key: {key_name}")
            return {}
            
        # Get active version
        active_version = self.active_versions.get(key_name)
        
        # Count versions
        total_versions = len(self.rotation_history[key_name])
        
        # Get creation and last rotation timestamps
        first_created = None
        last_rotated = None
        
        for entry in self.rotation_history[key_name]:
            if not first_created or entry['created_at'] < first_created:
                first_created = entry['created_at']
                
            if entry['version'] == active_version:
                last_rotated = entry['created_at']
                
        return {
            'name': key_name,
            'active_version': active_version,
            'total_versions': total_versions,
            'first_created': first_created,
            'last_rotated': last_rotated,
            'rotation_due': self._is_rotation_due(key_name)
        }
        
    def _is_rotation_due(self, key_name: str) -> bool:
        """
        Check if a key is due for rotation
        
        Args:
            key_name: Name of the key to check
            
        Returns:
            True if rotation is due, False otherwise
        """
        # Default rotation period is 90 days
        rotation_period = datetime.timedelta(days=90)
        
        # Get active version
        active_version = self.active_versions.get(key_name)
        if not active_version:
            return False
            
        # Find active key in history
        for entry in self.rotation_history[key_name]:
            if entry['version'] == active_version:
                # Check if key is older than rotation period
                age = datetime.datetime.utcnow() - entry['created_at']
                return age > rotation_period
                
        return False
        
    def get_rotation_schedule(self) -> List[Dict[str, Any]]:
        """
        Get rotation schedule for all keys
        
        Returns:
            List of key rotation schedules
        """
        if not self.initialized:
            logger.error("Key rotation manager not initialized")
            return []
            
        schedule = []
        
        for key_name in self.rotation_history:
            info = self.get_key_info(key_name)
            
            # Calculate next rotation date
            last_rotated = info.get('last_rotated')
            if last_rotated:
                next_rotation = last_rotated + datetime.timedelta(days=90)
                days_until_rotation = (next_rotation - datetime.datetime.utcnow()).days
            else:
                next_rotation = None
                days_until_rotation = None
                
            schedule.append({
                'name': key_name,
                'active_version': info.get('active_version'),
                'next_rotation': next_rotation,
                'days_until_rotation': days_until_rotation,
                'rotation_due': info.get('rotation_due', False)
            })
            
        # Sort by rotation due status and then by days until rotation
        return sorted(
            schedule,
            key=lambda x: (
                0 if x.get('rotation_due', False) else 1,
                x.get('days_until_rotation', 999)
            )
        )

# Create singleton instance
key_rotation_manager = KeyRotationManager()