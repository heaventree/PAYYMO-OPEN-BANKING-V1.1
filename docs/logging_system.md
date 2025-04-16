# Logging System Documentation

## Overview
The logging system provides comprehensive tracking of application activities, requests, and errors across the WHMCS-PAYYMO-OPEN-BANKING integration. It's designed to provide consistent formatting, appropriate detail levels, and context-aware error tracking.

## Key Components

### 1. Logger Utilities (`flask_backend/utils/logger.py`)
- Standardized logger creation and configuration
- Request and response logging
- Context-aware error logging with sensitive data redaction
- Flask application integration

### 2. Error Handler (`flask_backend/utils/error_handler.py`)
- Standardized error response generation
- Error categorization and handling
- Integration with logging system for error tracking

### 3. Request Context Middleware
- Request tracking with timing information
- Request context maintenance
- Performance monitoring

## Using the Logging System

### Getting a Logger

To get a properly configured logger:

```python
from flask_backend.utils.logger import get_logger

# Get a logger with default configuration
logger = get_logger('module.name')

# Get a logger with custom levels
logger = get_logger(
    'module.name',
    console_level=logging.DEBUG,
    file_level=logging.INFO,
    log_file='path/to/log.log'
)
```

### Logging Different Message Types

```python
# Informational messages
logger.info("Operation completed successfully")

# Debug information
logger.debug("Detailed debug information: %s", data)

# Warnings
logger.warning("Potential issue detected: %s", warning)

# Errors
logger.error("Error occurred", exc_info=True)

# Critical errors
logger.critical("System failure", exc_info=True)
```

### Logging Errors with Context

```python
from flask_backend.utils.logger import log_error

try:
    # Some operation that might fail
    result = operation()
except Exception as e:
    # Log the error with context
    context = {
        'operation': 'operation_name',
        'input_params': {'id': 123, 'action': 'update'},
        'user_id': current_user.id if current_user else None,
        # Don't include passwords or tokens here - they'll be redacted,
        # but better not to include them at all
    }
    log_error(logger, e, context)
```

### Request Logging

The system automatically logs HTTP requests with the following information:
- HTTP method and path
- Status code
- Response time
- Request headers (with sensitive data redacted)
- Request arguments

Example log entry:
```
2025-04-15 23:03:20,433 - flask_backend.utils.logger - INFO - API Response: GET /api/gocardless/banks - Status: 200, Duration: 0ms
```

## Configuration

### Log Levels

The following log levels are used:

- **DEBUG**: Detailed information, typically useful only for diagnosing problems
- **INFO**: Confirmation that things are working as expected
- **WARNING**: Indication that something unexpected happened, or may happen in the future
- **ERROR**: Due to a more serious problem, the software has not been able to perform a function
- **CRITICAL**: A serious error, indicating that the program itself may be unable to continue running

### Default Configuration

- Console logging: INFO level and above
- File logging (when enabled): DEBUG level and above
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- Date format: `%Y-%m-%d %H:%M:%S`

### Environment Variable Configuration

The following environment variables can be used to configure logging:

- `LOG_LEVEL`: Sets the overall logging level (DEBUG, INFO, etc.)
- `LOG_FILE`: Path to the log file (if not set, file logging is disabled)
- `LOG_FILE_LEVEL`: Sets the logging level for file output
- `LOG_FORMAT`: Custom log format string

## Integration with Flask

The logging system integrates with Flask using the following components:

### Setup Logging

In your Flask application:

```python
from flask_backend.utils.logger import setup_logging

# In your app.py or equivalent
app = Flask(__name__)
# ... other configuration
setup_logging(app)
```

This will:
1. Configure the Flask app's logger
2. Set up request tracking middleware
3. Configure error logging

### Request Tracking

The system automatically adds the following before/after request handlers:

```python
@app.before_request
def before_request():
    # Store request start time
    g.start_time = time.time()

@app.after_request
def after_request(response):
    # Calculate request duration
    duration_ms = (time.time() - g.start_time) * 1000
    
    # Log the request
    log_request(logger, request, response, duration_ms)
    
    return response
```

### Error Handling

The system adds a global exception handler:

```python
@app.errorhandler(Exception)
def handle_exception(error):
    # Log the error with context
    context = {
        'url': request.url,
        'method': request.method,
        'user_id': g.user.id if hasattr(g, 'user') and g.user else None,
        'tenant_id': g.tenant_id if hasattr(g, 'tenant_id') else None
    }
    log_error(logger, error, context)
    
    # Pass through to the default error handler
    return app.handle_exception(error)
```

## Security Features

### Sensitive Data Redaction

The logging system automatically redacts sensitive information:

```python
# In log_error function:
if context:
    # Sanitize context data
    safe_context = {k: v for k, v in context.items()}
    for sensitive_key in ['password', 'token', 'secret', 'key', 'credential']:
        for k in list(safe_context.keys()):
            if sensitive_key in k.lower():
                safe_context[k] = '[REDACTED]'
```

This prevents accidental logging of passwords, API keys, tokens, etc.

### Request Header Sanitization

When logging request headers, the system redacts sensitive headers:

```python
if 'Authorization' in headers:
    headers['Authorization'] = '[REDACTED]'
if 'Cookie' in headers:
    headers['Cookie'] = '[REDACTED]'
```

## Best Practices

1. **Use Descriptive Logger Names**: Structure logger names by module/component (e.g., 'flask_backend.services.auth_service')

2. **Choose Appropriate Log Levels**:
   - DEBUG: Detailed diagnostic information
   - INFO: Confirmation of normal events
   - WARNING: Unexpected events that don't prevent operation
   - ERROR: Problems that prevent specific operations
   - CRITICAL: System-wide failures

3. **Include Context in Messages**: Provide enough context to understand log entries:
   ```python
   # Bad
   logger.info("User created")
   
   # Good
   logger.info("User created: id=%s email=%s", user.id, user.email)
   ```

4. **Structure Complex Data**: For complex objects, consider JSON formatting:
   ```python
   import json
   logger.debug("Configuration: %s", json.dumps(config, indent=2))
   ```

5. **Avoid Excessive Logging**: Be mindful of performance and log volume, especially in production

6. **Log Exceptions Properly**: Always include `exc_info=True` when logging exceptions:
   ```python
   try:
       # operation
   except Exception as e:
       logger.error("Failed to process request", exc_info=True)
   ```

7. **Never Log Sensitive Data**: Avoid logging passwords, tokens, personal data, etc.

## Troubleshooting

### Common Issues

1. **Missing Logs**
   - Check log level configuration
   - Ensure logger name is correct
   - Verify log file permissions

2. **Performance Issues**
   - Reduce log level in production
   - Avoid expensive logging operations
   - Use asynchronous logging for high-volume environments

3. **Disk Space Concerns**
   - Implement log rotation
   - Monitor log file sizes
   - Set appropriate retention policies

## Conclusion

The enhanced logging system provides comprehensive tracking of application activities with appropriate security measures and integration with the Flask framework. By following the best practices outlined here, you can ensure effective monitoring and troubleshooting of the WHMCS-PAYYMO-OPEN-BANKING integration.