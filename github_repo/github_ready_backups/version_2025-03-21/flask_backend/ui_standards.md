# Payymo UI Standards

This document outlines the approved UI design patterns for the Payymo dashboard that should be maintained across all future updates.

## Layout Structure
- **Light Theme** with top navigation bar (WHMCS style compatibility)
- **Container-based Layout** with proper spacing between components
- **Card-based Components** with consistent styling across the application

## Dashboard Organization
1. **Alert Cards** (top) - For transactions/unassigned records
2. **Financial Goals** (middle) - Animated progress bars for key metrics
3. **Transaction Lists** (middle) - Main data tables
4. **System Health** (bottom) - Operational indicators

## Financial Goals Component
- **Animated Progress Bars** - With color transitions and glow effects
- **Card Layout** - Four quadrants showing different metrics
- **Hover Effects** - Subtle elevation on hover
- **Consistent Icons** - arrow-up-right instead of trending-up for compatibility

## Design Elements
- **Typography**: Bootstrap default with specific font weights
- **Colors**: Bootstrap variables with proper contrast
- **Icons**: Lucide icons with fallbacks defined
- **Buttons**: Minimal primary buttons, outline style for secondary actions
- **Spacing**: Consistent margins and padding using Bootstrap utility classes

## Card Structure
- **Header**: Clean with left-aligned title and right-aligned actions
- **Body**: Concise content with appropriate padding
- **Footer**: Visible links/buttons rather than hover overlays

## Animation Guidelines
- **Subtle** - Animations should be subtle and not distract from content
- **Purposeful** - Animations should serve to draw attention to important elements
- **Performance** - Animations should not impact performance

## Future Feature Integration
- New features should be added as discrete card components
- Maintain the overall top-to-bottom information hierarchy
- Alert-style information should always remain towards the top
- Statistics and goals should maintain their relative positions
- System health indicators should remain at the bottom

**DO NOT CHANGE** the overall structure, light theme, or move away from the card-based layout without explicit approval.