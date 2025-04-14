# Payymo - Financial Management Platform

A comprehensive financial management platform that combines advanced automation, intelligent payment processing, and user-centric design for seamless financial tracking and optimization.

## Core Technologies

- Flask backend with dynamic templating
- Stripe payment integration
- Open Banking integration via GoCardless
- Multi-service API connectivity
- Bootstrap 5 responsive design
- Chart.js for financial visualizations
- Secure authentication with tenant management
- Interactive dashboard with modular components
- Project management tools for transparent development tracking

## Features

- Multi-tenant architecture for serving multiple clients
- Bank connection management through Open Banking APIs
- Transaction retrieval and categorization
- Reconciliation with payment systems like Stripe
- Comprehensive dashboards for financial monitoring
- Automatic invoice matching and payment processing
- White-labeled client-facing interfaces
- Robust admin controls and permission system

## Project Documentation

All project documentation is organized in the [project_management](./project_management/) directory, including:

- [PLANNING.md](./project_management/PLANNING.md) - Project vision and architecture
- [TASK.md](./project_management/TASK.md) - Current tasks and status
- [ROADMAP.md](./project_management/ROADMAP.md) - Future development plans
- [ISSUES.md](./project_management/ISSUES.md) - Known issues and bugs
- [CHANGELOG.md](./project_management/CHANGELOG.md) - Version history

For a complete overview of all documentation, see the [MASTER_INDEX.md](./project_management/MASTER_INDEX.md).

## Technical Documentation

Technical documentation, API references, and implementation guides are available in the [project_management/technical](./project_management/technical/) directory.

## Getting Started

1. Clone this repository
2. Install required dependencies (`pip install -r requirements.txt`)
3. Set up environment variables (see `.env.example`)
4. Run the application with `python main.py`
5. Access the dashboard at http://localhost:5000

## Development Environment

This project requires Python 3.11+ and the following environment variables:

- `DATABASE_URL`: PostgreSQL database connection URL
- `SESSION_SECRET`: Secret key for Flask sessions
- `GOCARDLESS_CLIENT_ID`: GoCardless API client ID
- `GOCARDLESS_CLIENT_SECRET`: GoCardless API client secret
- `STRIPE_API_KEY`: Stripe API key
- `STRIPE_WEBHOOK_SECRET`: Stripe webhook signing secret

For a complete list, see the [environment setup guide](./project_management/technical/environment_setup.md).

## License

This project is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.