# Payymo - WHMCS Open Banking & Stripe Integration

![Payymo Logo](generated-icon.png)

Payymo is a comprehensive payment integration for WHMCS that combines the power of Open Banking (via GoCardless) and Stripe to automate payment reconciliation, reduce manual work, and improve cash flow.

## Overview

Payymo connects your WHMCS installation to over 2400 banks via the GoCardless Open Banking API and integrates with Stripe to provide a complete payment reconciliation solution. The system automatically matches incoming bank transactions and Stripe payments with unpaid invoices in WHMCS, saving you hours of manual reconciliation work.

### Key Features

- **Bank Connectivity**: Connect to over 2400 banks across Europe via GoCardless
- **Stripe Integration**: Retrieve and reconcile Stripe payments with WHMCS invoices
- **Automatic Matching**: Advanced algorithm matches transactions to invoices using reference, amount, date, and client information
- **Confidence Scoring**: Each match is assigned a confidence score to help identify reliable matches
- **Manual Review**: Review and approve/reject suggested matches with a simple interface
- **Detailed Reporting**: Get insights into your payment reconciliation process
- **Secure OAuth Flow**: Connect to banks and Stripe using secure OAuth connections
- **WHMCS Admin Interface**: Manage everything from within your WHMCS admin area

## Components

The Payymo integration consists of two main components:

1. **WHMCS Addon Module**: Integrates directly into your WHMCS installation, providing a user interface for managing connections, viewing transactions, and handling matches.

2. **Backend Service**: Python-based Flask application that handles communication with GoCardless and Stripe APIs, stores transaction data, and performs the matching algorithm.

## Use Cases

Payymo is ideal for WHMCS users who:

- Process a high volume of bank transfers or Stripe payments
- Spend significant time manually reconciling payments with invoices
- Want to improve cash flow by quickly identifying and applying payments
- Need a secure and compliant way to connect to customer bank accounts
- Want to offer customers the option to pay directly from their bank account

## Installation & Configuration

For detailed installation instructions, see [INSTALL.md](INSTALL.md).

For a quick setup guide and usage instructions, see [docs/usage_guide.md](docs/usage_guide.md).

## API Reference

Detailed API documentation is available in [docs/api_reference.md](docs/api_reference.md).

## Troubleshooting

For common issues and their solutions, see [docs/troubleshooting.md](docs/troubleshooting.md).

## Version History

For a full version history, see [CHANGELOG.md](CHANGELOG.md).

## License

Payymo is licensed software. A valid license key is required for use.

## Support

Need help? Contact our support team:

- Email: support@payymo.com
- Support Portal: https://support.payymo.com