# __Project Management & Documentation \(Final Enhancements\)__

__Core Principle:__ This document, along with related files \(PLANNING\.md, TASK\.md/project\.index\.json, AI\_AGENT\_GUIDELINES\.md\), forms the essential "operating system" for AI agent collaboration\. Its primary purpose is to maintain agent focus, ensure task alignment, prevent deviation or destructive errors \(like deleting work or overwriting correct code\), and provide clear recovery paths if an agent does go off track due to context limitations\. __Strict adherence to these processes is mandatory for successful AI\-assisted development\.__

## __Core Files: The Agent's Compass__

- __README\.md__: Project intro, tech, scripts, deployment guide\. Provides initial orientation\.
- __PLANNING\.md__: Tech stack, constraints, scope, high\-level architecture, agent roles\. __Crucial for grounding the agent in the project's overall goals and limitations\.__ Agents should reference this if unsure about architectural choices\.
- __TASK\.md__ / __project\.index\.json__ \(Tasks Section\): Defines the specific, atomic units of work\. Contains backlog, active tasks, dependencies, and status\. __This is the primary driver for agent actions\.__ Agents *must* reference the specific task details *before* starting work and update it *upon completion*\.

## __Workflow: Integrating AI__

- __Task Management Tools:__ Use GitHub Projects, ClickUp, Jira, etc\., for human oversight and sprint planning\.
- __Syncing with AI:__ The canonical task list for AI agents resides in TASK\.md or preferably the structured task definitions within project\.index\.json \(as defined in AI\_AGENT\_GUIDELINES\.md\)\.
	- AI agents should be prompted to query the task system for their next assigned task based on priority and dependencies\.
	- AI agents __must__ update the status \(in progress, blocked, completed, verified\) of their assigned task within the canonical task system \(project\.index\.json or TASK\.md\) as they work\.

## __Contribution Guidelines: Quality Gates for AI Code__

- __PR Template:__ The Pull Request template \(used when merging AI\-generated code from a feature branch\) __must__ include:
	- Clear description of the changes *and the task ID* it addresses\.
	- Screenshots/GIFs demonstrating the changes \(if UI\-related\)\.
	- Mandatory checklist confirming:
		- Tests pass \(pnpm test\)\.
		- Linting/Formatting passes \(pnpm lint\)\.
		- Relevant documentation updated \(README\.md, CHANGELOG\.md\)\.
		- __Human review conducted__ \(see details below\)\.
- __Issues:__ Bug reports or issues must include clear steps to reproduce, expected vs\. actual behavior, and relevant log output/error messages\. This provides essential context for AI agents tasked with fixing bugs\.
- __Reviewing AI\-Generated Code \(New Subsection\):__ The mandatory human review step for AI\-generated code \(during PR\) must critically assess:
	- __Correctness:__ Does the code fulfill the task requirements accurately?
	- __Adherence to Standards:__ Does it follow guidelines in CORE\_CODING\_STANDARDS\.md, UI\_\* guides, Backend\_Development\_Patterns\.md, etc\.?
	- __Security:__ Are there any potential vulnerabilities introduced? \(Reference 13\_Authentication\_Security\.md\)\. Check input validation, authorization, etc\.
	- __Performance:__ Are there obvious performance bottlenecks or inefficient patterns? \(Reference 17\_Performance\_Optimization\_Standards\.md\)\.
	- __Non\-Destructive Changes:__ __Crucially, verify that only code within the defined task scope was modified\.__ Check git diff carefully for unintended deletions or alterations of existing, unrelated code\.
	- __Simplicity & Readability:__ Is the code overly complex? Did the AI hallucinate unnecessary code or dependencies? Is it understandable and maintainable?
	- __Test Coverage:__ Were appropriate tests generated or updated, and do they provide adequate coverage? \(Reference 10\_Testing\_QA\_Standards\.md\)\.

## __Docs & Dev Portal__

- __Feature README\.md:__ AI agents tasked with creating or modifying features must update the corresponding feature's README\.md\.
- __Dev Portal:__ If using Docusaurus/Docsify, AI agents might be tasked with updating specific documentation pages, requiring careful prompts and review\.

## __Agent Context Handoff & Focus Management \(CRITICAL\)__

This section defines the strict protocol for managing AI agent context and preventing deviation\.

