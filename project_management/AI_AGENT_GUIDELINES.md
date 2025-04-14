# AI Agent Guidelines for Payymo Project

This document provides specific guidelines for AI agents working on the Payymo project, focusing on task management, non-destructive updates, and project organization.

## Core Principles

1. **Non-Destructive Development**: AI agents must never remove or modify existing, functional code outside the scope of their assigned task.
2. **Task-Focused Work**: Always reference the specific task ID and details before beginning work.
3. **Context Awareness**: Understand the project structure and file organization before making changes.
4. **Documentation**: Update relevant documentation alongside code changes.
5. **Verification**: Test changes thoroughly and report results clearly.

## Project Navigation

AI agents should use the following files to navigate and understand the project:

1. **project_management/PLANNING.md**: 
   - Understand the project vision, technical architecture, and constraints
   - Reference this file before making architectural decisions

2. **project_management/TASK.md**:
   - Find task details, requirements, and dependencies
   - Update task status as work progresses

3. **project_management/project.index.json**:
   - Machine-readable project structure
   - Contains file paths, API endpoints, schemas, and task definitions

4. **md_docs/master_development_guide.md**:
   - Comprehensive development guidelines
   - Technical standards and patterns

## Task Workflow for AI Agents

### 1. Task Assignment and Understanding
- Identify the specific task ID (e.g., PM-001)
- Read the full task description in TASK.md or project.index.json
- Review task dependencies and ensure they are completed
- Study affected files and related documentation

### 2. Pre-Implementation Check
- Verify project architecture alignment in PLANNING.md
- Check for related issues in ISSUES.md
- Understand the task's context within the broader project goals
- Ask for clarification if requirements are ambiguous

### 3. Implementation
- Update task status to "in progress" in TASK.md
- Follow coding standards in md_docs/development_guide.md
- Make non-destructive changes, focusing only on the task scope
- Add clear comments explaining complex logic
- Include appropriate error handling

### 4. Testing and Verification
- Test all changes thoroughly
- Verify against acceptance criteria in the task description
- Check for unintended side effects
- Document testing results

### 5. Documentation Updates
- Update affected documentation files
- Add entries to CHANGELOG.md in appropriate sections
- Update task status in TASK.md to "review"
- Summarize changes made and verification results

## Non-Destructive Update Guidelines

AI agents must adhere to these principles to ensure non-destructive updates:

1. **Scope Limitation**:
   - Make changes only to files specified in the task
   - Focus modifications on specific functions or code blocks
   - Do not refactor unrelated code, even if it seems inefficient

2. **Additive Approach**:
   - Prefer adding new code over modifying existing code
   - When changes to existing code are necessary, make minimal, targeted modifications
   - Never delete functional code without explicit instructions

3. **Preserve Behavior**:
   - Maintain existing functionality unless explicitly instructed to change it
   - Test to ensure existing features continue to work
   - Be especially careful with API endpoints and database operations

4. **Isolation Techniques**:
   - Use feature flags to isolate new functionality
   - Implement defensive coding practices
   - Add appropriate error handling for new code

## Collaboration with Humans

When collaborating with human developers:

1. **Status Updates**:
   - Provide clear summaries of work completed
   - Highlight any potential issues or concerns
   - Ask specific, targeted questions when needed

2. **Change Proposals**:
   - Present changes with clear explanations of their purpose
   - Offer alternatives for complex decisions
   - Wait for approval before implementing major changes

3. **Knowledge Transfer**:
   - Document complex implementations thoroughly
   - Explain the rationale behind technical decisions
   - Highlight areas that may need future attention

## Handling Errors and Recovery

If an AI agent makes a mistake or encounters an error:

1. **Stop immediately** to prevent cascading issues
2. **Document the error** clearly
3. **Propose a recovery plan** with specific steps
4. **Request guidance** if the recovery is complex
5. **Learn from the mistake** to avoid similar issues

## Project-Specific Guidelines

For the Payymo project specifically:

1. **Financial Data Handling**:
   - Treat all transaction data as sensitive information
   - Follow security best practices for financial applications
   - Validate all monetary calculations thoroughly

2. **API Integrations**:
   - Use service classes for external API interactions
   - Follow OAuth best practices for authentication
   - Implement proper error handling for API failures

3. **Multi-Tenant Architecture**:
   - Maintain strict data isolation between tenants
   - Always filter queries by tenant ID
   - Never expose data from one tenant to another

4. **Dashboard Development**:
   - Follow the NobleUI design patterns
   - Ensure performance optimization for data-heavy views
   - Implement responsive design for all UI components

## Prompt Templates

When working with the Payymo project, use these prompt templates for consistent results:

### Task Implementation Prompt

```
Role: Payymo Developer
Task: PM-XXX
Objective: [Brief description of the task]
Context: [Reference to relevant files, documentation, or issues]
Requirements:
- [Specific requirement 1]
- [Specific requirement 2]
Expected Output: [Description of the expected result]
```

### Issue Resolution Prompt

```
Role: Payymo Troubleshooter
Issue: ISSUE-XXX
Description: [Brief description of the issue]
Error Context: [Error messages, logs, or symptoms]
Affected Files: [List of relevant files]
Previous Attempts: [Any previous attempts to fix]
Required: Propose a solution that is minimally invasive and focused on the specific issue.
```

### Code Review Prompt

```
Role: Payymo Code Reviewer
Files to Review: [List of changed files]
Implementation Details: [Brief description of the changes]
Checklist:
- Does the code follow project standards?
- Is error handling implemented properly?
- Are there any potential performance issues?
- Is the code sufficiently documented?
- Does the code maintain multi-tenant isolation?
- Are there any security concerns?
```

## Continuous Improvement

AI agents should contribute to the continuous improvement of the project by:

1. Suggesting updates to documentation for clarity
2. Identifying potential issues before they become problems
3. Recommending optimizations that can be considered for future tasks
4. Helping maintain consistent style and quality across the codebase