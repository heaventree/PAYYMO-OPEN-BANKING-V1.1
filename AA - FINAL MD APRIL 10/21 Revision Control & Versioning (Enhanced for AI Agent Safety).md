# __Revision Control & Versioning \(Enhanced for AI Agent Safety\)__

__Core Principle:__ Strict adherence to this Git workflow and versioning strategy is __mandatory__ for all contributors, both human and AI\. It is designed to prevent data loss, maintain a clean history, facilitate collaboration, and enable safe integration of AI\-generated code\. Deviations can lead to significant rework and instability\.

## __Git Workflow: GitFlow \(Simplified\)__

- __main__: Represents the latest __stable, production\-ready__ code\. Only merge *tested* release branches or *critical* hotfixes here\. __Protected branch\.__ Direct pushes forbidden\.
- __develop__: Represents the latest integrated development changes, aiming for the next release\. Feature branches merge into develop via reviewed PRs\. __Protected branch\.__ Direct pushes forbidden\.
- __Feature Branches \(feature/, feat/\):__
	- __Creation:__ ALWAYS branch from the *latest* develop\. \(See "Pre\-Work Steps"\)\.
	- __Purpose:__ Develop new features or non\-trivial changes in isolation\.
	- __Merging:__ Merged back *only* into develop via Pull Requests \(PRs\) after passing all checks and reviews\.
	- __Naming:__ feature/TASK\-ID\-short\-description or feat/TASK\-ID\-short\-description\.
- __Release Branches \(release/\):__
	- __Creation:__ Branched from develop when features for the next release are complete\.
	- __Purpose:__ Final testing, minor bug fixes, documentation updates specific to the release\. No new features added here\.
	- __Merging:__ Merged into main \(tagged\) and *also* back into develop \(to incorporate any release\-specific fixes\)\.
	- __Naming:__ release/vMAJOR\.MINOR\.PATCH \(e\.g\., release/v1\.2\.0\)\.
- __Hotfix Branches \(hotfix/\):__
	- __Creation:__ Branched *directly from main*\.
	- __Purpose:__ Fixing critical, production\-breaking bugs *only*\.
	- __Merging:__ Merged back into main \(tagged\) and *also* back into develop to ensure the fix is in future releases\.
	- __Naming:__ hotfix/TASK\-ID\-fix\-description\.

graph LR  
    subgraph Development Cycle  
        D\(develop\) \-\-\- F1\(feat/A\)  
        D \-\-\- F2\(feat/B\)  
        F1 \-\-> D  
        F2 \-\-> D  
    end  
    subgraph Release Cycle  
        D \-\-> R\(release/v1\.0\)  
        R \-\-> M\(main\)  
        R \-\-> D  
    end  
    subgraph Hotfix Cycle  
        M \-\-> H\(hotfix/bug\)  
        H \-\-> M  
        H \-\-> D  
    end  


## __Pre\-Work Steps for Agents \(Mandatory\)__

Before starting any coding task on a feature/fix branch, AI agents __must__ perform these steps:

1. git checkout develop
2. git pull origin develop \(Ensure local develop is up\-to\-date\)
3. git checkout \-b <new\-branch\-name> \(Create the feature/fix branch using the correct naming convention\)

## __Branch Naming Conventions__

- Use prefixes: feature/, feat/, fix/, bugfix/, release/, hotfix/, docs/, test/, chore/\.
- Include Task ID from the task management system \(e\.g\., project\.index\.json, TASK\.md\) if applicable\.
- Use kebab\-case for descriptions \(e\.g\., feat/TASK\-123\-add\-login\-form\)\.

## __Commit Standards: Conventional Commits__

