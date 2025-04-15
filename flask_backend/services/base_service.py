"""
Base Service Interface

This module defines the standard interface that all services must implement
to ensure a consistent service pattern across the application.
"""
from abc import ABC, abstractmethod
import logging

# Logger
logger = logging.getLogger(__name__)

class BaseService(ABC):
    """Base service interface that all services must implement"""
    
    @abstractmethod
    def init_app(self, app):
        """
        Initialize the service with the Flask app
        
        Args:
            app: Flask application instance
        """
        pass
        
    @property
    @abstractmethod
    def initialized(self):
        """
        Return whether the service is initialized
        
        Returns:
            bool: True if initialized, False otherwise
        """
        pass
        
    @abstractmethod
    def health_check(self):
        """
        Return the health status of the service
        
        Returns:
            dict: Health status information with at least 'status' and 'message' keys
        """
        pass