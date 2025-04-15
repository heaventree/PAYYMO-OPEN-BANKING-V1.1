"""
Security Routes
--------------
Routes for security management and monitoring.
These routes are only accessible to super admins.
"""

import logging
import datetime
from flask import Blueprint, jsonify, g, request, current_app
from flask_backend.services.vault_service import vault_service
from flask_backend.services.auth_service import auth_service

# Logger
logger = logging.getLogger(__name__)

# Create blueprint
security_bp = Blueprint('security', __name__, url_prefix='/api/security')

@security_bp.before_request
def check_admin():
    """Check if the user is a super admin"""
    if not g.is_super_admin:
        logger.warning("Unauthorized access attempt to security routes")
        return jsonify({
            'success': False,
            'message': 'Unauthorized'
        }), 403

@security_bp.route('/key-rotation-status', methods=['GET'])
def key_rotation_status():
    """Get key rotation status"""
    # Check if we have a key rotation manager (vault service doesn't have rotation yet)
    return jsonify({
        'success': True,
        'message': 'Using vault service for secret management',
        'has_rotation_manager': False,
        'rotation_summary': {
            'total_keys': len(vault_service.CRITICAL_SECRETS),
            'keys_due_for_rotation': 0,
            'next_rotation_due': None
        }
    })

@security_bp.route('/rotate-key/<key_name>', methods=['POST'])
def rotate_key(key_name):
    """Rotate a specific key"""
    # Validate key name
    if not key_name:
        return jsonify({
            'success': False,
            'message': 'Key name is required'
        }), 400
        
    # Check if the key exists
    if not vault_service.get_secret(key_name):
        return jsonify({
            'success': False,
            'message': f'Key {key_name} not found'
        }), 404
        
    # Rotate the key
    try:
        new_key = vault_service.rotate_secret(key_name)
        if new_key:
            # Redact the actual key value for security
            return jsonify({
                'success': True,
                'message': f'Key {key_name} rotated successfully',
                'key_info': {
                    'name': key_name,
                    'rotated_at': datetime.datetime.utcnow().isoformat()
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Failed to rotate key {key_name}'
            }), 500
    except Exception as e:
        logger.error(f"Error rotating key {key_name}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error rotating key {key_name}: {str(e)}"
        }), 500

@security_bp.route('/keys', methods=['GET'])
def list_keys():
    """List all managed keys"""
    # Get list of all secrets
    try:
        # List critical secrets from vault service
        keys = []
        
        # Add critical secrets first
        for key_name, description in vault_service.CRITICAL_SECRETS.items():
            keys.append({
                'name': key_name,
                'managed': True,
                'critical': True,
                'description': description,
                'has_value': vault_service.get_secret(key_name) is not None
            })
        
        # Additional keys that might be in the cache
        if hasattr(vault_service, '_secrets_cache'):
            for key_name in vault_service._secrets_cache:
                # Skip if already added as critical
                if key_name in vault_service.CRITICAL_SECRETS:
                    continue
                    
                keys.append({
                    'name': key_name,
                    'managed': True,
                    'critical': False,
                    'has_value': True
                })
        
        return jsonify({
            'success': True,
            'keys': keys,
            'has_rotation_manager': False
        })
            
    except Exception as e:
        logger.error(f"Error listing keys: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error listing keys: {str(e)}"
        }), 500

# Register blueprint with app
def register_security_routes(app):
    """Register security routes with the app"""
    app.register_blueprint(security_bp)
    logger.info("Security routes registered")