"""
Input Validation Utilities
-------------------------
Centralized validation functions for user input data.
These functions ensure that all inputs are properly validated and sanitized
before being processed by the application.
"""

import re
import logging
from email_validator import validate_email, EmailNotValidError

# Initialize logging
logger = logging.getLogger(__name__)

# Validation regular expressions
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
USERNAME_REGEX = r'^[a-zA-Z0-9_-]{3,30}$'
ALPHA_REGEX = r'^[a-zA-Z]+$'
ALPHANUMERIC_REGEX = r'^[a-zA-Z0-9]+$'
NUMERIC_REGEX = r'^[0-9]+$'
UUID_REGEX = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
DATE_REGEX = r'^\d{4}-\d{2}-\d{2}$'
DATETIME_REGEX = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(.\d{1,6})?(Z|[+-]\d{2}:\d{2})?$'

# Security constants
PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 30
STRING_MAX_LENGTH = 255
TEXT_MAX_LENGTH = 65535  # 64KB of text


def is_valid_email(email):
    """
    Validate email format and check that it's properly formed.
    Uses both regex and the email_validator library for thorough validation.
    
    Args:
        email: The email to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not email or not isinstance(email, str):
        return False, "Email is required and must be a string"
        
    if len(email) > STRING_MAX_LENGTH:
        return False, f"Email exceeds maximum length of {STRING_MAX_LENGTH} characters"
        
    # First check with regex for basic format
    if not re.match(EMAIL_REGEX, email):
        return False, "Email format is invalid"
        
    # Then use email_validator for more thorough validation
    try:
        # Validate and get normalized form of email
        valid = validate_email(email)
        # Replace with normalized form
        email = valid.email
        return True, None
    except EmailNotValidError as e:
        return False, str(e)


def is_valid_password(password):
    """
    Validate password strength using multiple criteria.
    
    Args:
        password: The password to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not password or not isinstance(password, str):
        return False, "Password is required and must be a string"
        
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters long"
        
    if len(password) > PASSWORD_MAX_LENGTH:
        return False, f"Password exceeds maximum length of {PASSWORD_MAX_LENGTH} characters"
        
    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
        
    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
        
    # Check for at least one digit
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one digit"
        
    # Check for at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
        
    return True, None


def is_valid_username(username):
    """
    Validate username format.
    
    Args:
        username: The username to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not username or not isinstance(username, str):
        return False, "Username is required and must be a string"
        
    if len(username) < USERNAME_MIN_LENGTH:
        return False, f"Username must be at least {USERNAME_MIN_LENGTH} characters long"
        
    if len(username) > USERNAME_MAX_LENGTH:
        return False, f"Username exceeds maximum length of {USERNAME_MAX_LENGTH} characters"
        
    if not re.match(USERNAME_REGEX, username):
        return False, "Username must contain only letters, numbers, underscores, and hyphens"
        
    return True, None


def is_valid_text(text, field_name="Text", max_length=TEXT_MAX_LENGTH, required=True):
    """
    Validate a text field.
    
    Args:
        text: The text to validate
        field_name: Name of the field for error message
        max_length: Maximum allowed length
        required: Whether the field is required
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not text:
        if required:
            return False, f"{field_name} is required"
        else:
            return True, None
            
    if not isinstance(text, str):
        return False, f"{field_name} must be a string"
        
    if len(text) > max_length:
        return False, f"{field_name} exceeds maximum length of {max_length} characters"
        
    return True, None


def is_valid_string(string, field_name="Field", max_length=STRING_MAX_LENGTH, required=True, pattern=None, pattern_desc=None):
    """
    Validate a string field with an optional regex pattern.
    
    Args:
        string: The string to validate
        field_name: Name of the field for error message
        max_length: Maximum allowed length
        required: Whether the field is required
        pattern: Optional regex pattern to match
        pattern_desc: Description of the pattern for error message
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not string:
        if required:
            return False, f"{field_name} is required"
        else:
            return True, None
            
    if not isinstance(string, str):
        return False, f"{field_name} must be a string"
        
    if len(string) > max_length:
        return False, f"{field_name} exceeds maximum length of {max_length} characters"
        
    if pattern and not re.match(pattern, string):
        msg = f"{field_name} format is invalid"
        if pattern_desc:
            msg += f". {pattern_desc}"
        return False, msg
        
    return True, None


def is_valid_uuid(uuid_str):
    """
    Validate a UUID string.
    
    Args:
        uuid_str: The UUID string to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    valid, error = is_valid_string(uuid_str, field_name="UUID", pattern=UUID_REGEX)
    if not valid:
        return valid, error
    
    return True, None


def is_valid_date(date_str):
    """
    Validate a date string in YYYY-MM-DD format.
    
    Args:
        date_str: The date string to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    valid, error = is_valid_string(date_str, field_name="Date", pattern=DATE_REGEX)
    if not valid:
        return valid, error
    
    # Additional validation could be done here (e.g., checking that month is 1-12, etc.)
    return True, None


def is_valid_datetime(datetime_str):
    """
    Validate a datetime string in ISO 8601 format.
    
    Args:
        datetime_str: The datetime string to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    valid, error = is_valid_string(datetime_str, field_name="Datetime", pattern=DATETIME_REGEX)
    if not valid:
        return valid, error
    
    # Additional validation could be done here
    return True, None


def validate_data(data, validation_rules):
    """
    Validate a dictionary of data using validation rules.
    
    Args:
        data: Dictionary of data to validate
        validation_rules: Dictionary mapping field names to validation functions
        
    Returns:
        tuple: (is_valid, errors_dict)
    """
    if not data or not isinstance(data, dict):
        return False, {"error": "Invalid data format"}
        
    errors = {}
    
    for field, validator in validation_rules.items():
        value = data.get(field)
        is_valid, error = validator(value)
        
        if not is_valid:
            errors[field] = error
            
    return len(errors) == 0, errors


def sanitize_string(string, allow_html=False):
    """
    Sanitize a string by escaping HTML characters.
    
    Args:
        string: The string to sanitize
        allow_html: Whether to allow HTML tags
        
    Returns:
        Sanitized string
    """
    if not string or not isinstance(string, str):
        return string
        
    if not allow_html:
        # Replace HTML special characters with their entities
        string = string.replace('&', '&amp;')
        string = string.replace('<', '&lt;')
        string = string.replace('>', '&gt;')
        string = string.replace('"', '&quot;')
        string = string.replace("'", '&#x27;')
        
    return string