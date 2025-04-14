# __Backend Development Patterns__

This document outlines best practices and patterns for backend development using Node\.js \(with Fastify/Express\), Prisma, and PostgreSQL, complementing the core technology stack and other guidelines\.

## __1\. API Design \(RESTful Principles\)__

- __Resource\-Oriented:__ Structure APIs around resources \(e\.g\., /users, /forms, /submissions\)\.
- __Use HTTP Verbs:__
	- GET: Retrieve resources \(list or specific item\)\. Idempotent\.
	- POST: Create new resources\. Not idempotent\.
	- PUT: Replace/update an existing resource entirely\. Idempotent\.
	- PATCH: Partially update an existing resource\. Not idempotent \(usually\)\.
	- DELETE: Remove a resource\. Idempotent\.
- __Endpoint Naming:__ Use plural nouns for resource collections \(e\.g\., /forms, not /getForm\)\. Use IDs for specific resources \(e\.g\., /forms/\{formId\}\)\.
- __Request/Response Structure:__ Use JSON for request and response bodies\. Maintain consistent response structures \(e\.g\., \{ "data": \[\.\.\.\] \} for collections, \{ "data": \{\.\.\.\} \} for single items, \{ "error": \{ "message": "\.\.\.", "code": "\.\.\." \} \} for errors\)\.
- __Status Codes:__ Use appropriate HTTP status codes \(e\.g\., 200 OK, 201 Created, 204 No Content, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 500 Internal Server Error\)\.
- __Versioning:__ Implement API versioning from the start \(e\.g\., /api/v1/users\)\. See 24\_Future\_Proofing\_Scalability\.md\.

## __2\. Controller/Route Structure__

- __Framework Choice:__ Fastify is recommended for performance, but Express is acceptable\.
- __Separation of Concerns:__ Keep route handlers \(controllers\) thin\. Their primary responsibility is to parse requests, call appropriate service functions, and format responses\.
- __Organization:__ Group routes by resource \(e\.g\., src/routes/forms\.ts, src/routes/users\.ts\)\.
- __Validation:__ Use libraries like zod \(with fastify\-type\-provider\-zod for Fastify\) or express\-validator to validate request bodies, query parameters, and path parameters at the route level\.

// Example: Fastify Route Structure \(Conceptual\)  
import \{ FastifyInstance, FastifyRequest, FastifyReply \} from 'fastify';  
import \{ FormService \} from '\.\./services/formService';  
import \{ createFormSchema, getFormSchema \} from '\.\./schemas/formSchemas'; // Zod schemas  
  
async function formRoutes\(fastify: FastifyInstance\) \{  
  const formService = new FormService\(\);  
  
  fastify\.post\(  
    '/forms',  
    \{ schema: \{ body: createFormSchema \} \}, // Request validation  
    async \(request: FastifyRequest<\{ Body: typeof createFormSchema\.\_input \}>, reply: FastifyReply\) => \{  
      try \{  
        // Auth check would happen in middleware/hook  
        const newForm = await formService\.create\(request\.body, request\.user\.id\); // Assuming user ID from auth  
        reply\.code\(201\)\.send\(\{ data: newForm \}\);  
      \} catch \(error\) \{  
        fastify\.log\.error\(error\);  
        reply\.code\(500\)\.send\(\{ error: \{ message: 'Failed to create form' \} \}\);  
      \}  
    \}  
  \);  
  
  fastify\.get\(  
    '/forms/:formId',  
     \{ schema: \{ params: getFormSchema \} \},  
    async \(request: FastifyRequest<\{ Params: typeof getFormSchema\.\_input \}>, reply: FastifyReply\) => \{  
       // \.\.\. call formService\.getById \.\.\.  
    \}  
  \);  
  // \.\.\. other routes \(PUT, DELETE, GET list\)  
\}  
  
export default formRoutes;  


## __3\. Service Layer Pattern__

- __Purpose:__ Encapsulate business logic related to a specific resource or domain\. Controllers call service methods\. Services interact with data repositories \(like Prisma\)\.
- __Benefits:__ Improves code organization, testability \(services can be tested independently of route handlers\), and reusability\.
- __Location:__ src/services/ \(e\.g\., formService\.ts, userService\.ts\)\.
- __Dependency Injection:__ Consider using dependency injection frameworks \(like tsyringe or inversify\) for managing service dependencies, especially in larger applications\.

## __4\. Database Interaction \(Prisma\)__

- __Prisma Client:__ Use the generated Prisma Client for all database interactions\.
- __Schema:__ Define your database schema in prisma/schema\.prisma\. Use Prisma Migrate for schema changes \(11\_Backup\_Recovery\_Safety\.md\)\.
- __Transactions:__ Use Prisma's interactive transactions \($transaction\) for operations that must succeed or fail together\.
- __Query Optimization:__
	- Select only necessary fields using select or include\.
	- Be mindful of N\+1 query problems, especially with nested relations; use include judiciously\.
	- Add database indexes in schema\.prisma for frequently queried columns\.
	- Use Prisma's logging features \(log: \['query'\]\) during development to inspect generated SQL\.
- __Connection Pooling:__ Prisma Client manages connection pooling automatically\. Ensure your serverless environment configuration is compatible \(see Prisma docs on serverless\)\.

## __5\. Error Handling__

- __Centralized Handling:__ Use framework hooks \(Fastify setErrorHandler\) or middleware \(Express error middleware\) for centralized error handling\.
- __Custom Error Classes:__ Define custom error classes \(e\.g\., NotFoundError, ValidationError, UnauthorizedError\) to differentiate error types and map them to appropriate HTTP status codes\.
- __Logging:__ Log errors with context \(request ID, user ID\)\. See 09\_Error\_Handling\_Debugging\.md\.
- __Consistent Responses:__ Return consistent JSON error responses\.

## __6\. Middleware / Hooks__

- __Purpose:__ Handle cross\-cutting concerns like authentication, logging, request parsing, rate limiting, etc\.
- __Fastify:__ Use Hooks \(onRequest, preHandler, etc\.\)\.
- __Express:__ Use Middleware functions\.
- __Order Matters:__ Be mindful of the execution order of middleware/hooks\. Auth checks should typically run early\.

## __7\. Async Operations & Background Jobs__

- __Avoid Blocking:__ Don't perform long\-running operations directly in request handlers\.
- __Job Queues:__ Use a job queue like BullMQ with Redis for tasks like sending emails, processing images/videos, calling slow third\-party APIs, generating reports\.
- __Workflow:__
	1. Request handler receives request\.
	2. Handler adds a job to the queue \(e\.g\., emailQueue\.add\('sendWelcomeEmail', \{ userId \}\)\)\.
	3. Handler immediately returns a response \(e\.g\., 202 Accepted\)\.
	4. Separate worker process picks up the job from the queue and executes it\.
	5. Worker updates job status \(completed/failed\)\. Implement retry logic for failures\.

## __8\. Testing__

- __Unit Tests \(Services\):__ Test service layer logic in isolation\. Mock database interactions \(e\.g\., using prisma\-mock or Jest/Vitest mocking\)\.
- __Integration Tests \(API Endpoints\):__ Test API endpoints by making actual HTTP requests \(e\.g\., using supertest or Fastify's inject\) against a running instance of the application connected to a test database\.
- __Database Seeding:__ Use seed scripts \(e\.g\., Prisma seed\) to populate the test database with consistent data before running integration tests\.
- See 10\_Testing\_QA\_Standards\.md for more details\.

