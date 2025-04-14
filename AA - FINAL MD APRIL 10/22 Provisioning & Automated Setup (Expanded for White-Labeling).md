# __Provisioning & Automated Setup \(Expanded for White\-Labeling\)__

This document covers automated processes for user onboarding, system maintenance, and, critically, the design considerations and automated provisioning required for __white\-label SaaS instances__\.

## __1\. User Onboarding Workflow \(Tenant End\-Users & Initial Admin\)__

- __Trigger:__ Successful user signup and email verification \(or first login via SSO\)\. For white\-label instances, this workflow applies primarily to the *initial administrator* provisioned for that tenant\.
- __Steps:__
	1. Identify the correct tenant/workspace based on signup context \(e\.g\., subdomain, invitation code\)\.
	2. Create the user record linked to the specific tenant\_id\.
	3. Provision necessary database entries \(user profile, default settings *scoped to the tenant*\)\.
	4. Optionally trigger a welcome email sequence \(potentially using tenant\-specific email templates\)\.
	5. Redirect user to an onboarding tour or setup wizard relevant to their role and tenant configuration\.

## __2\. Designing and Provisioning for White\-Labeling \(New Major Section\)__

This section details the architectural considerations and automated processes required to support white\-label tenants effectively and securely\.

### __2\.1\. Defining White\-Label Scope__

- __Requirement:__ Before implementation, clearly define *what* aspects of the application are customizable by white\-label tenants \(based on Business Requirements \- Point 1\.2 from your list\)\. This typically includes:
	- Branding: Logo, favicon, application name\.
	- Theming: Color schemes, fonts, potentially custom CSS overrides\.
	- Domain: Using subdomains or custom domains\.
	- Features: Enabling/disabling specific modules or features via toggles\.
	- Email Templates: Customizing transactional emails\.
	- Legal/Compliance: Tenant\-specific terms of service or privacy policy links\.

### __2\.2\. Multi\-Tenancy & Data Isolation Strategy__

- __Requirement:__ Ensure strict data isolation between tenants\. The chosen strategy significantly impacts provisioning and security \(Points 1\.3, 2\.3\)\.
- __Implementation Options:__
	- __Row\-Level Security \(RLS\) with Shared DB:__ Simpler to manage initially\. Requires a tenant\_id column on all relevant tables and database policies enforcing data access based on the current user's tenant\_id\. Provisioning involves creating the tenant record and associating users\. Backups are typically for the entire shared database, but PITR allows restoring specific tenant data if needed \(complex\)\.
	- __Separate Schemas \(Shared DB\):__ One schema per tenant within the same database instance\. Offers stronger isolation than RLS\. Provisioning requires creating a new schema and applying the standard table structure\. Backup/restore can be done per schema\. More complex connection management\.
	- __Separate Databases \(Shared or Dedicated Instance\):__ Maximum isolation, potentially better performance scaling per tenant\. Provisioning involves creating an entirely new database for the tenant\. Backup/restore is straightforward per tenant\. Highest cost and management complexity\.
- __Decision:__ The chosen method __must__ be documented in PLANNING\.md or a dedicated architecture document\. Automation scripts \(Section 3\) must support the chosen strategy\.
- __Backup Strategy:__ Must align with the isolation model\. If using separate DBs, ensure each tenant DB is backed up regularly\. See 11\_Backup\_Recovery\_Safety\.md\.

### __2\.3\. Tenant Branding & Theming__

- __Requirement:__ Allow tenants to apply their branding \(Point 2\.3\)\.
- __Implementation:__
	- __Asset Storage:__ Store tenant\-specific logos, favicons, etc\., in secured object storage \(S3/Supabase Storage\), potentially organized by tenant\_id\.
	- __Configuration Storage:__ Store theme settings \(color codes, font choices, custom CSS snippets if allowed\) in the database, linked to the tenant\_id\.
	- __Application:__
		- __Runtime Loading:__ Application fetches tenant branding/theme config upon user login or based on domain, applying it dynamically \(e\.g\., setting CSS variables, loading specific assets\)\. Suitable for most changes\.
		- __Build Time:__ For deeper branding requiring different build outputs, the CI/CD pipeline might need steps to generate tenant\-specific builds \(more complex\)\. See 12\_DevOps\_Infrastructure\.md\.

### __2\.4\. Domain Management \(Subdomains & Custom Domains\)__

