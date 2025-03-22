# Payymo - WHMCS Open Banking & Stripe Integration

## Overview

Payymo is a comprehensive financial integration platform for WHMCS that connects to approximately 2400 banks via the GoCardless Open Banking API and integrates with Stripe for payment processing. This solution enables automated payment processing, invoice detection, and transaction matching for WHMCS-powered businesses.

## Key Features

- **Open Banking Integration**: Connect to thousands of banks across Europe through the GoCardless API
- **Stripe Integration**: Process payments and retrieve transaction data from Stripe
- **Automated Invoice Matching**: Intelligently match incoming bank transactions to unpaid invoices
- **Secure Bank Connections**: OAuth-based secure connections to banking APIs
- **Real-time Transaction Syncing**: Keep your financial data up-to-date automatically
- **Transaction Reconciliation**: Simplify accounting with automatic reconciliation
- **Seamless WHMCS Integration**: Works within your existing WHMCS installation
- **Comprehensive Dashboard**: Monitor all financial connections in one place

## Components

This package contains two main components:

1. **WHMCS Module**: The addon module that integrates directly with your WHMCS installation
2. **Backend Service**: A Flask-based Python service that handles API communication and data processing

## Installation

Please refer to the included `INSTALL.md` file for detailed installation instructions.

Quick start:
1. Install the WHMCS module in your WHMCS installation
2. Set up the backend service using the included `install_backend.sh` script
3. Configure your connections in the WHMCS admin area

## Documentation

Complete documentation is available in the `docs` directory, covering:
- Installation and configuration
- Usage guides
- API reference
- Troubleshooting

## Support

For technical support, please contact support@payymo.com or visit our support portal at https://support.payymo.com.

## License

This software is licensed according to the terms of your service agreement. Unauthorized distribution is prohibited.