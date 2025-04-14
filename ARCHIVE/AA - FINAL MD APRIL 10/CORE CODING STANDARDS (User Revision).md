# __CORE CODING STANDARDS \(User Revision\)__

This document provides detailed instructions for setting up the developer environment, including prerequisites, setup steps, environment variables, and common scripts\. It is designed to ensure that every developer is working from a consistent baseline and to minimize configuration drift\. \(Refer to CORE\_TECH\_STACK\.md for prerequisite software versions such as Node\.js, pnpm/npm, and Docker\.\)

## __1\. General Coding Principles__

- __Readability & Simplicity__
	- __Clarity Over Cleverness:__ Write clear, concise, and understandable code\. When multiple solutions exist, favor the one that is easiest to read and maintain—even if it is slightly more verbose\.
	- __Modularity:__ Break down complex functions into smaller, single\-purpose units\. Each function should do one thing and do it well\.
- __DRY \(Don't Repeat Yourself\)__
	- __Reusability:__ Encapsulate common logic or values in functions, components, or constants\. Centralize shared code to minimize duplication\.
- __Naming Conventions__
	- __Variables & Functions:__ Use camelCase \(e\.g\., userName, calculateTotal\)\.
	- __Constants:__ Use UPPER\_SNAKE\_CASE for true constants \(values that never change\), especially for globals \(e\.g\., MAX\_RETRIES, DEFAULT\_TIMEOUT\)\. In TypeScript, use readonly to enforce immutability\.
	- __Classes, Interfaces, Types, and Enums:__ Use PascalCase \(e\.g\., UserService, FormSchema, StatusEnum\)\.
	- __Boolean Variables:__ Prefix with is, has, should, or can \(e\.g\., isLoading, hasPermission\)\.
	- __File Naming:__ Follow guidelines in 02\_Directory\_File\_Structure\.md \(e\.g\., PascalCase\.tsx for components, camelCase\.ts for hooks/utilities\)\.
- __Code Comments & Documentation__
	- __Explain Why, Not What:__ Use comments to clarify complex logic or reasoning\. Avoid stating the obvious\.
	- __JSDoc/TSDoc:__ Document functions, classes, and complex logic using the appropriate syntax\. For example:  
/\*\*  
 \* Calculates the total price including tax\.  
 \* @param items \- Array of items with a price property\.  
 \* @param taxRate \- The tax rate \(e\.g\., 0\.08 for 8%\)\.  
 \* @returns The total price including tax\.  
 \* @throws Error if taxRate is negative\.  
 \*/  
function calculateTotalWithTax\(items: Item\[\], taxRate: number\): number \{  
  // \.\.\. implementation \.\.\.  
\}  

	- __TODOs:__ Use // TODO: TASK\-\#\#\#\# comments to mark areas that need future work\.
	- __READMEs:__ Update relevant README\.md files when adding or making significant changes, as outlined in 15\_Project\_Management\_Documentation\.md\.
- __Basic Error Handling Patterns__
	- __Try/Catch:__ Use try\.\.\.catch blocks to capture potential failures, especially in asynchronous operations\.
	- __Error Propagation:__ Propagate errors meaningfully or handle them gracefully\. Avoid silently swallowing errors\.
	- __Standardization:__ Use consistent error object shapes and logging practices across the codebase\. Refer to 09\_Error\_Handling\_Debugging\.md for additional strategies\.
- __Security Considerations__
	- __Input Validation:__ Sanitize user inputs, validate data on backend endpoints, and encode outputs where required\.
	- __Permissions:__ Check user permissions before performing sensitive operations\.
	- __Security Documentation:__ See 13\_Authentication\_Security\.md for deeper guidelines on security best practices\.

## __2\. TypeScript Standards__

- __Strict Mode__
	- __Enabled Strict Options:__ In your tsconfig\.json, ensure strict: true \(or enable individual flags such as strictNullChecks and noImplicitAny\)\. All code must be compatible with strict mode\.
- __Type Definitions__
	- __Explicit Types:__ Define explicit types for function parameters, return values \(especially for exported functions\), and complex data structures\.
	- __Leverage Inference Where Sensible:__ For simple variables with obvious types, rely on TypeScript’s type inference\.
	- __Avoid any:__ Use specific types \(e\.g\., string, number, custom interfaces\) or unknown when necessary\. Conduct proper type checks before using unknown values\.
	- __Centralize Reusable Types:__ Place common types and interfaces in dedicated files \(e\.g\., src/types/\) or co\-locate with features that use them\.
- __Utility Types__
	- __Built\-in Utilities:__ Use utility types such as Partial, Required, Readonly, Pick, and Omit to form new types based on existing ones effectively\.
- __Enums:__
	- Use either TypeScript enum or string literal unions \(e\.g\., type Status = 'pending' | 'completed'\) and favor string\-based enums or unions for improved debuggability\.

## __3\. React Component Standards__

- __Functional Components & Hooks__
	- __Preferred Approach:__ Use functional components combined with React Hooks \(useState, useEffect, useContext, useMemo, useCallback, etc\.\)\. Only use class components for legacy code maintenance\.
- __Props Handling__
	- __Explicit Prop Types:__ Define component prop types using TypeScript interfaces or types\. Choose clear, descriptive prop names and pass only necessary data\.
	- __Avoid Prop Drilling:__ Use patterns like the Context API, Zustand, or component composition to minimize deep prop passing\.
- __State Management__
	- __Local vs\. Global:__ Use local state via useState when possible\. Lift state up or use global state management \(e\.g\., Zustand\) when multiple components share state\. Reference 07\_State\_Management\_Best\_Practices\.md\.
	- __Immutable Updates:__ Always update state immutably\. Use functional updates or spread operators to ensure no side effects\.
- __Component Composition__
	- __Build with Reusability in Mind:__ Compose complex UIs from smaller, well\-defined reusable components rather than relying on complex props or inheritance\.
- __Stable Keys:__
	- Provide stable, unique key props when rendering lists to avoid rendering errors\. Never use array indices as keys if the data order can change\.
- __Accessibility__
	- __Built\-in Accessibility:__ Build accessibility into components from the start by using semantic HTML, proper ARIA attributes, and ensuring keyboard navigability\. See 16\_Accessibility\_Compliance\.md\.

## __4\. Styling Standards \(Tailwind CSS Focus\)__

- __Tailwind CSS Conventions__
	- __Utility\-First Approach:__ Use Tailwind utility classes directly in your JSX\.
	- __Minimize Custom CSS:__ Avoid custom CSS unless absolutely necessary \(e\.g\., for complex animations not covered by utilities\)\.
- __Using @apply:__
	- Use Tailwind’s @apply directive mainly in global styles \(styles/globals\.css\) or within CSS Modules for complex, reusable patterns\. Avoid direct use in component files\.
- __Design Tokens & Consistency__
	- __Configured Scales:__ Adopt Tailwind's predefined spacing and typography scales \(e\.g\., p\-4, mt\-6, text\-heading\-xl\) and avoid arbitrary values \(e\.g\., mt\-\[13px\]\) unless justified\.
	- __Semantic Colors:__ Use semantic class names for colors \(e\.g\., bg\-primary, text\-secondary\) and enforce dark mode via class strategy with WCAG AA contrast compliance\.
- __Responsive Design:__
	- Use responsive modifiers \(sm:, md:, etc\.\) to build mobile\-first designs with Flexbox or Grid layouts\. Avoid fixed pixel widths for layout\.
- __Animations__
	- __Simple Transitions:__ Use Tailwind utilities \(transition, duration\-\*\) for basic animations\.
	- __Complex Animations:__ Implement Framer Motion for advanced interactions \(see 18\_Animation\_Motion\_Guidelines\.md\) while respecting user preferences like prefers\-reduced\-motion\.

## __5\. Do/Don't Examples \(React/Tailwind\)__

- __Do – Good Practices:__  
interface UserCardProps \{  
  user: \{ id: string; name: string; email: string; \};  
\}  
function UserCard\(\{ user \}: UserCardProps\) \{  
  return \(  
    <div key=\{user\.id\} className="p\-4 border border\-default rounded\-md shadow\-sm bg\-card text\-card\-foreground">  
      <h3 className="text\-lg font\-semibold">\{user\.name\}</h3>  
      <p className="text\-sm text\-muted\-foreground">\{user\.email\}</p>  
    </div>  
  \);  
\}  

- __Don't – Practices to Avoid:__  
function BadUserList\(\{ users \}: \{ users: any\[\] \}\) \{ // Avoid using 'any'  
  return \(  
    <div style=\{\{ margin: '15px' \}\}> \{/\* Avoid inline styles & magic numbers \*/\}  
      \{users\.map\(user => \( // Missing key prop\!  
        <div className="user\-card\-manual"> \{/\* Avoid custom CSS in favor of Tailwind utilities \*/\}  
          <h3 style=\{\{ fontSize: '18px' \}\}>\{user\.name\}</h3> \{/\* Avoid inline styles \*/\}  
          <p>\{user\.email\}</p>  
        </div>  
      \)\)\}  
    </div>  
  \);  
\}  


## __6\. SCSS/Custom CSS Rules__

- __Minimize Custom CSS:__ Use custom CSS only when Tailwind cannot achieve the desired effect\.
- __Location and Scoping:__
	- __Global styles:__ Place in styles/globals\.css\.
	- __Modular styles:__ Use CSS Modules \(files ending in \.module\.css\) to scope styles locally\.
- __Avoid \!important:__ Use it sparingly and document the rationale when absolutely necessary \(usually for overriding third\-party styles\)\.
- __CSS Variables:__ Use design tokens defined as CSS variables \(e\.g\., var\(\-\-ds\-color\-primary\)\) to ensure consistency\.

## __7\. AI Agent Adherence & Enforcement \(Mandatory\)__

- __Strict Compliance__
	- __Mandatory Adherence:__ All code—generated by human developers or AI agents—must follow these coding standards and any associated project guidelines \(e\.g\., UI\_\*, Backend\_\*\)\. Prompts must explicitly instruct adherence\.
- __Tooling Integration:__ AI\-generated code must pass all configured tooling:
	- __ESLint:__ Code must pass lint checks \(pnpm lint\)\.
	- __Prettier:__ Code must be formatted according to Prettier \(pnpm format\)\. Agents should ideally format before presenting code\.
	- __TypeScript:__ Code must compile without errors \(tsc \-\-noEmit\)\.
- __Verification Before Commit:__ Before finalizing any code \(such as in a pull request\), run linting, formatting, and type\-checking tools\. Pre\-commit hooks \(configured via Husky, see 10\_Testing\_QA\_Standards\.md\) __must__ automatically enforce these checks\.
- __Continuous Integration:__ Ensure that the CI pipeline includes these validations as part of the automated build process\. Fail builds on violations\.

## __Conclusion__

Adherence to these comprehensive coding standards is essential for building a high\-quality, maintainable, scalable, and secure application\. They provide clear guidelines for both human developers and AI agents, minimizing ambiguity and ensuring consistency across the entire codebase\. Automated tooling enforces these standards, acting as a crucial quality gate throughout the development lifecycle\.

