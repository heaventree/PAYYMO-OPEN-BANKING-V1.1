# __Authentication & Security \(Expanded\)__

__Core Principle:__ Implement security at every layer \(defense\-in\-depth\)\. Assume breaches can happen and design systems to limit blast radius and ensure detectability\. Regularly review and update security practices based on evolving threats \(e\.g\., OWASP Top 10\)\.

## __1\. Authentication Providers & User Credentials__

- __Primary:__ Passwordless \(email magic link\) or social logins \(Google, GitHub\) via Supabase Auth or Auth0 are preferred to reduce password\-related risks\.
- __Password Strategy:__
	- If passwords *must* be used:
		- Enforce strong complexity requirements \(length, character types\) via client\-side and server\-side validation\.
		- Use a strong, adaptive hashing algorithm like __Argon2id__ \(preferred\) or bcrypt with a high work factor\. Store only the hash\.
		- Implement protection against credential stuffing \(e\.g\., rate limiting, CAPTCHAs after multiple failures, breached password detection using services like Have I Been Pwned\)\.
- __Multi\-Factor Authentication \(MFA\):__
	- __Offer:__ Strongly recommend offering TOTP \(e\.g\., Google Authenticator, Authy\) as an MFA option for all users, especially admins\.
	- __Enrollment:__ Secure enrollment process \(e\.g\., verify password again before enabling MFA\)\. Provide QR code and manual setup key\.
	- __Recovery Codes:__ Provide users with one\-time recovery codes upon MFA setup and advise secure storage\. Implement a secure process for account recovery if MFA device/codes are lost\.

## __2\. Roles and Permissions \(RBAC \- Principle of Least Privilege\)__

- __Define Roles:__ Clearly define granular roles \(admin, editor, billing\_manager, viewer, etc\.\) based on the principle of least privilege\.
- __Assign Permissions:__ Associate specific, fine\-grained permissions \(read:user, update:user:profile, delete:form, manage:billing\) with each role\. Avoid overly broad permissions\.
- __Implementation:__
	- Store user roles/permissions reliably \(database\)\.
	- __Backend Enforcement:__ Use middleware for coarse\-grained checks \(e\.g\., is user authenticated? is user an admin?\)\. __Crucially, perform fine\-grained permission checks within the service layer or endpoint logic__ before executing sensitive operations \(e\.g\., if \(\!userHasPermission\(currentUser, 'delete:form', targetForm\)\) throw new ForbiddenError\(\);\)\. Don't rely solely on frontend UI hiding elements\.
	- __Frontend:__ Conditionally render UI elements based on roles/permissions fetched from the backend, but treat this as UX enhancement, not a security measure\.

## __3\. Token Handling \(JWT\) & Session Management__

- __JWT Signing Algorithm:__ Use asymmetric algorithms \(e\.g\., RS256\) where the backend holds the private key for signing and the public key can be shared for verification\. Avoid HS256 if the secret key might be compromised elsewhere\.
- __Access Tokens \(Short\-Lived\):__
	- Issue JWTs with short expiry times \(e\.g\., 5\-15 minutes\)\.
	- Payload should include user ID, roles/permissions \(or reference to fetch them\), and expiration \(exp\)\. Avoid including sensitive data\.
	- Store in memory \(e\.g\., Zustand store\) on the client\. __Never store in localStorage or sessionStorage__ due to XSS risks\.
- __Refresh Tokens \(Longer\-Lived & Secure\):__
	- Issue opaque \(non\-JWT\), long\-lived refresh tokens \(e\.g\., hours, days, weeks depending on security requirements\)\.
	- __Storage:__ Store refresh tokens securely using __HTTP\-only, Secure, SameSite=Strict \(or Lax\)__ cookies\. This prevents access via JavaScript \(XSS\)\.
	- __Rotation:__ Implement refresh token rotation\. When a refresh token is used, issue a *new* refresh token along with the new access token, and invalidate the used refresh token immediately or after a short grace period\.
	- __Theft Detection:__ If a previously used \(or invalidated\) refresh token is presented, assume potential theft, invalidate the entire token family for that user, and force re\-authentication\. Log this event\.
