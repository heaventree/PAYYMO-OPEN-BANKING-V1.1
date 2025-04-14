# __Accessibility & Compliance \(WCAG 2\.2 AA \- Technically Expanded\)__

This document outlines standards with technical details and examples to ensure the application meets WCAG 2\.2 Level AA guidelines, minimizing ambiguity for developers and AI agents\.

## __Core Principles \(POUR\)__

1. __Perceivable:__ Information and UI components must be presentable to users in ways they can perceive\.
	- __1\.1 Text Alternatives:__
		- __Requirement:__ Provide text alternatives \(alt attribute\) for any non\-text content \(images\)\. Decorative images should have alt=""\. Complex images \(charts, graphs\) need longer descriptions provided nearby or via aria\-describedby or within the alt text if concise\.
		- __Technical Example \(HTML\):__  
<img src="logo\.png" alt="CompanyName Logo">  
  
<img src="spacer\.gif" alt="">  
  
<figure role="group" aria\-labelledby="chart\-caption">  
  <img src="sales\-chart\.png" alt="Bar chart showing increasing sales over the last 4 quarters\.">  
  <figcaption id="chart\-caption">  
    Sales trend Q1\-Q4 2024\. Q1: $10k, Q2: $15k, Q3: $18k, Q4: $25k\.  
    </figcaption>  
</figure>  

	- __1\.3 Adaptable:__
		- __Requirement:__ Create content that can be presented in different ways \(e\.g\., simpler layout, screen reader\) without losing information or structure\. Use semantic HTML correctly\. Ensure proper heading hierarchy \(h1 only once per page ideally, h2\-h6 nested correctly\)\. Use landmarks \(<nav>, <main>, <aside>, <header>, <footer>\)\.
		- __Technical Example \(HTML Structure\):__  
<body>  
  <header>\.\.\.</header>  
  <nav aria\-label="Main Navigation">\.\.\.</nav>  
  <main>  
    <h1>Page Title</h1>  
    <section aria\-labelledby="section1\-heading">  
      <h2 id="section1\-heading">Section 1</h2>  
      <p>\.\.\.</p>  
      <article>  
        <h3>Article Title</h3>  
      </article>  
    </section>  
    <aside>\.\.\.</aside>  
  </main>  
  <footer>\.\.\.</footer>  
</body>  

	- __1\.4 Distinguishable:__
		- __1\.4\.1 Use of Color:__ Don't use color alone\. Example: Use icons *and* color for error messages, not just red text\. Provide text labels or patterns in charts alongside colors\.
		- __1\.4\.3 Contrast \(Minimum \- AA\):__ 4\.5:1 for normal text, 3:1 for large text \(18pt/24px normal weight, or 14pt/18\.5px bold\)\. Use tools like WebAIM Contrast Checker or browser devtools\. Check text over images/gradients too\.
		- __1\.4\.11 Non\-text Contrast \(AA\):__ 3:1 contrast ratio required for UI component boundaries/states \(e\.g\., input borders, button outlines, checkbox/radio borders, focus indicators\) and essential parts of graphics/icons\.
			- __Technical Example \(CSS \- Focus Indicator\):__  
/\* Ensure focus outline has sufficient contrast with background AND component \*/  
button:focus\-visible \{  
  outline: 2px solid blue; /\* High contrast blue \*/  
  outline\-offset: 2px;  
\}  

		- __1\.4\.13 Content on Hover or Focus \(AA\):__ Tooltips, dropdowns, etc\., appearing on hover/focus must be:
			- __Dismissible:__ User can dismiss without moving hover/focus \(e\.g\., Esc key\)\.
			- __Hoverable:__ Mouse pointer can move over the revealed content without it disappearing\.
			- __Persistent:__ Content remains visible until hover/focus is removed, it's dismissed, or info is no longer valid\.
2. __Operable:__ UI components and navigation must be operable\.
	- __2\.1 Keyboard Accessible:__
		- __2\.1\.1 Keyboard:__ All interactive elements \(links, buttons, form fields, custom controls\) must be focusable and operable using only the keyboard \(typically Tab, Shift\+Tab, Enter, Space, Arrow keys\)\. Avoid creating keyboard traps where focus cannot leave a component\. Custom components need tabindex="0" if not natively focusable\.
		- __2\.1\.4 Character Key Shortcuts:__ If using single\-key shortcuts \(e\.g\., 'j' for next\), provide a mechanism in settings to turn off or remap them, or ensure they only activate when a specific component has focus\.
	- __2\.4 Navigable:__
		- __2\.4\.1 Bypass Blocks:__ Implement a "Skip to main content" link as the first focusable element on the page, visible only on focus\.  
