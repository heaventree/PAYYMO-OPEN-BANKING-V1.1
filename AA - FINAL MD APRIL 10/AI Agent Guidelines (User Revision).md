# __AI Agent Guidelines \(User Revision\)__

This document provides comprehensive guidelines for AI agents involved in the project\. It covers roles, prompt engineering, file awareness, memory management, project indexing, fix suggestions, audit trails, task management, and advanced protocols for error handling and inter\-agent communications\. The goal is to ensure that AI agents integrate seamlessly with human workflows and maintain the quality, clarity, and consistency expected across the codebase\.

## __1\. Agent Roles__

Each AI agent has a distinct role to support project development:

- __AI Form Builder:__
	- Function: Analyzes user input to suggest logical field groups and form structures\.
- __AI Debugger:__
	- Function: Detects errors, provides source mapping, and suggests corrections\.
- __AI Styler:__
	- Function: Recommends improvements for Tailwind classes and UI styling consistency\.
- __AI Accessibility Auditor:__
	- Function: Checks WCAG compliance—including contrast ratios and ARIA roles—to ensure accessibility\.
- __AI Navigator:__
	- Function: Understands file structure, project goals, and overall agent workflows by consulting centralized documentation\.
- __AI Task Manager:__
	- Function: Parses requirements, breaks down tasks into actionable items, manages dependencies, and tracks progress\.

Each role should be clearly declared in agent prompts and referenced in corresponding documentation \(e\.g\., MASTER\_INDEX\.md, project\.index\.json\)\.

## __2\. Prompt Engineering__

- __Role and Objective Declaration:__ Every AI prompt must define the role and objective\. For example:  
\{  
  "role": "AI\_DEBUGGER",  
  "objective": "Fix broken submit logic",  
  "example\_input": "form fails on field blur"  
\}  

- __Include Context:__ Provide relevant context such as file paths, code snippets, and task IDs\.
- __Sample Input/Output:__ When applicable, include example inputs and expected outputs to reduce ambiguity\.

## __3\. File Awareness__

- __Knowledge of File Structure:__ AI agents must have an up\-to\-date understanding of the project’s file organization\. Consult the MASTER\_INDEX\.md and project\.index\.json to:
	- Locate files accurately\.
	- Reference correct import paths\.
	- Avoid hallucinating non\-existent modules or directories\.
- __Strict Referencing:__ Agents must not generate or reference file paths or imports not documented in the project index\.

## __4\. Memory and Context Management__

- __Reference Documents:__ Agents should reference the PLANNING\.md and TASK\.md \(or the project’s task management system\) at the start of a session\.
- __Error Memory:__ Maintain a rolling memory of the last 20 errors and corresponding fixes\. Each error is hashed and linked to its file, line number, and suggested fix\.
- __Hash Verification:__ Every time an error is encountered, re\-check its hash to determine if the problem has been previously addressed\.
- __Note:__ Robust memory management can also be implemented using enhanced libraries, vector databases, or custom strategies as detailed in 15\_Project\_Management\_Documentation\.md\.

## __5\. Project Indexing__

- __Central Resource:__ The project\.index\.json file serves as the master index for endpoints, schemas, pages, types, and tasks\. It must be maintained accurately\.
- __Reference for Context:__ Agents should consult this file to understand:
	- The overall project structure\.
	- Existing resources and endpoints\.
	- Tasks and dependencies already in progress\.

## __6\. Fix Suggestions__

- __Diffing Process:__ All LLM\-proposed code fixes must be diffed against the current version before being applied\.
- __User Approval:__ Allow for user approval or rollback of AI suggestions to maintain control and accountability\.

## __7\. Audit Trail__

- __Logging Standards:__ Ensure that the following elements are logged:
	- Original Code: The state before any suggestion\.
	- AI Suggestion: The generated code or change proposal\.
	- User Decision: Approval, modification, or rejection of the suggestion\.
	- Final Commit: The resulting code state after applying the approved change\.to d
	- __Tracking:__ These logs should be stored in a central audit system to enable review and traceability\.
	- 8\. Task, "in progress", "blocked", "completed", "verified"\), priority \("high", "medium", "low"\), dependencies \(array of task IDs\), context \(files, data, tools\), assignee, output, estimated\_complexity\.