- __Validation \(Backend\):__
	- Verify JWT signature using the correct public key \(for RS256\) or secret \(for HS256\)\.
	- Check exp claim for expiration\.
	- Check nbf \(Not Before\) and iat \(Issued At\) claims if used\.
	- Verify iss \(Issuer\) and aud \(Audience\) claims if used\.
	- Check against a token revocation list if implementing immediate logout features beyond just expiry\.

## __4\. Input Validation \(Defense against Injection\)__

- __Principle:__ __Never trust user input\.__ Validate and sanitize input rigorously on the __backend__, even if validation exists on the frontend\.
- __Backend Validation:__ Use schema validation libraries \(like Zod\) integrated with your framework \(e\.g\., fastify\-type\-provider\-zod\) to validate *all* incoming data: request bodies, query parameters, path parameters, headers\. Check types, formats, lengths, ranges, and allowed values\.
- __Sanitization:__ Sanitize output data appropriately based on context \(e\.g\., use React's automatic JSX encoding for HTML, use parameterized queries/ORM for SQL\)\. Avoid manually constructing queries or HTML with raw user input\.
- __Specific Protections:__ Guard against SQL Injection \(use ORMs like Prisma\), NoSQL Injection, Command Injection, XSS \(validate input, sanitize output, use CSP\)\.

## __5\. API Security Best Practices__

- __Authorization:__ Re\-verify permissions within API endpoint logic for sensitive operations \(see RBAC section\)\. Ensure users can only access/modify resources they own or have explicit permission for\.
- __Prevent Mass Assignment:__ When updating database records based on request bodies, explicitly map allowed fields\. Do not blindly pass the entire request body to database update functions \(e\.g\., use select or DTOs\)\.
- __Secure Defaults:__ Design APIs with secure defaults \(e\.g\., resources are private unless explicitly made public\)\.
- __Resource IDs:__ Use non\-sequential, unpredictable IDs \(e\.g\., UUIDs\) for resources exposed externally to prevent enumeration attacks\.

## __6\. Security Headers \(Hardening HTTP Responses\)__

- Implement these headers via backend middleware or edge configuration \(Cloudflare\):
	- __Strict\-Transport\-Security__ \(HSTS\): Strict\-Transport\-Security: max\-age=31536000; includeSubDomains; preload \- Forces browsers to use HTTPS\. Submit to preload list\.
	- __X\-Frame\-Options__: X\-Frame\-Options: DENY \(or SAMEORIGIN\) \- Prevents clickjacking attacks by controlling embedding in iframes\.
	- __X\-Content\-Type\-Options__: X\-Content\-Type\-Options: nosniff \- Prevents browsers from MIME\-sniffing responses away from the declared Content\-Type\.
	- __Content\-Security\-Policy__ \(CSP\): \(See below\)
	- __Referrer\-Policy__: Referrer\-Policy: strict\-origin\-when\-cross\-origin \(or no\-referrer\) \- Controls how much referrer information is sent\.
	- __Permissions\-Policy__: Permissions\-Policy: geolocation=\(\), microphone=\(\), camera=\(\) \- Restricts browser feature access \(specify only needed features\)\.

## __7\. Content Security Policy \(CSP\) \- Expanded__

- __Goal:__ Mitigate XSS and some data injection attacks\. Define allowed sources for various content types\.
- __Strategy:__ Start restrictive \(default\-src 'self'\) and explicitly allow necessary origins\. Use nonces or hashes for inline scripts/styles if absolutely unavoidable \(prefer external files\)\.
- __Key Directives:__
	- default\-src 'self' trusted\.cdn\.com;: Default policy for most types\.
	- script\-src 'self' 'nonce\-RANDOM\_NONCE' https://apis\.google\.com;: Allow scripts from self, specific nonces, and Google APIs\.
	- style\-src 'self' 'unsafe\-inline' https://fonts\.googleapis\.com;: Allow styles from self, inline styles \(use hashes/nonces if possible instead\), and Google Fonts\.
	- img\-src 'self' data: https://images\.example\.com;: Allow images from self, data URIs, and a specific domain\.
	- connect\-src 'self' https://api\.example\.com;: Control origins for fetch, XHR, WebSockets\.
	- frame\-ancestors 'none';: Similar to X\-Frame\-Options: DENY\.
	- form\-action 'self';: Restrict where forms can submit to\.
	- report\-uri /csp\-report\-endpoint; \(Deprecated\) or report\-to csp\-endpoint;: Send violation reports to an endpoint for monitoring\.
- __Implementation:__ Use libraries like helmet \(Express\) or fastify\-helmet \(Fastify\) or configure at the edge \(Cloudflare\)\.

## __8\. CSRF Protection \(Cross\-Site Request Forgery\)__

- __Threat:__ Attacker tricks a logged\-in user's browser into making an unintended state\-changing request to the application\.
- __Mitigation:__
	- __Primary:__ Use SameSite=Strict \(preferred\) or SameSite=Lax on session/authentication cookies\. This prevents the browser from sending the cookie with cross\-site requests initiated by third\-party sites\. Strict is more secure but can affect linking into the site\.
	- __Secondary \(Defense\-in\-Depth\):__ Implement the Synchronizer Token Pattern \(Anti\-CSRF Tokens\)\. Generate a unique, unpredictable token associated with the user's session\. Embed this token in forms as a hidden field\. Require this token to be sent back \(e\.g\., in the request body or a custom header like X\-CSRF\-Token\) for all state\-changing requests \(POST, PUT, PATCH, DELETE\)\. Validate the token on the backend\. Libraries like csurf \(Express\) can help\.
	- __Check Origin/Referer:__ Can be used as an additional check but can sometimes be unreliable or spoofed\.

## __9\. Dependency Security__

- __Regular Scans:__ Use npm audit or pnpm audit regularly to check for known vulnerabilities in project dependencies\.
- __Automated Tools:__ Integrate automated scanning tools like GitHub Dependabot or Snyk into the repository and CI/CD pipeline\. Configure automated alerts and/or PRs for vulnerable dependencies\.
- __Update Strategy:__ Keep dependencies reasonably up\-to\-date, prioritizing security patches\. Test thoroughly after updates\.

## __10\. Secrets Management__

- __Never Hardcode Secrets:__ Do not commit API keys, database credentials, JWT secrets, encryption keys, etc\., directly into source code\.
- __Environment Variables:__ Use environment variables \(\.env locally, platform\-provided vars in staging/prod\) as a baseline\.
- __Dedicated Services \(Recommended\):__ For better security, auditing, and rotation capabilities, use dedicated secrets management services like AWS Secrets Manager, Google Secret Manager, HashiCorp Vault, or Doppler\. Application instances fetch secrets from these services at runtime\.

## __11\. Security Logging & Monitoring__

- __Log Security Events:__ Explicitly log security\-relevant events:
	- Successful/failed logins\.
	- Password reset requests/completions\.
	- MFA enrollment/verification/failures\.
	- Permission failures \(authorization denied\)\.
	- Significant security setting changes \(e\.g\., MFA disable\)\.
	- Detected rate limiting events\.
	- CSP violations \(via report\-uri/report\-to\)\.
- __Alerting:__ Configure alerts in your monitoring system \(Sentry, Datadog, etc\.\) for suspicious patterns \(e\.g\., high rate of failed logins, multiple permission failures from one user, critical security errors\)\.
- __Correlation:__ Use requestId to correlate security events across frontend and backend logs \(See 09\_Error\_Handling\_Debugging\.md\)\.

## __12\. Regular Security Audits__

- __Internal Reviews:__ Conduct regular internal code reviews focusing specifically on security aspects\. Use security checklists \(e\.g\., OWASP ASVS\)\.
- __External Penetration Testing:__ Consider periodic penetration testing by external security experts, especially before major launches or for applications handling highly sensitive data\.

## __13\. AI Agent Security Considerations__

- __Secure Prompts:__ When prompting AI to generate code, explicitly include security requirements \(e\.g\., "Generate a SQL query using parameterized inputs to prevent SQL injection," "Ensure proper authorization checks are included"\)\.
- __Review AI Code:__ __Critically review all code generated by AI agents for potential security vulnerabilities\.__ Treat it like code from a junior developer needing a thorough review\. Pay attention to input validation, authorization checks, and secure handling of secrets or data\.
- __Limit AI Capabilities:__ Restrict AI agents' ability to directly modify critical security configurations, authentication mechanisms, or access/manage secrets\. These areas require human oversight\.
- __Training Data:__ Be aware of the potential for AI models to have been trained on insecure code examples\. Do not blindly trust AI output\.