1. __Pre\-Task Check \(Mandatory\):__ Before executing *any* code changes for a task, the agent __must__:
	- Re\-read the full details of the assigned task from TASK\.md or project\.index\.json \(including ID, description, context, dependencies, expected output\)\.
	- Re\-read PLANNING\.md to ensure alignment with overall architecture and constraints\.
	- Confirm understanding of the task and context\. If ambiguity exists, follow the "Requesting Clarification" protocol in AI\_AGENT\_GUIDELINES\.md\.
2. __Atomic Tasks:__ Tasks defined in the system should be small, specific, and independently verifiable\. This limits the potential impact if an agent deviates and makes non\-destructive updates easier to manage\. Complex features __must__ be broken down \(see Task Management in AI\_AGENT\_GUIDELINES\.md\)\.
3. __Non\-Destructive Updates \(Mandatory\):__
	- __Principle:__ Agents __must__ operate non\-destructively by default\. Modifications should be additive or targeted *only* to the specific code, elements, components, or files explicitly defined within the scope of the current task\. __Existing, unrelated, approved code, styles, UI elements, or configurations must not be removed or altered unless that is the explicit goal of the task\.__
	- __Scope Definition:__ The task description and context __must__ clearly define the boundaries of the required changes\. Prompts given to the agent should reinforce this scope \(e\.g\., "Update *only the specified component*\.\.\.", "Add a new CSS class without changing existing ones\.\.\."\)\.
	- __Verification:__
		- Agents should ideally be prompted to provide a summary or diff \(git diff\) of their changes *before* finalizing them\.
		- Human review during the PR process __must__ explicitly check that no unintended deletions or modifications occurred outside the task's scope\. Use git diff or the PR's file view carefully\.
	- __Prompting Strategy:__ Frame prompts to be specific and targeted\. Instead of "Improve the button styling," use "Update the background color and padding *only* for the button with id='save\-button' in src/components/SaveButton\.tsx\."
4. __Intermediate Checkpoints \(Optional but Recommended\):__ For tasks expected to take longer or involve significant changes, prompt the agent mid\-task: "Summarize the changes made so far for Task \[ID\]" or "Provide a diff of the changes for Task \[ID\]"\. Review this output to ensure the agent is still on track and adhering to non\-destructive principles\.
5. __Post\-Task Verification \(Mandatory\):__ Upon completing the implementation steps for a task, the agent __must__:
	- Run all relevant checks \(linting, tests\)\.
	- Update the task status to "completed" in TASK\.md or project\.index\.json\.
	- Update relevant README\.md files if feature documentation changed\.
	- Update CHANGELOG\.md if user\-facing changes were made \(following Conventional Commits\)\.
	- Commit the changes with a correctly formatted commit message referencing the task ID\.
	- *Await human review/verification* \(including non\-destructive check and points in "Reviewing AI\-Generated Code"\) before the task is marked "verified"\.
6. __Deviation Recovery Protocol:__ If an agent deviates, deletes work, or modifies code incorrectly:
	- __STOP:__ Immediately halt the agent's execution\.
	- __ASSESS:__ Identify the incorrect changes made, including any unintended deletions/modifications\.
	- __REVERT:__ Use Git to revert the unwanted changes\. __Do not rely on the agent to fix its own large\-scale deviations\.__ Common commands:
		- git status \(to see changes\)
		- git stash \(to temporarily save uncommitted changes if needed\)
		- git reset HEAD \-\-hard \(to discard all uncommitted changes \- use with caution\)
		- git checkout \. \(to discard changes in specific files\)
		- git checkout <branch\-name> \(to switch back to a clean branch\)
		- Refer to 21\_Revision\_Control\_Versioning\.md for Git workflow details\.
	- __RE\-ORIENT:__ Provide the agent with:
		- The correct Task ID it should be working on\.
		- The relevant context files \(PLANNING\.md, TASK\.md/project\.index\.json, specific feature files\)\.
		- The last known *good* state of the code \(e\.g\., "The code is now reverted to commit X\. Please restart Task \[ID\] focusing *only* on file Y\."\)\.
		- An explicit instruction to __disregard its previous internal state/memory__ regarding the deviated work\.
	- __PROCEED:__ Give the agent the specific, corrected instruction to proceed with the task from the known good state\. Monitor closely, potentially using intermediate checkpoints\.
7. __Adherence to Guidelines:__ Agents must always adhere to the protocols defined in AI\_AGENT\_GUIDELINES\.md, including error handling and clarification procedures\.

__\(Link to 11\_Backup\_Recovery\_Safety\.md\):__ Before instructing an AI agent to perform potentially risky refactoring or data migration tasks, consider manually creating a snapshot or ensuring version control is clean, allowing for easy rollback if needed\.

