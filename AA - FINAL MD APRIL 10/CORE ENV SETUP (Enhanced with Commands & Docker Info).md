# __CORE ENVIRONMENT SETUP__

This document provides detailed instructions for setting up the developer environment, including prerequisites, setup steps, environment variables, and scripts\.

__\(Refer to CORE\_TECH\_STACK\.md for prerequisite software versions like Node\.js, pnpm/npm, Docker\)__

## __Setup Steps__

1. __Clone the Repository:__  
git clone <repository\-url>  
cd <project\-directory>  

2. __Install Dependencies:__ Use the preferred package manager \(pnpm recommended\)\.  
pnpm install  
  
*\(This installs all dependencies listed in package\.json and pnpm\-lock\.yaml, including development tools like ESLint, Prettier, Vite, etc\.\)*
3. __Configure Environment Variables:__
	- Copy the example environment file:  
cp \.env\.example \.env\.local  

	- Edit \.env\.local and fill in the required secrets and configuration values for your __local machine__\. Obtain necessary API keys or credentials as needed\.
4. __Run Database Migrations \(if applicable\):__ If using Prisma or another ORM with migrations:  
\# Example using Prisma  
pnpm prisma migrate dev  
  
*\(This ensures your local database schema matches the expected structure\)\.*
5. __Seed Database \(Optional\):__ If seed data is available for development:  
\# Example using Prisma  
pnpm prisma db seed  

6. __Start Development Server:__  
pnpm dev  
  
*\(This typically starts the frontend development server \(e\.g\., Vite\) and potentially the backend server concurrently, depending on the project setup\)\.*

## __ENV Keys \(\.env\.local\)__

This file contains environment\-specific variables for your local machine\. __It must NOT be committed to Git\.__ Refer to \.env\.example for the list of required variables\. Examples:

- OPENAI\_API\_KEY= \(Your personal OpenAI key for local testing\)
- STRIPE\_SECRET= \(Stripe Test Mode secret key\)
- SUPABASE\_URL= \(Supabase project URL \- local or cloud dev instance\)
- SUPABASE\_ANON= \(Supabase anon key \- local or cloud dev instance\)
- DATABASE\_URL="postgresql://user:password@host:port/database?schema=public" \(Local database connection string\)
- REDIS\_URL="redis://localhost:6379" \(Local Redis connection string\)

*\(Note: For adding new variables required by the project, update \.env\.example first, then instruct developers to update their \.env\.local\. See 19\_Developer\_Environment\_Setup\.md\)*

## __Local Services & Containerization \(New Section\)__

To ensure consistency across development environments and simplify the setup of dependent services \(like databases, caches\), using Docker is recommended:

- __Docker Compose:__ Utilize a docker\-compose\.yml file in the project root to define and manage local containers for services like PostgreSQL and Redis\.
- __Running Services:__ Start these services with docker\-compose up \-d\.
- __Benefits:__ Provides isolated, reproducible instances of backend services without needing manual installation on the host machine\. Ensures all developers use the same service versions\.
- __\(Optional\) Dev Containers:__ For a fully encapsulated environment, consider using VS Code Dev Containers, which can leverage the docker\-compose\.yml file\.

## __Common Scripts \(package\.json\)__

Refer to the scripts section in package\.json for all available commands\. Standard scripts include:

- dev: Starts the local development server\(s\) with hot reloading\.  
pnpm dev  

- build: Creates an optimized production build of the application\.  
pnpm build  

- start: Runs the production build locally \(after running build\)\.  
pnpm start  

- lint: Runs ESLint and potentially other linters to check code quality\.  
pnpm lint  

- format: Runs Prettier to format code automatically\.  
pnpm format  

- test: Runs unit and integration tests \(e\.g\., using Vitest/Jest\)\.  
pnpm test  

- test:e2e: Runs end\-to\-end tests \(e\.g\., using Cypress/Playwright\)\.  
pnpm test:e2e  

- db:migrate:dev: \(If using Prisma\) Runs database migrations for development\.  
pnpm prisma migrate dev  

- db:seed: \(If using Prisma\) Runs database seeding script\.  
pnpm prisma db seed  


*\(Run scripts using pnpm <script\-name> or npm run <script\-name>\. Consider adding pre\-commit hooks \(e\.g\., with Husky\) to enforce linting/formatting before code is committed\.\)*

