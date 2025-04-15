"""
Service Registry

This module provides a registry for managing service initialization and dependencies.
It ensures that services are initialized in the correct order based on their dependencies.
"""
import logging

# Logger
logger = logging.getLogger(__name__)

class ServiceRegistry:
    """Registry for managing service initialization and dependencies"""
    
    def __init__(self):
        self._services = {}
        self._dependencies = {}
        self._initialized = False
        
    def register(self, name, service, dependencies=None):
        """
        Register a service with the registry
        
        Args:
            name: Name of the service
            service: Service instance
            dependencies: Optional list of service names that this service depends on
        """
        self._services[name] = service
        if dependencies:
            self._dependencies[name] = dependencies
        logger.debug(f"Registered service: {name}")
            
    def initialize(self, app):
        """
        Initialize all services in dependency order
        
        Args:
            app: Flask application instance
        """
        if self._initialized:
            logger.warning("Service registry already initialized")
            return
            
        logger.info("Initializing services...")
        initialized = set()
        
        def init_service(name):
            # Skip if already initialized
            if name in initialized:
                return
                
            # Check if service exists
            if name not in self._services:
                logger.error(f"Service not found: {name}")
                raise KeyError(f"Service not found: {name}")
                
            # Initialize dependencies first
            deps = self._dependencies.get(name, [])
            for dep in deps:
                if dep not in initialized:
                    init_service(dep)
                    
            # Initialize the service
            logger.debug(f"Initializing service: {name}")
            service = self._services[name]
            service.init_app(app)
            initialized.add(name)
            logger.info(f"Service initialized: {name}")
            
        # Initialize all services
        for name in list(self._services.keys()):
            try:
                init_service(name)
            except Exception as e:
                logger.error(f"Failed to initialize service {name}: {str(e)}")
                
        self._initialized = True
        logger.info(f"Service initialization complete. Initialized {len(initialized)} services.")
        
    def get_service(self, name):
        """
        Get a service by name
        
        Args:
            name: Name of the service to retrieve
            
        Returns:
            Service instance or None if not found
        """
        return self._services.get(name)
        
    def health_check(self):
        """
        Check the health of all services
        
        Returns:
            dict: Health status of all services
        """
        results = {}
        for name, service in self._services.items():
            try:
                status = service.health_check()
                results[name] = status
            except Exception as e:
                results[name] = {"status": "error", "message": str(e)}
                
        return results

# Create singleton instance
service_registry = ServiceRegistry()