<a href="\#main\-content" class="skip\-link">Skip to main content</a>  
\.\.\.  
<main id="main\-content">\.\.\.</main>  
\`\`\`css  
\.skip\-link \{  
  position: absolute;  
  top: \-40px; /\* Hide off\-screen \*/  
  left: 0;  
  background: \#000;  
  color: white;  
  padding: 8px;  
  z\-index: 100;  
\}  
\.skip\-link:focus \{  
  top: 10px; /\* Make visible on focus \*/  
\}  

		- __2\.4\.3 Focus Order:__ Ensure the order in which elements receive focus via Tab key is logical and follows the visual layout\. Check DOM order or use tabindex carefully \(avoid positive values > 0\)\.
		- __2\.4\.4 Link Purpose \(In Context\):__ Link text should clearly describe the destination\. Avoid generic text like "Click Here" or "Learn More" unless the surrounding context makes the purpose clear\. Use aria\-label for clarification if necessary\.  
<a href="/reports/annual\-2024\.pdf">Download Annual Report 2024 \(PDF\)</a>  
  
<p>Read the latest news\. <a href="/news/latest">Learn More</a></p>  
  
<p>Item 1 <a href="/items/1/details" aria\-label="View details for Item 1">Details</a></p>  

		- __2\.4\.7 Focus Visible:__ The keyboard focus indicator must be clearly visible and meet contrast requirements \(1\.4\.11\)\. Use :focus\-visible for styling to avoid showing outlines on mouse clicks for elements that support it\.
		- __2\.4\.11 Focus Not Obscured \(Minimum \- AA \- WCAG 2\.2\):__ When an element receives focus, it must not be entirely hidden by other content \(e\.g\., sticky headers/footers, non\-dismissed dialogs\)\.
	- __2\.5 Input Modalities:__
		- __2\.5\.3 Label in Name \(AA\):__ If a button has visible text "Save", its aria\-label \(if used\) must include "Save"\. Don't use aria\-label to *replace* the visible label if it causes a mismatch\.
		- __2\.5\.7 Dragging Movements \(AA \- WCAG 2\.2\):__ If functionality relies on dragging \(e\.g\., sliders, drag\-and\-drop reordering\), provide a simple pointer alternative \(e\.g\., buttons for up/down/move, input field for slider value\)\.
		- __2\.5\.8 Target Size \(Minimum \- AA \- WCAG 2\.2\):__ Interactive targets need to be at least 24x24 CSS pixels in size, OR have sufficient spacing around them to prevent accidental activation\. This applies even to targets within text\.
3. __Understandable:__ Information and the operation of the UI must be understandable\.
	- __3\.2 Predictable:__
		- __3\.2\.6 Consistent Help \(A \- WCAG 2\.2\):__ If help mechanisms \(contact info, help links, chat bots\) are provided, they should appear consistently across pages \(e\.g\., always in the footer or header\)\.
	- __3\.3 Input Assistance:__
		- __3\.3\.1 Error Identification:__ Clearly identify errors using text, icons, and appropriate ARIA \(aria\-invalid="true"\)\. Associate error messages with inputs using aria\-describedby\.  
<label for="email">Email:</label>  
<input type="email" id="email" name="email" aria\-invalid="true" aria\-describedby="email\-error">  
<span id="email\-error" class="error\-message">Please enter a valid email address\.</span>  

		- __3\.3\.2 Labels or Instructions:__ All form controls need clear, associated labels \(<label for="\.\.\.">\)\. Provide instructions for complex inputs where needed\.
		- __3\.3\.7 Redundant Entry \(A \- WCAG 2\.2\):__ In multi\-step processes within the same session, avoid asking for the same information twice \(e\.g\., shipping and billing address if identical\), unless essential for security or legality\. Allow users to indicate "same as\.\.\."
		- __3\.3\.8 Accessible Authentication \(Minimum \- AA \- WCAG 2\.2\):__ Cognitive tests \(like solving puzzles, memorization tasks, transcription\) should not be the *sole* method for authentication\. Provide alternatives \(e\.g\., email link, OTP\) and allow password manager support \(autocomplete attributes\)\.
4. __Robust:__ Content must be robust enough that it can be interpreted reliably by assistive technologies\.
	- __4\.1 Compatible:__
		- __4\.1\.1 Parsing:__ Ensure valid HTML \(no duplicate IDs, proper nesting, start/end tags\)\. Use HTML validators\.
		- __4\.1\.2 Name, Role, Value:__ Use native HTML elements where possible \(they have built\-in roles/states\)\. For custom components \(e\.g\., built with divs\), use ARIA roles \(role="button", role="checkbox"\), states \(aria\-checked, aria\-expanded\), and properties \(aria\-label, aria\-labelledby\) correctly\. Ensure state changes are communicated \(e\.g\., changing aria\-expanded when an accordion opens\)\.
		- __4\.1\.3 Status Messages:__ Use role="status" or aria\-live="polite" \(for less urgent updates\) or aria\-live="assertive" \(for urgent updates, use sparingly\) to announce dynamic content changes \(e\.g\., "Item added to cart", "Search results updated", "Form submitted successfully"\) to screen readers without shifting focus\.  
<div role="status" aria\-live="polite" id="status\-message">  
  \{/\* Content updated dynamically via JS \*/\}  
  \{message\}  
</div>  


## __Key ARIA Roles & Properties \(Examples\)__

- __role="alert"__: For important, time\-sensitive messages \(often used with aria\-live="assertive"\)\.
- __role="dialog"__: For modal dialogs\. Use with aria\-modal="true", aria\-labelledby \(pointing to dialog title\), and aria\-describedby \(pointing to dialog description\)\. Requires focus trapping\.
- __role="tablist"__, __role="tab"__, __role="tabpanel"__: For tabbed interfaces\. Manage aria\-selected state on tabs and hidden attribute on tab panels\. Requires keyboard navigation \(arrow keys\)\.
- __aria\-live="polite"__ / __"assertive"__: Announces dynamic content changes\. Polite waits for a pause; assertive interrupts\.
- __aria\-labelledby__ / __aria\-describedby__: Associates elements with their labels or descriptions programmatically when for/id isn't sufficient\.
- __aria\-invalid="true"__: Indicates an input field has an error\.
- __aria\-required="true"__: Indicates a form field is required\.
- __aria\-expanded="true/false"__: Indicates if a collapsible element \(menu, accordion\) is open or closed\.
- __aria\-current="page"__ / __"step"__ / __"true"__: Indicates the current item within a set \(e\.g\., current page in navigation, current step in a process\)\.

## __Focus Management Techniques__

- __Modals:__ When a modal \(role="dialog", aria\-modal="true"\) opens:
	- Move focus to the first focusable element inside the modal\.
	- Trap Tab key focus within the modal \(cannot tab outside\)\.
	- Restore focus to the element that opened the modal when it closes\.
- __SPAs:__ On route changes, manage focus appropriately\. Often best to move focus to the main content area's heading \(h1\) or the main container \(<main>\)\.
- __Dynamic Content:__ When new interactive content appears \(e\.g\., error messages, search results\), consider moving focus to it *if* it's the logical next step for the user, or announce it using aria\-live\.

## __Common Pitfalls__

- __Incorrect ARIA Usage:__ Using role="button" on a link \(<a>\), missing required ARIA attributes for complex roles \(like tablist\), incorrect aria\-live usage\. Use native elements first\.
- __Poor Focus Management:__ Focus lost on dynamic updates, focus traps not implemented for modals, non\-visible focus indicators\.
- __Relying on Color Alone:__ For status, links, errors, etc\.
- __Vague Link Text:__ "Click Here", "Learn More"\.
- __Ignoring Keyboard Navigation:__ Assuming mouse\-only interaction\.
- __Insufficient Contrast:__ Especially on disabled elements, placeholders, or non\-text elements\.

## __Automated Audit Tools__

- __Browser Extensions:__ Axe DevTools, WAVE \- Use during development for quick checks\.
- __CI/CD Integration:__ Lighthouse \(includes accessibility checks\), Axe\-core \(@axe\-core/react for React components, jest\-axe for unit tests\)\. Integrate these into your test suite and CI pipeline to catch regressions automatically\.
	- __Example \(jest\-axe\):__  
import \{ render \} from '@testing\-library/react';  
import \{ axe, toHaveNoViolations \} from 'jest\-axe';  
import MyComponent from '\./MyComponent';  
  
expect\.extend\(toHaveNoViolations\);  
  
it\('should have no axe violations', async \(\) => \{  
  const \{ container \} = render\(<MyComponent />\);  
  const results = await axe\(container\);  
  expect\(results\)\.toHaveNoViolations\(\);  
\}\);  

- __Linters:__ eslint\-plugin\-jsx\-a11y \- Catches potential issues in JSX during development\.

## __Manual Testing \(Essential\)__

- __Keyboard Navigation:__ Can you reach and operate *everything* with Tab, Shift\+Tab, Enter, Space, Arrows? Is the focus order logical? Is the focus indicator visible?
- __Screen Reader Testing:__ Test key flows with NVDA/VoiceOver/TalkBack\. Are labels read correctly? Is dynamic content announced? Can custom controls be understood and operated?
- __Zoom/Magnification:__ Zoom to 200%\. Does content reflow? Is anything cut off or obscured?
- __Contrast Check:__ Use browser devtools or extensions to check text and non\-text contrast\.

