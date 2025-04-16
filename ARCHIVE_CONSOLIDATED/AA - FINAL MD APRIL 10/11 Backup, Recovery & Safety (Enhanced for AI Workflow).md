# __Backup, Recovery & Safety \(Enhanced for AI Workflow\)__

__Core Principle:__ Data integrity and recoverability are paramount\. There must be multiple, tested layers of protection against data loss, whether caused by system failure, user error, or AI agent actions\. Assume failures *will* happen and plan accordingly\.

## __1\. Frontend Autosave System \(User Work Protection\)__

- __Mechanism:__ Use LocalForage or IndexedDB for robust client\-side storage of drafts \(forms, documents, configurations\)\. These offer better reliability and capacity than localStorage\.
- __Trigger:__ Autosave frequently \(e\.g\., every 5\-10 seconds of inactivity\) and *before* potentially disruptive actions \(e\.g\., navigating away, closing tab \- use beforeunload cautiously\)\. Also save on field blur\.
- __Error Handling:__ Wrap all storage operations \(setItem, getItem, removeItem\) in try\.\.\.catch blocks\. Log errors to the monitoring service \(e\.g\., Sentry\)\. If storage fails persistently, notify the user that autosave is inactive\. Consider a temporary in\-memory backup as a fallback\.
- __Indicator:__ Provide a clear, persistent UI indicator showing the last saved time \(e\.g\., "Draft saved at HH:MM:SS"\) or saving status \("Saving\.\.\."\)\.
- __Restore Prompt:__ On application load/re\-entry to a relevant page, reliably detect existing local drafts\. Prompt the user clearly: "We found an unsaved draft from \[Timestamp\]\. Would you like to restore it?"\. Provide options like "Restore" and "Discard"\. Ensure this prompt doesn't interfere with initial page load performance\.
- __Clearing:__ Explicitly clear local drafts only upon *successful* submission confirmed by the backend, or via an explicit user "Discard Draft" action with confirmation\.

## __2\. Snapshot System \(User Data / Configuration\)__

- __Purpose:__ Allow point\-in\-time backups of specific user\-controlled data sets \(form schemas, complex configurations, workspace settings\) initiated by users or admins\.
- __Mechanism:__
	- User/Admin initiated via UI\.
	- __Automation:__ Consider automatically creating a snapshot before executing potentially destructive or complex configuration changes \(especially if initiated via AI\)\.
- __Storage:__ Store snapshots securely in the primary database or dedicated versioned object storage \(S3/Supabase Storage with versioning and potentially object lock/immutability for critical snapshots\)\.
- __Versioning:__ Include timestamp, user ID \(who created it\), optional description, and potentially the source of the change \(e\.g\., "Manual Edit", "AI Refactor Task\-XYZ"\)\.
- __RBAC:__ Implement Role\-Based Access Control for snapshot management\. Define who can create, view, restore, and delete snapshots \(e\.g\., admins may have full control, users might only restore their own\)\. Deletion should require confirmation\.
- __UI:__ Provide a clear interface to view snapshot history, compare versions \(diff\), restore to a previous state \(with confirmation\), and manage snapshots according to permissions\.

## __3\. AI Agent Data Safety Protocols \(CRITICAL\)__

- __Principle:__ AI agents __must not__ perform unconfirmed destructive actions on user data or critical configuration\.
- __Read\-Only First:__ Design prompts and agent capabilities to favor read\-only operations whenever possible\.
- __Explicit Confirmation:__ Any action involving data deletion, overwriting, or significant modification \(beyond trivial updates\) initiated by an AI agent __requires explicit, unambiguous user confirmation__ via the UI before execution\. The confirmation prompt must clearly state:
	- The exact action \(e\.g\., "Delete form 'XYZ'"\)\.
	- The target data/resource\.
	- Potential consequences \(e\.g\., "This action cannot be undone"\)\.
- __Descriptive Prompts:__ Prompts instructing AI agents to modify data must be precise, specifying the exact target and the change required\. Avoid vague instructions like "clean up old data"\.
- __Snapshot Integration:__ Agents *can* be prompted to *initiate* the creation of a snapshot \(using the defined snapshot mechanism\) before attempting potentially risky operations, but the snapshot creation itself should be logged and ideally confirmable\.
- __Restricted Restore:__ AI agents __should not__ be given the capability to directly trigger data restoration from backups or snapshots without human oversight and confirmation through the UI\.