- __Format:__ <type>\(<scope>\): <subject> \(See previous version for details on type, scope, subject\)\.
- __Commit Frequency:__ Make small, logical commits frequently within the feature branch\. This makes changes easier to understand, review, and revert if necessary\. Avoid large, monolithic commits\.
- __Body/Footer:__ Use the body/footer for more context and linking to issues \(Closes \#\.\.\., Refs \#\.\.\.\)\.
- __Enforcement:__ commitlint \+ Husky hooks __must__ be used to enforce this standard before commits are accepted locally\.

## __Handling Merge Conflicts \(AI Agent Protocol\)__

- __Detection:__ Conflicts may occur when updating a feature branch with the latest develop \(git pull origin develop or git rebase origin/develop\)\.
- __Agent Action:__ If Git reports merge conflicts, the AI agent __must STOP__ execution for the current task\.
- __Reporting:__ The agent must clearly report:
	- That merge conflicts occurred\.
	- Which files have conflicts\.
	- The current task ID\.
- __Resolution:__ __AI agents must NOT attempt to resolve merge conflicts autonomously\.__ Conflict resolution requires human understanding of the competing changes\. A human developer must resolve the conflicts manually\.
- __Continuation:__ Once a human has resolved the conflicts and pushed the changes, the agent can be instructed to continue its task after pulling the resolved code\.

## __Rebasing vs\. Merging__

- __Feature Branches:__ Prefer merging feature branches into develop via GitHub PRs \(creates merge commits, preserving branch history\)\.
- __Updating Feature Branches:__ Developers may choose to use git rebase origin/develop *on their local feature branch* to maintain a cleaner linear history *before* creating a PR, but this requires understanding interactive rebase and force\-pushing *only to their own feature branch*\. __AI agents should generally avoid rebasing unless specifically instructed and supervised for simple cases\.__
- __Force Pushing:__ __NEVER force\-push \(git push \-\-force or git push \-f\) to shared branches \(main, develop\)\.__ Force\-pushing feature branches should only be done with extreme caution after rebasing locally\.

## __Safe Git Commands for Agents \(Examples\)__

- __Expected/Allowed:__ git status, git checkout <branch>, git checkout \-b <new\-branch>, git pull origin <branch>, git fetch origin, git add <file>, git add \., git commit \-m "\.\.\.", git push origin <feature\-branch\-name>, git log, git diff\.
- __Use with Human Supervision/Confirmation:__ git rebase, git merge, git stash, git reset HEAD <file>, git checkout \-\- <file>\.
- __Generally Avoid \(Requires Human Execution\):__ git reset \-\-hard, git push \-\-force, git filter\-branch, git revert <commit> \(unless specifically generating the command for human review\)\.

## __Tags & Releases__

- Use Semantic Versioning \(MAJOR\.MINOR\.PATCH\)\. Increment based on changes \(MAJOR for breaking, MINOR for features, PATCH for fixes\)\.
- Create *annotated* Git tags \(git tag \-a\) for all releases on main\. Include release notes in the tag message\.
- Push tags explicitly \(git push origin \-\-tags\)\.
- Use GitHub Releases for user\-facing release notes, linking to tags and potentially attaching build artifacts\. Automation via conventional\-changelog or semantic\-release is recommended\.

## __Snapshot System \(User Data / Config\)__

- This refers to application\-level backups/versioning \(see 11\_Backup\_Recovery\_Safety\.md\), distinct from Git's code versioning\.

## __Change Logs__

- Maintain CHANGELOG\.md \(Keep a Changelog format\)\.
- Update should be part of the release process or automated via Conventional Commits tooling\.

## __GitHub Actions Integration & Checks__

- __CI Pipeline:__ Runs on PRs to develop/main\. Enforces linting, testing, build success\. __Acts as a critical automated gatekeeper\.__
- __CD Pipeline:__ Triggered on merges to main \(production\) / develop \(staging\)\.
- __Automated Releases \(Optional\):__ Tools like semantic\-release can automate version bumping, tagging, and release creation based on commit messages\.

__\(Link to 15\_Project\_Management\_Documentation\.md\):__ The Pull Request process, including mandatory checks and human review, is detailed in the Project Management guide\. The Deviation Recovery Protocol relies heavily on safe Git usage\.

