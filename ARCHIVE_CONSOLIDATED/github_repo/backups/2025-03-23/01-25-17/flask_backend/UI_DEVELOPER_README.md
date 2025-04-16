# UI Developer Guidelines for Payymo

## Overview
This document provides guidelines for developing UI components for Payymo, ensuring consistency with the approved design patterns.

## Approved UI Structure
Payymo uses a light-themed, card-based layout that matches the WHMCS admin interface style. This structure has been approved and should be maintained during all development.

## Template Usage
Always use the provided templates for consistency:

1. **Feature Card Template**: `components/feature_card_template.html`
   - Use this as the base for any new feature components
   - Maintains consistent card styling across the application

2. **Dashboard Layout**: Follow the established hierarchy:
   - Alert cards at top
   - Financial goals section
   - Main content area (transactions, etc.)
   - System health at bottom

## Design Guidelines
1. **Colors**:
   - Use Bootstrap color variables
   - For custom components, reference existing color schemes

2. **Typography**:
   - Use the default Bootstrap font stack
   - Maintain consistent font sizing:
     - Card titles: `.card-title`
     - Section headers: `h5`, `h6`
     - Normal text: Default Bootstrap

3. **Icons**:
   - Use Lucide icons
   - Standard sizing: 
     - Navigation: 18px × 18px
     - In-content: 14px × 14px
     - Feature icons: 24px × 24px

4. **Spacing**:
   - Card padding: Use Bootstrap default `.card-body` padding
   - Between cards: `mb-4`
   - Between elements: Bootstrap spacing utilities

5. **Animations**:
   - Keep animations subtle and purposeful
   - Standard animation duration: 0.3s
   - Hover transitions allowed but subtle

## Adding New Features
When adding new features:

1. Create a new component file in `components/`
2. Use the feature_card_template.html as a base
3. Add the component to the dashboard in the appropriate section
4. Test for mobile responsiveness

## Testing Requirements
Before submitting UI changes:

1. Test across multiple viewport sizes
2. Verify consistency with existing components
3. Check animation performance
4. Validate against the UI standards document

## Important Notes
- DO NOT modify the global layout structure
- DO NOT change the approved color scheme
- DO NOT create new UI patterns without approval
- ALWAYS use the provided templates for new features

Remember: The current UI has been approved and should be maintained as a standard for all new development.