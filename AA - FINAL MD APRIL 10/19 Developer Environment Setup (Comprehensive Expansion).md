# __Developer Environment Setup \(Comprehensive Expansion\)__

__Core Principle:__ A consistent and correctly configured development environment is crucial for both human developers and AI agents to work efficiently, maintain code quality, and collaborate effectively\. This document outlines the key aspects of the environment setup and workflow\.

__IMPORTANT:__ For initial setup prerequisites \(Node\.js, pnpm, Docker\), specific setup commands \(git clone, pnpm install\), required environment variables \(\.env\.local\), and common scripts \(dev, build, lint, test\), agents __must__ refer to:

- __CORE\_TECH\_STACK\.md__ \(for prerequisites\)
- __CORE\_ENV\_SETUP\.md__ \(for setup steps, ENV keys, scripts\)

This document focuses on workflow and tooling within that established environment\.

## __Git Workflow & Branching \(Expanded\)__

Adherence to the Git workflow is essential for collaboration and preventing code conflicts or loss of work\. Refer to 21\_Revision\_Control\_Versioning\.md for full details\. Key points for agents:

- __Main Branches:__ main \(production\) and develop \(integration\) are protected\. Direct pushes are disallowed\.
- __Feature Branches:__
	- Always create a new feature branch from the *latest* develop branch \(git checkout develop; git pull; git checkout \-b feature/TASK\-ID\-description\)\.
	- Branch naming: feature/, feat/, fix/, bugfix/, docs/, chore/ followed by Task ID \(if applicable\) and a short description \(e\.g\., feat/TASK\-123\-add\-login\-button\)\.
- __Commits:__ Follow Conventional Commit standards \(<type>\(<scope>\): <subject>\)\. Reference 21\_Revision\_Control\_Versioning\.md\. Commit frequently with meaningful messages\.
- __Keeping Updated:__ Regularly update your feature branch with the latest changes from develop to minimize merge conflicts later \(git pull origin develop followed by resolving any conflicts, or preferably git fetch origin; git rebase origin/develop\)\.
- __Pull Requests \(PRs\):__
	- Once a task is complete and tested locally, push the feature branch \(git push origin feature/TASK\-ID\-description\)\.
	- Create a Pull Request on GitHub targeting the develop branch\.
	- Ensure the PR template is filled correctly \(Task ID, description, testing steps\)\. Reference 15\_Project\_Management\_Documentation\.md\.
	- The CI pipeline \(GitHub Actions\) will automatically run checks \(lint, tests, build\)\. PRs cannot be merged if checks fail\.
	- Human review is required before merging\.

## __Editor Setup \(VS Code Recommended\)__

Using a consistent editor setup with recommended extensions helps enforce standards and provides useful context\.

- __Recommended Editor:__ Visual Studio Code \(VS Code\)\.
- __Essential Extensions:__
	- __Prettier \- Code formatter__ \(__esbenp\.prettier\-vscode__\): Automatically formats code according to project rules \(\.prettierrc\.js\)\. Ensures consistent style\. *Agents must respect Prettier formatting\.*
	- __ESLint__ \(__dbaeumer\.vscode\-eslint__\): Analyzes code for potential errors and style issues based on project rules \(\.eslintrc\.js\)\. Helps catch bugs early and enforce standards\. *Agents must address ESLint errors/warnings\.*
	- __Tailwind CSS IntelliSense__ \(__bradlc\.vscode\-tailwindcss__\): Provides autocompletion, linting, and hover previews for Tailwind classes\. Essential for efficient UI development\.
	- __GitLens — Git supercharged__ \(__eamodio\.gitlens__\): Provides valuable insights into code history, authorship \(blame\), and changes directly within the editor\. Useful for context\.
	- __Prisma__ \(__prisma\.prisma__\): Adds syntax highlighting, formatting, auto\-completion, and diagnostics for the schema\.prisma file\. Crucial for backend/database work\.
	- __Axe Accessibility Linter__ \(__deque\-systems\.vscode\-axe\-linter__\) \(Optional but Recommended\): Scans code for common accessibility issues during development\.
- __Key Settings \(User/Workspace settings\.json\):__
	- "editor\.formatOnSave": true: Ensures Prettier runs automatically on save\.
	- "editor\.codeActionsOnSave": \{ "source\.fixAll\.eslint": true \}: Automatically fixes ESLint issues on save where possible\.
	- "files\.eol": "\\n": Enforces consistent line endings \(LF\)\.
- __Configuration Files:__ Agents must respect the configurations defined in project files like \.prettierrc\.js, \.eslintrc\.js, tsconfig\.json, tailwind\.config\.js, etc\. Do not override these settings unless explicitly tasked\.

## __Local Development Server__

- __Starting:__ Use the command defined in CORE\_ENV\_SETUP\.md \(typically pnpm dev or npm run dev\)\.
- __Accessing:__ Usually available at http://localhost:PORT \(check terminal output for the specific port, often 3000, 5173, etc\.\)\.
- __Hot Reloading:__ Vite/Next\.js provide Hot Module Replacement \(HMR\) for fast updates during development\.
- __Common Issues:__ Port conflicts \(ensure the required port is free\), missing environment variables \(\.env\.local\), dependency issues \(run pnpm install\)\.

## __Running Tests Locally__

- __Command:__ Use the command defined in CORE\_ENV\_SETUP\.md \(typically pnpm test or npm run test\)\.
- __Importance:__ Run tests locally *before* committing or creating a PR to catch issues early\.
- __Types:__ This usually runs unit and integration tests\. E2E tests might require a separate command and setup\.
- __Reference:__ See 10\_Testing\_QA\_Standards\.md for testing strategies\.

## __Local Debugging__

- __Frontend:__ Use Browser Developer Tools \(Console, Sources, Network tabs\) for inspecting elements, logging, setting breakpoints in JavaScript\. React DevTools extension is essential for inspecting component state/props\.
- __Backend \(Node\.js\):__ Use the Node\.js inspector \(node \-\-inspect\-brk\) combined with VS Code's debugger or Chrome DevTools for Node \(chrome://inspect\)\. Set breakpoints directly in VS Code\.
- __Reference:__ See 09\_Error\_Handling\_Debugging\.md for debugging tools and strategies\.

## __Handling Environment Variables__

- __\.env\.local__: Contains secrets and configuration for your *local* machine\. __Never commit this file\.__
- __\.env\.example__: Tracks *which* variables are needed by the project\. It contains placeholder or non\-sensitive default values\.
- __Agent Workflow:__ If an agent needs a *new* environment variable:
	1. The agent should identify the need for the variable\.
	2. The agent should update the \.env\.example file with the new variable name and a placeholder/default value\.
	3. The agent must instruct the *human user* to add the actual secret value to their local \.env\.local file and configure it securely in staging/production environments\. Agents __must not__ handle or store actual secret values\.

## __Containerized Development \(Optional\)__

- __Docker / Dev Containers:__ For maximum consistency, consider using Docker Compose \(docker\-compose\.yml\) to define and run project services \(backend, database, Redis\) locally\. VS Code's Dev Containers feature can use this setup to create a fully containerized development environment, ensuring all developers \(and potentially CI\) use the exact same environment and dependencies\.
- __Reference:__ See 12\_DevOps\_Infrastructure\.md for Docker details\.