// Example Task Definition  
\{  
  "id": "TASK\-123",  
  "title": "Implement User Authentication",  
  "description": "Implement user authentication using Supabase Auth, including login, registration, and password reset\.",  
  "status": "to do",  
  "priority": "high",  
  "dependencies": \["TASK\-122"\],  
  "context": \{  
    "files": \["13\_Authentication\_Security\.md", "src/features/auth/components/AuthForm\.tsx", "src/lib/auth\.ts"\],  
    "data": \{\},  
    "tools": \["Supabase CLI"\]  
  \},  
  "assignee": "AI\_AGENT\-Auth",  
  "output": "Working user authentication flow\.",  
  "estimated\_complexity": "medium"  
\}  


- __Task Workflow:__
	- __Discovery:__ Parse requirements \(PRDs, user stories\), identify tasks, estimate complexity, define dependencies\. Agents can assist here\.
	- __Decomposition:__ If a task's complexity is high, break it down into smaller sub\-tasks\.
	- __Implementation:__ Work on the task, referencing context and dependencies\. Update status to "in progress"\.
	- __Verification:__ Test the output \(unit, integration, E2E tests\)\. Perform code review\. Agents can assist with automated checks\. Update status to "completed"\.
	- __Completion:__ Merge code, update documentation, potentially deploy\. Update status to "verified"\.
- __Task Context & Communication:__
	- Each task should have a defined context \(relevant files, data, dependencies\)\.
	- Agents should request clarification if context is insufficient \(See Advanced Agent Protocols\)\.
	- Information between dependent tasks must be passed explicitly \(e\.g\., output of one task becomes input for another, potentially via shared storage or task updates\)\.
	- Agents update task status via the defined system \(e\.g\., updating project\.index\.json or specific task files\)\.
- __Self\-Improvement:__
	- If an agent makes a mistake during a task, it should attempt to identify the root cause\.
	- Suggest adding a new rule or guideline to relevant documentation \(e\.g\., CORE\_CODING\_STANDARDS\.md or this file\) to prevent recurrence\.

## __Agent Interaction Guidelines__

- Agents should clearly state the task they are working on\.
- Agents should request confirmation before making significant changes or applying fixes\.
- Agents should update relevant documentation \(TASK\.md, README\.md, CHANGELOG\.md\) upon task completion\.

## __Advanced Agent Protocols__

*\(Added based on QA Audit\)*

1. __Agent Error Handling:__
	- If an agent encounters an error during task execution that it cannot resolve autonomously:
		- __Log:__ Clearly log the error encountered, including stack traces or relevant details\.
		- __State Blockage:__ Explicitly state that it is blocked on the current task \(e\.g\., update task status to "blocked"\)\.
		- __Identify Cause \(If Possible\):__ Briefly explain the nature of the error and, if possible, suggest potential causes \(e\.g\., "Encountered TypeError in src/utils/helper\.ts, possibly due to unexpected null value\."\)\.
		- __Request Intervention:__ Clearly request human review or intervention to resolve the blocker\.
2. __Requesting Clarification:__
	- If task requirements or context are ambiguous or insufficient:
		- __State Ambiguity:__ Clearly state what information is missing or unclear \(e\.g\., "The requirement 'Implement sorting' needs clarification: Which fields should be sortable? What is the default sort order?"\)\.
		- __Ask Specific Questions:__ Formulate precise questions to resolve the ambiguity\.
		- __Suggest Interpretations \(Optional\):__ Offer possible interpretations or options to guide the clarification process \(e\.g\., "Should sorting be client\-side or server\-side?"\)\.
		- __Update Status:__ Potentially mark the task as "blocked" pending clarification\.
3. __Inter\-Agent Communication & Coordination:__
	- __Task System as Hub:__ Primarily use the Task Management system \(project\.index\.json or task files\) for coordination\. Define clear dependencies\.
	- __Handoffs:__ When one agent's task output is required for another agent's task:
		- The first agent updates the task status to "completed" or "verified"\.
		- The first agent ensures the output \(e\.g\., code committed, API endpoint documented, file generated\) is clearly referenced or accessible according to the task definition\.
		- The second agent checks the status and dependencies before starting its task\.
	- __Shared Context:__ For complex interactions, define specific shared context points \(e\.g\., a dedicated section in TASK\.md or a temporary shared document\) if direct data passing is needed beyond task outputs\. Avoid relying on implicit shared memory\.

