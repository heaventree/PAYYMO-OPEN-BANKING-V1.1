"""
Security Routes
--------------
Routes for security management and monitoring.
These routes are only accessible to super admins.
"""

import logging
import datetime
from flask import Blueprint, jsonify, g, request, current_app
from flask_backend.services.secrets_service import secrets_service
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
    # Check if we have a key rotation manager
    if not hasattr(secrets_service, 'has_rotation_manager') or not secrets_service.has_rotation_manager:
        return jsonify({
            'success': False,
            'message': 'Key rotation manager not available',
            'has_rotation_manager': False
        })
        
    # Get rotation schedule
    try:
        rotation_schedule = secrets_service.key_rotation_manager.get_rotation_schedule()
        
        # Get summary info
        rotation_summary = {
            'total_keys': len(rotation_schedule),
            'keys_due_for_rotation': sum(1 for key in rotation_schedule if key.get('rotation_due', False)),
            'next_rotation_due': min([key.get('days_until_rotation', 999) for key in rotation_schedule 
                                      if key.get('days_until_rotation') is not None], default=None)
        }
        
        return jsonify({
            'success': True,
            'has_rotation_manager': True,
            'rotation_summary': rotation_summary,
            'rotation_schedule': rotation_schedule
        })
    except Exception as e:
        logger.error(f"Error getting key rotation status: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error getting key rotation status: {str(e)}",
            'has_rotation_manager': True
        }), 500

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
    if not secrets_service.get_secret(key_name):
        return jsonify({
            'success': False,
            'message': f'Key {key_name} not found'
        }), 404
        
    # Rotate the key
    try:
        new_key = secrets_service.rotate_secret(key_name)
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
        # Check if we have a key rotation manager
        if hasattr(secrets_service, 'has_rotation_manager') and secrets_service.has_rotation_manager:
            keys = []
            
            # Get rotation info for each key
            for key_name in secrets_service._secrets_cache:
                if secrets_service.key_rotation_manager.has_key(key_name):
                    key_info = secrets_service.key_rotation_manager.get_key_info(key_name)
                    keys.append(key_info)
                else:
                    keys.append({
                        'name': key_name,
                        'managed': False,
                        'rotation_status': 'Not managed by rotation service'
                    })
                    
            return jsonify({
                'success': True,
                'keys': keys,
                'has_rotation_manager': True
            })
        else:
            # Without rotation manager, just list the key names
            keys = [{'name': name, 'managed': False} for name in secrets_service._secrets_cache]
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