## __4\. Recovery Flow & Mandatory Testing__

- __Database \(PITR\):__
	- Utilize Point\-in\-Time Recovery \(PITR\) provided by the database provider \(Supabase/AWS RDS\)\. Configure automated daily backups with a reasonable retention period \(e\.g\., 7\-30 days\)\.
	- __Mandatory Testing \(Quarterly\):__ Regularly \(at least quarterly\) perform test restores of the database backup to a *separate, temporary environment*\. Verify data integrity, consistency, and completeness after the restore\. Document the process and results\. Failure to successfully test restores indicates a critical risk\.
- __Object Storage \(Versioning\):__
	- Enable versioning on all critical S3 buckets / Supabase Storage\.
	- __Mandatory Testing \(Quarterly\):__ Regularly test the process of retrieving previous versions of critical files or objects\. Document the process\.
- __Frontend Drafts:__
	- __Testing:__ Manually test the draft recovery mechanism under various scenarios \(browser crash simulation, closing tab, logging out and back in\)\.

## __5\. Persistent Storage Tools__

- __Primary DB:__ PostgreSQL \(via Supabase or managed service like RDS\)\. Ensure backup/PITR features are enabled and configured correctly\.
- __Object Storage:__ Supabase Storage or AWS S3\. Ensure versioning and appropriate access controls are enabled\. Consider lifecycle policies for older versions/backups\.
- __Caching/Queues:__ Redis\. Data in Redis is typically volatile; do not rely on it for primary data persistence\. Ensure applications can rebuild cache or tolerate queue loss if Redis fails \(though Redis itself can have persistence options\)\.

## __6\. Audit Logs \(Enhanced for Safety\)__

- __Scope:__ Log all critical actions, especially those related to data modification, deletion, configuration changes, and recovery operations\.
- __Critical Events to Log:__
	- User/Admin login/logout/failed login attempts\.
	- Resource create, update, delete \(include resource ID and summary of changes if possible\)\.
	- snapshot\_created \(incl\. user, description\)\.
	- snapshot\_restored \(incl\. user, target snapshot ID\)\.
	- snapshot\_deleted \(incl\. user, target snapshot ID\)\.
	- permission\_change \(user roles/permissions modified\)\.
	- backup\_started, backup\_completed, backup\_failed\.
	- restore\_attempted \(manual or automated\)\.
	- restore\_completed, restore\_failed\.
	- __AI Actions:__ Log AI\-initiated actions *before* confirmation, the user's confirmation decision, and the final execution result\.
- __Storage & Access:__ Use a dedicated, secure logging system\. Ensure logs are tamper\-evident if possible\. Provide admins with powerful search/filter capabilities\. Correlate logs with requestId \(see 09\_Error\_Handling\_Debugging\.md\)\.

## __7\. Cloud Redundancy & Failover__

- __Database:__ Use multi\-AZ replication and automated failover\.
- __Application Servers:__ Deploy across multiple AZs with load balancing and health checks\.
- __Static Assets/Frontend:__ Use CDN for resilience\.
- __Cross\-Region Backups \(Optional\):__ For highest resilience, consider replicating critical backups \(DB snapshots, object storage\) to a different geographic region\.

## __8\. Manual Restore Options__

- __Documentation:__ Maintain detailed, *tested*, and easily accessible documentation for performing manual restores from all backup types \(DB, Object Storage\)\. Include necessary credentials access procedures\.
- __Regular Testing:__ Manual restore procedures __must__ be tested regularly \(at least quarterly\) alongside automated restore tests\.
- __Secure Access:__ Define and secure the process for how authorized personnel can trigger manual restores\. Log all manual restore actions thoroughly\.

## __9\. Backup Monitoring & Alerting \(New Section\)__

- __Monitor Backup Jobs:__ Implement monitoring for all automated backup processes \(database PITR, scheduled object storage backups\)\.
- __Alert on Failures:__ Configure immediate alerts \(e\.g\., email, Slack, PagerDuty\) for any backup job failures\. Treat backup failures as critical incidents\.
- __Verify Backup Integrity:__ Periodically \(less frequently than restore tests, e\.g\., annually\) perform checks on backup file integrity if possible \(e\.g\., checksum verification\)\.