- __Requirement:__ Allow tenants to use their own domains \(Point 2\.3\)\.
- __Implementation:__
	- __Subdomains \(tenant\.yourapp\.com\):__ Configure wildcard DNS \(\*\.yourapp\.com\) pointing to your load balancer/application servers\. The application identifies the tenant from the subdomain in the request host header\. Automated SSL \(e\.g\., wildcard Let's Encrypt\) is needed\.
	- __Custom Domains \(app\.tenantdomain\.com\):__
		1. Tenant configures a CNAME record in their DNS pointing their desired domain to a specific endpoint you provide \(e\.g\., whitelabel\.yourapp\.com\)\.
		2. Your application/infrastructure needs to handle incoming requests for these custom domains\.
		3. Implement automated SSL certificate provisioning and renewal for custom domains \(e\.g\., using Let's Encrypt via Caddy, Traefik, or platform services like Vercel/Netlify/Cloudflare for SaaS\)\.
	- __Provisioning:__ Provide clear instructions and potentially a UI for tenants to configure their custom domains\. Backend scripts needed to manage domain mappings and trigger SSL generation\.

### __2\.5\. Feature Flagging & Tenant Configuration__

- __Requirement:__ Enable/disable features or modify settings per tenant \(Point 2\.3\)\.
- __Implementation:__
	- Use a database table storing tenant\-specific configurations \(e\.g\., tenant\_configurations with tenant\_id, config\_key, config\_value\)\.
	- Application logic checks these configurations when rendering UI or executing backend logic\.
	- Provide a UI for platform admins \(and potentially tenant admins, depending on scope\) to manage these flags/settings\.
	- Leverage the Default Config Generator \(Section 4\) for initial tenant setup\.

### __2\.6\. Secure Tenant Containers & Infrastructure__

- __Requirement:__ Ensure tenant isolation at the infrastructure level where appropriate \(Point 2\.3, 4\)\.
- __Implementation:__ Depending on the multi\-tenancy DB strategy and overall architecture:
	- __Shared Infrastructure \(Common\):__ Rely primarily on application\-level and database\-level \(RLS/Schema\) isolation\. Ensure sufficient resource allocation and monitoring to prevent noisy neighbors\.
	- __Containerization:__ Use Docker/Kubernetes for deployment consistency\. While often shared, K8s namespaces *can* offer some level of resource isolation if needed, but application logic remains key\.
	- __Dedicated Resources \(Less Common/High Cost\):__ For very large or sensitive tenants, potentially provision dedicated application instances or database instances\. This requires significant automation\.
- __Reference:__ See 12\_DevOps\_Infrastructure\.md\.

### __2\.7\. Automated White\-Label Tenant Provisioning Workflow__

- __Requirement:__ A fully automated, reliable process for creating and configuring new white\-label instances \(Point 7\.1\)\.
- __Trigger:__ Manual request by platform admin, or potentially automated via an API call from a partner portal\.
- __Steps \(Example Flow\):__
	1. __Create Tenant Record:__ Generate unique tenant\_id, store basic tenant info\.
	2. __Database Setup:__ Execute automation script \(Section 3\) to set up RLS policies, create schema, or provision a new database based on the chosen isolation strategy\.
	3. __Default Configuration:__ Apply default configurations using the Default Config Generator \(Section 4\)\.
	4. __Domain/Subdomain Setup:__ Configure necessary DNS \(if managing subdomains\) or prepare for custom domain CNAME mapping\. Initiate SSL certificate process\.
	5. __Branding Setup:__ Provision storage for branding assets; apply default branding initially\.
	6. __Create Initial Admin User:__ Create the first admin user account associated with this tenant\.
	7. __Trigger Welcome Email:__ Send setup/welcome email to the tenant admin \(using appropriate branding if possible\)\.
	8. __Logging:__ Log all provisioning steps and outcomes\.
- __Tooling:__ Utilize backend automation scripts, potentially orchestrated by a workflow engine or CI/CD pipeline, interacting with hosting APIs \(14\_Third\_Party\_Integrations\.md\) if needed\.

### __2\.8\. Tenant Onboarding & Offboarding__

- __Onboarding:__ Beyond technical provisioning, provide clear documentation and potentially guided setup wizards for tenant admins\.
- __Offboarding:__ Define a clear process for deactivating or deleting a tenant instance\. This __must__ include secure data handling \(archival or deletion according to legal/contractual requirements\) and removal of DNS/configurations\. This process should also be automated where possible but requires careful execution\.

### __2\.9\. White\-Label Documentation__

- __Requirement:__ Provide specific documentation for white\-label partners/tenant administrators covering customizable features, domain setup, user management within their tenant, etc\. \(Point 7\.2\)\.

## __3\. Automation Scripts \(Backend\) \- White\-Label Context__

- Scripts are essential for tenant provisioning, de\-provisioning, data migration across tenants \(if applicable and careful\), and applying configuration changes in bulk\.
- Ensure scripts are tenant\-aware and operate safely within the defined multi\-tenancy model\.

## __4\. Default Config Generator \- White\-Label Context__

- Provides the baseline configuration for *newly provisioned* white\-label tenants before they apply their customizations\.

## __5\. Restore & Clone Scripts \- White\-Label Context__

- __Restore:__ Procedures must support tenant\-specific restores, especially if using separate databases/schemas\. Testing is critical\.
- __Clone:__ Cloning tenant data for staging/testing requires __extreme care__ regarding data anonymization and ensuring data doesn't leak between the cloned environment and production or other tenants\.

## __6\. Cron Jobs / Scheduled Tasks \- White\-Label Context__

- Ensure scheduled tasks are tenant\-aware \(e\.g\., process data only for the relevant tenant or iterate through all active tenants\)\.
- Consider if certain tasks \(like report generation\) need to run per\-tenant or can be aggregated\. Resource usage must be monitored\.

