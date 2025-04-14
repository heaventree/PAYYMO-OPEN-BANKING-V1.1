# __Error Handling & Debugging \(Updated\)__

## __Structured Logging__

- __Library:__ Pino or Winston for Node\.js backend; a simple console wrapper formatting to JSON for frontend\.
- __Format:__ JSON logs including timestamp, level \(info, warn, error\), message, and relevant context\.
- __Levels:__
	- error: Unrecoverable errors, crashes, failed API requests\.
	- warn: Recoverable issues, potential problems, unexpected states, non\-critical API failures \(e\.g\., retries\)\.
	- info: Key application events \(startup, config loaded, user login, resource creation\)\.
	- debug: Detailed diagnostic information \(only in dev/staging\)\.
- __Context Fields \(Examples\):__
	- __requestId__: \(See Error Correlation\) Unique ID for tracing a request across services\.
	- __userId__: ID of the logged\-in user \(if available\)\.
	- __sessionId__: Session identifier\.
	- __component__: Frontend component name where the log originated\.
	- __service__: Backend service name\.
	- __operation__: Specific function or action being performed \(e\.g\., loginUser, fetchForms\)\.
	- __path__: API endpoint path or frontend route\.
	- __method__: HTTP method \(for API requests\)\.
	- __statusCode__: HTTP status code \(for API responses\)\.
	- __durationMs__: Duration of an operation \(e\.g\., API request\)\.
	- __errorCode__: Application\-specific error code \(if applicable\)\.
	- __stackTrace__: \(For error level\) Stack trace of the error\.
- __Logging Patterns \(New Section\):__
	- __API Request Start \(Backend \- info\):__ Log incoming request details \(method, path, requestId, userId\)\.  
\{ "level": "info", "timestamp": "\.\.\.", "message": "API Request Start", "method": "POST", "path": "/api/v1/forms", "requestId": "xyz789", "userId": "user123" \}  

	- __API Request End \(Backend \- info/error\):__ Log response details \(statusCode, durationMs, requestId\)\. Log errors with stack trace\.  
\{ "level": "info", "timestamp": "\.\.\.", "message": "API Request End", "method": "POST", "path": "/api/v1/forms", "statusCode": 201, "durationMs": 150, "requestId": "xyz789", "userId": "user123" \}  
\`\`\`json  
\{ "level": "error", "timestamp": "\.\.\.", "message": "API Request Failed", "method": "POST", "path": "/api/v1/forms", "statusCode": 500, "durationMs": 120, "requestId": "xyz789", "userId": "user123", "error": "Database connection failed", "stackTrace": "\.\.\." \}  

	- __Frontend Action \(Frontend \- info\):__ Log key user interactions or component actions\.  
\{ "level": "info", "timestamp": "\.\.\.", "message": "User submitted login form", "component": "LoginForm", "userId": null, "sessionId": "abc123" \}  

	- __Frontend API Call \(Frontend \- info/error\):__ Log initiation and completion/failure of API calls from the frontend, including requestId\.  
\{ "level": "info", "timestamp": "\.\.\.", "message": "Initiating API call to POST /api/v1/forms", "component": "FormBuilder", "requestId": "xyz789", "sessionId": "abc123" \}  
\`\`\`json  
\{ "level": "error", "timestamp": "\.\.\.", "message": "API call failed: POST /api/v1/forms", "component": "FormBuilder", "status": 500, "error": "Server error", "requestId": "xyz789", "sessionId": "abc123" \}  


## __Error Boundary System \(Frontend \- React\)__

- Use React Error Boundaries at key component levels \(e\.g\., around routes, major features\)\.
- Log errors to Sentry or similar service within componentDidCatch, including requestId if available in context/state\.
- Display a user\-friendly fallback UI instead of a crashed component\.

// Example Error Boundary \(Conceptual logging enhancement\)  
// \.\.\. \(Previous Error Boundary Code\) \.\.\.  
  
  public componentDidCatch\(error: Error, errorInfo: ErrorInfo\) \{  
    console\.error\("Uncaught error:", error, errorInfo\);  
    const context = this\.getContext\(\); // Hypothetical function to get context like requestId  
    // logErrorToService\(error, \{ \.\.\.errorInfo, \.\.\.context \}\); // Send enriched data  
  \}  
  
// \.\.\. \(Rest of Error Boundary Code\) \.\.\.  


## __Recovery UI__

- Provide clear error messages to users \(avoid technical jargon\)\.
- Offer actionable steps \(e\.g\., "Try again," "Contact support," "Go to dashboard"\)\.
- Include a unique error ID \(correlationId or errorInstanceId shown to user\) that can be mapped back to logs \(e\.g\., the requestId\)\.

## __Snapshot System \(AI Debugger\)__

- Before applying AI\-suggested code changes, create a snapshot \(diff or copy\) of the original code\.
- Allow users to easily revert to the previous state if the AI change introduces errors\.
- Log the AI suggestion, the diff, and the user's decision \(accept/reject\)\.

## __Error Correlation \(New Section\)__

- __Goal:__ Trace a single user interaction or request across frontend, backend, and potentially other services\.
- __Mechanism:__ Use a unique __Request ID__ \(also known as Correlation ID or Trace ID\)\.
	- __Generation:__
		- Generate a unique ID \(e\.g\., UUID\) on the frontend when an operation \(like an API call\) starts\.
		- OR, generate it at the edge \(CDN, load balancer\) and pass it as a request header \(e\.g\., X\-Request\-ID\)\.
	- __Propagation:__
		- __Frontend:__ Include the requestId in all log messages related to that operation\. Send the requestId as a custom header \(e\.g\., X\-Request\-ID\) in API calls\.
		- __Backend:__ Read the X\-Request\-ID header from incoming requests\. Include this requestId in all log messages generated while processing that request\. If the backend makes calls to other internal services, propagate the requestId header to those calls as well\.
- __Benefits:__ Allows filtering logs in a centralized logging system \(e\.g\., Datadog, Logtail\) by requestId to see the complete flow of an operation across the entire stack, making debugging distributed issues much easier\.

## __Debug Tools__

- __Frontend:__ React DevTools, Redux DevTools \(if applicable\), Browser DevTools \(Console, Network, Performance tabs\)\.
- __Backend:__ Node\.js Inspector, console\.trace\(\), debugger statements\.
- __Environment:__ Consistent use of \.env files for configuration\.

## __Monitoring & Alerting__

- __Service:__ Sentry, Datadog, or similar for real\-time error tracking and performance monitoring\.
- __Alerting:__ Configure alerts for critical error spikes \(using logged error levels/codes\) or performance degradation\. Use requestId in alerts where possible\.

## __Known Error Registry__

- Maintain a simple registry \(e\.g\., a shared document or knowledge base\) of known, non\-critical errors and their workarounds\.
- Link error IDs from user\-facing messages \(or correlationId\) to this registry where appropriate\.

