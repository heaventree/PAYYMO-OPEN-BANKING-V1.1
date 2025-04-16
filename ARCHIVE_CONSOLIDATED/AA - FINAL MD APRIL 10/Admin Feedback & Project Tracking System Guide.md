# __Admin Feedback & Project Tracking System Guide__

## __1\. Introduction__

__Goal:__ To define a unified administrative interface for managing various types of project\-related items, including internally defined roadmap features, debug tasks/bugs, and externally submitted user feedback \(especially visual point\-and\-click feedback\)\. This system provides a central place for tracking progress, assigning tasks, managing statuses, and facilitating communication around project development and user input\.

This guide draws inspiration from the concepts presented in the "WCAG Admin Project Management System" and "Visual Feedback System" documents\.

## __2\. Core Data Models__

A flexible data model is needed to accommodate different item types\. A single table with a type discriminator or related tables could work\. Below is a conceptual model inspired by the Drizzle schema provided, adapted for unification:

// Conceptual Schema \(e\.g\., using Drizzle ORM syntax for illustration\)  
// Assumes a central 'tracked\_items' table  
  
import \{ pgTable, serial, text, timestamp, integer, json, varchar \} from "drizzle\-orm/pg\-core";  
  
// Define potential enum types \(or use varchar with validation\)  
const itemTypeEnum = pgEnum\('item\_type', \['roadmap', 'debug', 'visual\_feedback', 'general\_task'\]\);  
const statusEnum = pgEnum\('status', \['planned', 'open', 'identified', 'investigating', 'in\-progress', 'testing', 'resolved', 'closed', 'deferred'\]\);  
const priorityEnum = pgEnum\('priority', \['low', 'medium', 'high', 'critical'\]\);  
  
export const trackedItems = pgTable\("tracked\_items", \{  
  id: serial\("id"\)\.primaryKey\(\),  
  tenantId: text\("tenant\_id"\)\.notNull\(\), // For multi\-tenancy  
  projectId: text\("project\_id"\)\.notNull\(\), // Link to project if managing multiple  
  
  itemType: itemTypeEnum\("item\_type"\)\.notNull\(\), // 'roadmap', 'debug', 'visual\_feedback', etc\.  
  
  title: text\("title"\)\.notNull\(\),  
  description: text\("description"\)\.notNull\(\),  
  
  status: statusEnum\("status"\)\.notNull\(\)\.default\("open"\),  
  priority: priorityEnum\("priority"\)\.notNull\(\)\.default\("medium"\),  
  
  createdAt: timestamp\("created\_at", \{ withTimezone: true \}\)\.defaultNow\(\)\.notNull\(\),  
  updatedAt: timestamp\("updated\_at", \{ withTimezone: true \}\)\.defaultNow\(\)\.notNull\(\),  
  
  reporter: text\("reporter"\), // User ID or name/email  
  assignedTo: text\("assigned\_to"\), // User ID or name  
  
  // Type\-specific fields \(can be NULL depending on itemType\)  
  category: text\("category"\), // For roadmap/debug \(e\.g\., 'ui', 'core', 'api'\)  
  pagePath: text\("page\_path"\), // For visual feedback  
  elementPath: text\("element\_path"\), // CSS Selector for visual feedback  
  coordinates: json\("coordinates"\)\.$type<\{x: number, y: number\}>\(\), // Click coordinates for visual feedback  
  dependencies: json\("dependencies"\)\.$type<string\[\]>\(\), // Array of other item IDs \(for roadmap\)  
  dueDate: timestamp\("due\_date", \{ withTimezone: true \}\),  
  
  // Add other relevant fields like tags, attachments reference, etc\.  
\}\);  
  
export const itemComments = pgTable\("item\_comments", \{  
  id: serial\("id"\)\.primaryKey\(\),  
  itemId: integer\("item\_id"\)\.references\(\(\) => trackedItems\.id, \{ onDelete: "cascade" \}\)\.notNull\(\),  
  author: text\("author"\)\.notNull\(\),  
  content: text\("content"\)\.notNull\(\),  
  createdAt: timestamp\("created\_at", \{ withTimezone: true \}\)\.defaultNow\(\)\.notNull\(\),  
\}\);  
  
// Zod schemas for validation would be derived from this\.  


## __3\. Key Features \(Admin Interface\)__

The admin interface should provide the following functionalities:

- __Unified Dashboard View:__
	- Overview widgets showing counts of items by status, priority, itemType, or assignee\.
	- Quick access to recently created or high\-priority items\.
	- Potentially charts showing trends \(e\.g\., items resolved over time\)\.
	- Configurable based on admin preferences\.
