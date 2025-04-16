# __CORE TECH STACK \(Updated\)__

This document provides a comprehensive reference for the technology stack used in the project, covering frontend, backend, AI, DevOps, and integrations\. Specific versions are indicative and should be kept current\.

## __Frontend Stack__

- __React \(v18\.2\+\)__: Composable UI architecture\. *\(Why: Industry standard, large ecosystem, component model\)\.*
- __TypeScript__: Type\-safe dev environment\. *\(Why: Improved code quality, maintainability, catching errors early\)\.*
- __Vite__: Fast build tool with native ESM support\. *\(Why: Significantly faster development server start and HMR than Webpack\)\.*
- __Tailwind CSS__: Utility\-first CSS framework\. *\(Why: Rapid UI development, consistency, avoids CSS file bloat\)\.*
- __PostCSS__: CSS plugin engine \(used with Tailwind\)\. *\(Why: Required by Tailwind, enables future CSS transformations\)\.*
- __Zustand__: Lightweight, scalable state management\. *\(Why: Simple API, minimal boilerplate, good performance\)\.*
- __React Hook Form \+ Zod__: Form management and schema validation\. *\(Why: Performant form handling \(uncontrolled\), powerful schema\-based validation\)\.*
- __Framer Motion__: Declarative animation and interaction layer\. *\(Why: Easy\-to\-use API for complex React animations\)\.*
- __DndKit__: Drag\-and\-drop library for low\-level interactions\. *\(Why: Modern, accessible, and performant drag\-and\-drop solution\)\.*

## __Backend Stack__

- __Fastify or Express__: Minimal HTTP server framework \(Node\.js\)\. *\(Why: Fastify for performance, Express for simplicity/ecosystem; choice depends on specific needs\)\.*
- __PostgreSQL \(v15\+\) \+ Prisma__: Strong relational backend with type\-safe querying\. *\(Why: PostgreSQL for reliability/features, Prisma for excellent DX and type safety\)\.*
- __Redis__: Session caching and background job queue \(BullMQ\)\. *\(Why: Fast in\-memory store for caching and managing background job state\)\.*
- __Supabase / AWS S3__: Scalable object \+ blob storage\. *\(Why: Managed, scalable solutions for file storage\)\.*
- __WebSockets__: Real\-time presence and sync \(Liveblocks/Socket\.io\)\. *\(Why: Enables real\-time features like collaboration and notifications\)\.*

## __AI & Automation__

- __OpenAI GPT \(ChatGPT, Whisper\)__: Agent interactions and language understanding\.
- __DeepSeek / Gemini__: AI model fallbacks\.
- __Whisper API__: Audio to text for voice integration\.
- __AI Debugger__: AI memory log \+ fixer toolchain \(Conceptual\)\.
- __WCAG Auditor AI__: Contrast, structure, focus audits \(Conceptual\)\.

## __DevOps / Infrastructure__

- __GitHub Actions__: CI pipeline with testing and linting\. *\(Why: Integrated with GitHub, good free tier, widely used\)\.*
- __Docker__: Unified dev/test/prod containerization\. *\(Why: Consistent environments, simplifies deployment\)\.*
- __Vercel / Netlify / Render / Fly\.io__: Deployment targets\. *\(Why: Platform\-as\-a\-Service options simplifying deployment and scaling\)\.*
- __Sentry \+ PostHog__: Error tracking, session replays\. *\(Why: Comprehensive monitoring and debugging tools\)\.*
- __Cloudflare__: Edge caching \+ CDN routing\. *\(Why: Performance improvements, security features\)\.*
- __Node\.js \(v18\.17\.0 LTS or later\)__: JavaScript runtime\.
- __pnpm \(v8\+\) or npm \(v9\+\)__: Package manager\. *\(Why: pnpm preferred for speed and efficient disk usage\)\.*
- __Docker \(latest stable\)__: \(Optional, for DB and API testing\)\.
- __GitHub CLI \(gh\)__: Command\-line interface for GitHub\.

## __Integrations__

- __Stripe \(Connect\)__: Subscription \+ marketplace billing\.
- __IMAP/SMTP__: Bi\-directional email integration \(using services like SendGrid/Mailgun recommended\)\.
- __Zapier / Make / ClickUp / Boost\.space__: Workflow automations\.
- __20i API__: Hosting setup via reseller automation \(Example\)\.

