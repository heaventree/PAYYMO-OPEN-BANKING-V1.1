# __Form Engine & Management \(Updated\)__

## __Form Builder Design__

- Forms stored as JSON schema defining fields, labels, types, validation, and logic\.
- __Field Types:__ text, email, password, textarea, dropdown, radio, checkbox, date, number, file upload, rich text editor, address block, repeater section, etc\.
- Each field definition includes attributes like id, type, label, placeholder, required, defaultValue, options \(for selects/radios\), validationRules \(e\.g\., minLength, pattern\), conditionalLogic\.  
__Simple Example:__  
\{  
  "id": "email",  
  "type": "email",  
  "label": "Email Address",  
  "required": true,  
  "defaultValue": "",  
  "placeholder": "Enter your email",  
  "validationRules": \{  
    "isEmail": true  
  \}  
\}  
  
__More Complex Example \(Nested Fields & Arrays\):__  
\[  
  \{  
    "id": "fullName",  
    "type": "text",  
    "label": "Full Name",  
    "required": true  
  \},  
  \{  
    "id": "contactPreference",  
    "type": "radio",  
    "label": "Preferred Contact Method",  
    "options": \["Email", "Phone"\],  
    "defaultValue": "Email"  
  \},  
  \{  
    "id": "address",  
    "type": "addressBlock", // Custom composite field type  
    "label": "Mailing Address",  
    "required": true,  
    "fields": \[ // Nested fields within the block  
      \{ "id": "street", "type": "text", "label": "Street" \},  
      \{ "id": "city", "type": "text", "label": "City" \},  
      \{ "id": "zip", "type": "text", "label": "Zip Code", "validationRules": \{ "pattern": "^\\\\d\{5\}$" \} \}  
    \]  
  \},  
  \{  
    "id": "phoneNumbers",  
    "type": "repeater", // Allows adding multiple sets of fields  
    "label": "Phone Numbers",  
    "minItems": 0,  
    "maxItems": 3,  
    "itemSchema": \[ // Schema for each repeated item  
       \{ "id": "type", "type": "dropdown", "label": "Type", "options": \["Mobile", "Home", "Work"\] \},  
       \{ "id": "number", "type": "tel", "label": "Number" \}  
    \]  
  \}  
\]  


## __Draft & Autosave Support__

- LocalForage\-backed storage of partial form data\.
- Form state autosaved every 5\-10 seconds or on field blur\.

## __Form Schema Versioning__

- Git\-style diffing between form schema versions stored in the database or version control\.
- Changeset viewer UI to highlight new, removed, or modified fields between versions\.

## __Conditional Logic Engine__

- Define rules to show/hide fields or sections based on other field values\.
- Supports conditions like: “If field\-x = 'value\-y', THEN show field\-z”\.
- Supports multiple conditions with AND/OR grouping\.
- Logic can be defined within the field schema itself\.  
__Example Conditional Logic Representation:__  
\{  
  "id": "otherFeedback",  
  "type": "textarea",  
  "label": "Other Feedback",  
  "conditionalLogic": \{  
    "action": "show", // or "hide"  
    "conditions": \[  
      \{  
        "fieldId": "satisfactionRating",  
        "operator": "lessThan", // equals, notEquals, greaterThan, etc\.  
        "value": 3  
      \}  
    \]  
  \}  
\},  
\{  
   "id": "subscribeNewsletter",  
   "type": "checkbox",  
   "label": "Subscribe to Newsletter?",  
   "conditionalLogic": \{  
       "action": "show",  
       "operator": "AND", // 'OR' also possible  
       "conditions": \[  
           \{ "fieldId": "contactPreference", "operator": "equals", "value": "Email" \},  
           \{ "fieldId": "consentGiven", "operator": "equals", "value": true \}  
       \]  
   \}  
\}  


## __Form Validation__

- Leverage Zod schemas generated from \(or alongside\) the form JSON schema for robust validation on both client \(on blur/submit\) and server\.
- Server\-side validation always re\-validates submitted data against the authoritative schema\.
- Provide clear, inline error messages linked via aria\-describedby\.

## __Submissions__

- Stored as immutable JSON blobs with metadata \(timestamp, user ID, form schema version\)\.
- Option for PDF export of submitted data \(using libraries like pdf\-lib or an API service\)\.
- Secure "resume later" links can include a submission ID and optional expiry\.

## __Accessibility__

- All fields keyboard navigable with clear focus indicators\.
- Proper labeling using <label>, for, id, and aria\-label / aria\-labelledby\.
- Error messages linked correctly using aria\-describedby\.
- Field groups utilize <fieldset> and <legend>\.

