# __CORE TECH STACK \(Added Key Tools & Concepts\)__

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
- __Lucide Icons \(lucide\-react\)__: Clean & consistent SVG icon library\. *\(Why: Provides a wide range of easily customizable icons\)\.*
- __Testing Tools:__ Jest/Vitest \+ React Testing Library \(Unit/Integration\), Cypress/Playwright \(E2E\)\. *\(Why: Ensures component correctness and validates critical user flows\. See 10\_Testing\_QA\_Standards\.md\)\.*

## __Backend Stack__

- __Fastify or Express__: Minimal HTTP server framework \(Node\.js\)\. *\(Why: Fastify for performance, Express for simplicity/ecosystem; choice depends on specific needs\)\.*
- __PostgreSQL \(v15\+\) \+ Prisma__: Strong relational backend with type\-safe querying\. *\(Why: PostgreSQL for reliability/features, Prisma for excellent DX and type safety\)\.*
- __Redis__: Session caching and background job queue \(BullMQ\)\. *\(Why: Fast in\-memory store for caching and managing background job state\)\.*
- __Supabase / AWS S3__: Scalable object \+ blob storage\. *\(Why: Managed, scalable solutions for file storage\)\.*
- __WebSockets__: Real\-time presence and sync \(Liveblocks/Socket\.io\)\. *\(Why: Enables real\-time features like collaboration and notifications\)\.*
- __API Documentation:__ OpenAPI \(Swagger\) specification generated via framework plugins or tools like swagger\-jsdoc\. *\(Why: Essential for clear API contracts for frontend, third parties, and AI agents\. See 14\_Third\_Party\_Integrations\.md\)\.*
- __Testing Tools:__ Jest/Vitest \(Unit/Integration\), Supertest \(API Integration\)\. *\(Why: Validates backend logic and API endpoint behavior\. See 10\_Testing\_QA\_Standards\.md & Backend\_Development\_Patterns\.md\)\.*

## __AI & Automation__

- __Primary LLMs:__ OpenAI GPT series \(ChatGPT API\), Google Gemini API\.
- __Fallback/Alternative LLMs:__ Deepseek models, Anthropic Claude series, locally\-run models via Ollama \(cost\-effective, offline capability\)\. *\(Selection depends on cost, performance, and specific task requirements\)\.*
- __Specialized Models:__ OpenAI Whisper API \(Audio\-to\-Text\)\.
- __Vector Databases \(Optional\):__ Pinecone, Weaviate, pgvector \(Postgres extension\)\. *\(Why: For efficient similarity search needed in advanced RAG or memory systems for AI\)\.*
- __Conceptual Tooling:__ AI Debugger \(memory log \+ fixer\), WCAG Auditor AI\.
- __Memory/Context Management:__ *\(Note: Effective AI agent operation relies on robust memory/context management strategies, potentially using enhanced libraries, vector databases, or custom context window management techniques detailed in AI\_AGENT\_GUIDELINES\.md and 15\_Project\_Management\_Documentation\.md\)\.*

## __DevOps / Infrastructure__

- __GitHub Actions__: CI pipeline with testing and linting\. *\(Why: Integrated with GitHub, good free tier, widely used\)\.*
- __Docker__: Unified dev/test/prod containerization\. *\(Why: Consistent environments, simplifies deployment\)\.*
- __Vercel / Netlify / Render / Fly\.io__: Deployment targets \(PaaS\)\. *\(Why: Platform\-as\-a\-Service options simplifying deployment and scaling\)\.*
- __Sentry \+ PostHog__: Error tracking, session replays\. *\(Why: Comprehensive monitoring and debugging tools\)\.*
- __Cloudflare__: Edge caching \+ CDN routing\. *\(Why: Performance improvements, security features\)\.*
- __Node\.js \(v18\.17\.0 LTS or later\)__: JavaScript runtime\.
- __pnpm \(v8\+\) or npm \(v9\+\)__: Package manager\. *\(Why: pnpm preferred for speed and efficient disk usage\)\.*
	- *\(Ensuring linters like ESLint, formatters like Prettier, icon/gradient generators, and any project\-specific tooling are installed via package manager \(pnpm install\) and configured early \(eslintrc\.js, prettierrc\.js, etc\.\) is crucial for code consistency and preventing UI/design issues\. Refer to 19\_Developer\_Environment\_Setup\.md\)*\.
- __Docker \(latest stable\)__: \(Optional, for DB and API testing\)\.
- __GitHub CLI \(gh\)__: Command\-line interface for GitHub\.
- __Infrastructure as Code \(IaC\) \(Optional\):__ Terraform, Pulumi, AWS CDK\. *\(Why: Manages cloud infrastructure programmatically for consistency and repeatability\)\.*
- __Container Orchestration \(Optional\):__ Kubernetes \(EKS, GKE, AKS\), Docker Swarm\. *\(Why: For managing containerized applications at scale, offering high availability and complex deployment strategies\)\.*
- __Observability \(Optional\):__ OpenTelemetry \(for tracing\), ELK Stack/Loki\+Grafana \(for logging aggregation beyond basic services\)\. *\(Why: Provides deeper insights into distributed systems performance and behavior\)\.*

## __Integrations__

- __Stripe \(Connect\)__: Subscription \+ marketplace billing\.
- __IMAP/SMTP__: Bi\-directional email integration \(using services like SendGrid/Mailgun recommended\)\.
- __Zapier / Make / ClickUp / Boost\.space__: Workflow automations \(via Core Application API\)\.
- __20i API__: Hosting setup via reseller automation \(Example\)\.

