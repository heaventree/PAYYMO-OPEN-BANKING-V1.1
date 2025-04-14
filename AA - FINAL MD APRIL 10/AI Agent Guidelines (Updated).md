# __AI Agent Guidelines \(Updated\)__

This document provides comprehensive guidelines for AI agents involved in the project, including roles, prompt engineering, file awareness, memory, project indexing, fix suggestions, audit trails, task management, and advanced protocols\.

## __Agent Roles__

- __AI Form Builder:__ Suggests field groups from user input\.
- __AI Debugger:__ Detects errors, suggests fixes with source mapping\.
- __AI Styler:__ Suggests Tailwind class improvements\.
- __AI Accessibility Auditor:__ WCAG contrast and role checks\.
- __AI Navigator:__ Understands file structure, project goals, and agent workflows\.
- __AI Task Manager:__ Parses requirements, breaks down tasks, manages dependencies\.

## __Prompt Engineering__

- Always define role and objective\.
- Include example input/output when calling the LLM\.  
\{ "role": "AI\_DEBUGGER", "objective": "Fix broken submit logic", "example\_input": "form fails on field blur" \}  

- Provide relevant context \(e\.g\., file paths, code snippets, task ID\)\.

## __File Awareness__

- Agent knows file structure and data source\.
- Agent will not hallucinate imports or paths\.
- Agents should reference MASTER\_INDEX\.md and project\.index\.json to locate relevant files and understand project structure\.

## __Memory__

- Agents reference PLANNING\.md and TASK\.md \(or the task management system\) at session start\.
- Memory includes last 20 errors and 20 fixes\.
- Errors are hashed and stored on failure\.
- Hashes link to file/line/suggested fix\.
- AI checks hash on every error rerun\.

## __Project Indexing__

- project\.index\.json stores all endpoints, schemas, pages, types, and tasks\. *\(This file needs to be maintained\.\)*
- Agents should consult this file to understand the project's structure and available resources\.

## __Fix Suggestions__

- LLM fix proposals are diffed before applying\.
- User can approve or rollback\.

## __Audit Trail__

- Logs contain:
	- Original code
	- AI suggestion
	- User decision
	- Final commit

## __Task Management__

*\(Incorporating concepts from Roo Code Boomerang Tasks & Claude Task Master\)*

1. __Task Definition:__
	- Tasks are defined in a structured format \(e\.g\., JSON within project\.index\.json or separate task files\)\.
	- __Fields:__ id, title, description, status \("to do", "in progress", "blocked", "verified"\), priority \("high", "medium", "low"\), dependencies \(array of task IDs\), context \(files, data, tools\), assignee, output, estimated\_complexity\.

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


1. __Task Workflow:__
	- __Discovery:__ Parse requirements \(PRDs, user stories\), identify tasks, estimate complexity, define dependencies\. Agents can assist here\.
	- __Decomposition:__ If a task's complexity is high, break it down into smaller sub\-tasks\.
	- __Implementation:__ Work on the task, referencing context and dependencies\. Update status to "in progress"\.
	- __Verification:__ Test the output \(unit, integration, E2E tests\)\. Perform code review\. Agents can assist with automated checks\. Update status to "completed"\.
	- __Completion:__ Merge code, update documentation, potentially deploy\. Update status to "verified"\.
2. __Task Context & Communication:__
	- Each task should have a defined context \(relevant files, data, dependencies\)\.
	- Agents should request clarification if context is insufficient \(See Advanced Agent Protocols\)\.
	- Information between dependent tasks must be passed explicitly \(e\.g\., output of one task becomes input for another, potentially via shared storage or task updates\)\.
	- Agents update task status via the defined system \(e\.g\., updating project\.index\.json or specific task files\)\.
3. __Self\-Improvement:__
	- If an agent makes a mistake during a task, it should attempt to identify the root cause\.
	- Suggest adding a new rule or guideline to relevant documentation \(e\.g\., CORE\_CODING\_STANDARDS\.md or this file\) to prevent recurrence\.

## __Agent Interaction Guidelines__

- Agents should clearly state the task they are working on\.
- Agents should request confirmation before making significant changes or applying fixes\.
- Agents should update relevant documentation \(TASK\.md, README\.md, CHANGELOG\.md\) upon task completion\.

## __Advanced Agent Protocols__

*\(New section based on QA Audit\)*

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

