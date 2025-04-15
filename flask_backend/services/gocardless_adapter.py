"""
GoCardless Service Adapter

This module provides backward compatibility with the legacy GoCardless service interface,
allowing existing code to continue working while migrating to the new consolidated service.
"""
import logging
from flask_backend.services.core_banking_service import core_banking_service

# Logger
logger = logging.getLogger(__name__)

class GoCardlessServiceAdapter:
    """
    Adapter for backwards compatibility with old GoCardless service interfaces
    
    This adapter forwards calls to the new consolidated CoreBankingService while
    maintaining the same interface as the original GoCardlessService.
    """
    
    def __init__(self, core_service):
        """
        Initialize the adapter with the core banking service
        
        Args:
            core_service: CoreBankingService instance to use
        """
        self._core_service = core_service
        logger.info("GoCardless service adapter initialized")
    
    @property
    def client_id(self):
        """Legacy client_id property"""
        return self._core_service._client_id
    
    @property
    def client_secret(self):
        """Legacy client_secret property"""
        return self._core_service._client_secret
    
    @property
    def sandbox_mode(self):
        """Legacy sandbox_mode property"""
        return self._core_service._sandbox_mode
    
    @property
    def api_base_url(self):
        """Legacy api_base_url property"""
        return self._core_service._api_base_url
    
    @property
    def api_version(self):
        """Legacy api_version property"""
        return self._core_service._api_version
    
    @property
    def banks_endpoint(self):
        """Legacy banks_endpoint property"""
        return self._core_service._banks_endpoint
    
    @property
    def auth_url(self):
        """Legacy auth_url property"""
        return self._core_service._auth_url
    
    @property
    def token_url(self):
        """Legacy token_url property"""
        return self._core_service._token_url
    
    def get_available_banks(self, country=None, limit=50):
        """
        Adapter for legacy get_available_banks method
        
        Args:
            country: Country code (ISO 3166-1 alpha-2)
            limit: Maximum number of banks to return
            
        Returns:
            list: List of bank information dictionaries
        """
        return self._core_service.get_banks(country, limit)
    
    def create_bank_authorization_link(self, tenant_id, bank_id, redirect_uri, state=None):
        """
        Adapter for legacy create_bank_authorization_link method
        
        Args:
            tenant_id: ID of the tenant (WHMCS instance)
            bank_id: ID of the bank to connect to
            redirect_uri: URL to redirect to after authorization
            state: Optional state for CSRF protection
            
        Returns:
            dict: Bank link information with url and other details
        """
        return self._core_service.create_bank_link(tenant_id, bank_id, redirect_uri, state)
    
    def process_bank_authorization_callback(self, tenant_id, bank_id, code, redirect_uri):
        """
        Adapter for legacy process_bank_authorization_callback method
        
        Args:
            tenant_id: ID of the tenant (WHMCS instance)
            bank_id: ID of the bank to connect to
            code: Authorization code from redirect
            redirect_uri: Redirect URI used in authorization
            
        Returns:
            dict: Connection information with access token and other details
        """
        return self._core_service.complete_bank_connection(tenant_id, bank_id, code, redirect_uri)
    
    def refresh_access_token(self, connection_id):
        """
        Adapter for legacy refresh_access_token method
        
        Args:
            connection_id: ID of the bank connection to refresh
            
        Returns:
            dict: Updated connection information
        """
        return self._core_service.refresh_bank_connection(connection_id)
    
    def get_bank_transactions(self, connection_id, date_from=None, date_to=None):
        """
        Adapter for legacy get_bank_transactions method
        
        Args:
            connection_id: ID of the bank connection
            date_from: Optional start date (ISO format)
            date_to: Optional end date (ISO format)
            
        Returns:
            list: List of transaction dictionaries
        """
        return self._core_service.get_transactions(connection_id, date_from, date_to)
    
    def validate_webhook_certificate(self, cert_data):
        """
        Adapter for legacy validate_webhook_certificate method
        
        Args:
            cert_data: Certificate data from webhook
            
        Returns:
            bool: True if certificate is valid, False otherwise
        """
        return self._core_service.verify_webhook_certificate(cert_data)
    
    def handle_webhook_event(self, event_type, payload):
        """
        Adapter for legacy handle_webhook_event method
        
        Args:
            event_type: Type of webhook event
            payload: Webhook event payload
            
        Returns:
            dict: Processing result
        """
        return self._core_service.process_webhook(event_type, payload)
    
    def list_bank_connections(self, tenant_id):
        """
        Adapter for legacy list_bank_connections method
        
        Args:
            tenant_id: ID of the tenant (WHMCS instance)
            
        Returns:
            list: List of bank connection dictionaries
        """
        return self._core_service.get_bank_connections(tenant_id)
    
    def disconnect_bank(self, connection_id):
        """
        Adapter for legacy disconnect_bank method
        
        Args:
            connection_id: ID of the bank connection to revoke
            
        Returns:
            dict: Result of the revocation
        """
        return self._core_service.revoke_bank_connection(connection_id)

# Create adapter instance using the CoreBankingService singleton
gocardless_service = GoCardlessServiceAdapter(core_banking_service)