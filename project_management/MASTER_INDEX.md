# Payymo Project Documentation Master Index

This document serves as the central navigation point for all Payymo project documentation, organized by category for easy reference.

## Project Management

- [README.md](./README.md) - Overview of the project management system
- [PLANNING.md](./PLANNING.md) - Project vision, technical architecture, and constraints
- [TASK.md](./TASK.md) - Current tasks, their status, and progress tracking
- [ROADMAP.md](./ROADMAP.md) - Long-term project goals and feature timelines
- [ISSUES.md](./ISSUES.md) - Known issues, bugs, and their resolution status
- [CHANGELOG.md](./CHANGELOG.md) - History of changes to the project
- [AI_AGENT_GUIDELINES.md](./AI_AGENT_GUIDELINES.md) - Guidelines for AI agents working on the project
- [project.index.json](./project.index.json) - Machine-readable project structure

## Development Guidelines

- [md_docs/master_development_guide.md](../md_docs/master_development_guide.md) - Comprehensive development guidelines
- [md_docs/development_guide.md](../md_docs/development_guide.md) - General development practices
- [md_docs/api_reference.md](../md_docs/api_reference.md) - API documentation
- [md_docs/error_handling_guide.md](../md_docs/error_handling_guide.md) - Error handling best practices
- [md_docs/styling_guide.md](../md_docs/styling_guide.md) - CSS and styling standards
- [md_docs/testing_guide.md](../md_docs/testing_guide.md) - Testing procedures and standards

## Integration Documentation

- [md_docs/gocardless_webhooks.md](../md_docs/gocardless_webhooks.md) - GoCardless webhook implementation
- [md_docs/api_troubleshooting_guide.md](../md_docs/api_troubleshooting_guide.md) - Troubleshooting API issues
- [md_docs/testing_with_gocardless_cli.md](../md_docs/testing_with_gocardless_cli.md) - Using GoCardless CLI for testing

## User Documentation

- [md_docs/INSTALL.md](../md_docs/INSTALL.md) - Installation instructions
- [md_docs/usage_guide.md](../md_docs/usage_guide.md) - User guide for the application
- [md_docs/troubleshooting.md](../md_docs/troubleshooting.md) - User-facing troubleshooting guide

## System Documentation

- [md_docs/safety_and_backup_systems.md](../md_docs/safety_and_backup_systems.md) - Backup and recovery procedures
- [md_docs/non_breaking_implementation_guide.md](../md_docs/non_breaking_implementation_guide.md) - Guide for safe implementations

## Updated Guidelines (April 10, 2025)

- [AA - FINAL MD APRIL 10/MASTER INDEX (Updated).md](../AA%20-%20FINAL%20MD%20APRIL%2010/MASTER%20INDEX%20(Updated).md) - Updated master index
- [AA - FINAL MD APRIL 10/15 Project Management & Documentation (Final Enhancements).md](../AA%20-%20FINAL%20MD%20APRIL%2010/15%20Project%20Management%20%26%20Documentation%20(Final%20Enhancements).md) - Enhanced project management guidelines
- [AA - FINAL MD APRIL 10/AI Agent Guidelines (Updated).md](../AA%20-%20FINAL%20MD%20APRIL%2010/AI%20Agent%20Guidelines%20(Updated).md) - Updated AI agent guidelines
- [AA - FINAL MD APRIL 10/CORE CODING STANDARDS (User Revision).md](../AA%20-%20FINAL%20MD%20APRIL%2010/CORE%20CODING%20STANDARDS%20(User%20Revision).md) - Updated coding standards

## Structure of Documentation

The documentation is organized in a hierarchical structure:

1. **Project Management** - Files in the `project_management` directory for tracking tasks, issues, and project progress
2. **Development Guidelines** - Technical standards and practices for developers
3. **Integration Documentation** - Details on external API integrations
4. **User Documentation** - Guides for end users of the application
5. **System Documentation** - Information on system operations and maintenance
6. **Updated Guidelines** - Latest revisions to project standards (April 10, 2025)

## Documentation Conventions

All documentation follows these conventions:

1. **Markdown Format** - All documentation is written in Markdown for consistency
2. **File Naming** - Uppercase for main index files, lowercase with underscores for specific guides
3. **Headers** - Use H1 (#) for document title, H2 (##) for major sections, H3 (###) for subsections
4. **Links** - Use relative paths for internal links to other documentation files
5. **Tables** - Use Markdown tables for structured data
6. **Code Blocks** - Use triple backticks with language specifier for code examples
7. **Task IDs** - Prefix with PM- for project management tasks
8. **Issue IDs** - Prefix with ISSUE- for bug tracking

## How to Update Documentation

When adding or updating documentation:

1. Update the appropriate sectional document
2. Add an entry to CHANGELOG.md if it's a significant change
3. Update this master index if adding new files
4. Verify all links are working
5. Follow the formatting and naming conventions