- __Unified List View:__
	- A central table displaying all trackedItems\.
	- __Columns:__ Key information like ID, Title, Type, Status, Priority, Assignee, Project, Page Path \(if applicable\), Created Date, Updated Date\. Columns should be customizable/sortable\.
	- __Filtering:__ Robust filtering options are essential:
		- By itemType \(Roadmap, Debug, Visual Feedback, etc\.\)\.
		- By status \(Open, In Progress, Resolved, etc\.\)\.
		- By priority \(Critical, High, Medium, Low\)\.
		- By assignee\.
		- By projectId \(if applicable\)\.
		- By pagePath \(useful for visual feedback\)\.
		- By date range \(createdAt, updatedAt\)\.
		- Free\-text search across title and description\.
	- __Sorting:__ Ability to sort by any major column\. Default sort likely by priority then createdAt or updatedAt\.
	- __Bulk Actions:__ Allow selecting multiple items to perform actions like changing status, priority, or assignee\.
- __Detail View \(Modal or Dedicated Page\):__
	- Triggered by clicking an item in the list view\.
	- Displays all fields associated with the trackedItem\.
	- __Visual Context:__ For visual\_feedback items, display the pagePath, elementPath, and potentially render a screenshot or highlight the element on an embedded view if feasible\. Show coordinates\.
	- __Commenting Thread:__ Display comments associated with the item \(itemComments\) chronologically\. Provide an input field to add new comments\.
	- __Activity Log:__ Show a history of changes \(status updates, assignments, edits\)\.
	- __Editing:__ Allow authorized admins to edit fields like title, description, status, priority, assignee, category, dueDate\.
- __Item Creation:__ A form or modal to manually create new items \(especially for Roadmap and Debug types\)\.
- __Assignment Workflow:__ Clear mechanism to assign items to team members \(users within the system\)\. Potentially includes notifications upon assignment\.
- __Reporting \(Optional\):__ Basic reports on item resolution times, volume by type/status, workload per assignee\.

## __4\. Integration Points__

- __Visual Feedback Widget:__ An API endpoint \(e\.g\., /api/external/feedbacks as in Doc 2\) receives submissions from the frontend point\-and\-click widget\. This endpoint creates new trackedItems with itemType: 'visual\_feedback'\.
- __Internal Creation:__ UI within the admin system allows manual creation of roadmap and debug items\.
- __External Systems \(Optional\):__ Consider APIs or webhooks to integrate with external issue trackers \(Jira, GitHub Issues\) or project management tools, potentially syncing status or creating items\. Reference 14\_Third\_Party\_Integrations\.md\.

## __5\. UI/UX Considerations__

- __Leverage Design System:__ Utilize the established UI Kit/Design System \(src/UI\_Design\_System\_Architecture\.md\) and component examples \(src/UI\_Examples\_and\_Patterns\.md\) for consistency\.
- __Key Components:__ Requires components like:
	- Table \(with sorting, filtering capabilities \- e\.g\., TanStack Table\)
	- Dialog / Modal \(for detail view/editing\)
	- Select / Dropdowns \(for status, priority, assignee filters/editors\)
	- Badge \(for visually indicating status, priority, type\)
	- Avatar \(for assignees\)
	- Input, Textarea, DatePicker \(for forms\)
	- Button
	- Card \(for dashboard widgets\)
	- Progress \(for roadmap/completion view\)
- __Information Density:__ Balance showing sufficient information in list views with maintaining clarity\. Use tooltips or expandable rows if needed\.
- __Responsiveness:__ Ensure the admin interface works effectively on various screen sizes\.
- __Accessibility:__ Adhere strictly to 16\_Accessibility\_Compliance\.md\.

## __6\. Technical Considerations__

- __Frontend:__ React, TypeScript\. Use TanStack Query for efficient data fetching, caching, and state synchronization with the backend API for the feedback list and details\. Use Zustand for local UI state management \(e\.g\., filter values, modal open state\)\.
- __Backend:__ Node\.js \(Fastify/Express\)\. Requires a comprehensive set of API endpoints for CRUD \(Create, Read, Update, Delete\) operations on trackedItems and itemComments\. Implement proper authentication and authorization \(RBAC\) to ensure only authorized admins can perform actions\. Use validation \(Zod\) on all API inputs\.
- __Database:__ PostgreSQL with Prisma or Drizzle ORM, implementing the data models defined above\. Ensure appropriate indexing on fields used for filtering and sorting \(tenantId, projectId, status, priority, itemType, createdAt\)\.

