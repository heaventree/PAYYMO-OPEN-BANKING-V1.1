# Payymo - WHMCS Open Banking & Stripe Integration

## Installation Guide

This document provides instructions for installing and configuring the Payymo integration for WHMCS, which combines Open Banking (via GoCardless) and Stripe payment processing functionality.

## System Requirements

- WHMCS 8.0 or higher
- PHP 7.4 or higher
- Python 3.8 or higher
- PostgreSQL database
- Web server with mod_rewrite enabled (Apache, Nginx, etc.)
- SSL certificate (required for secure API communication)

## Installation Steps

### 1. WHMCS Module Installation

1. Upload the `modules` folder from this package to your WHMCS root directory, merging with the existing modules folder.
2. Log in to your WHMCS admin area.
3. Navigate to **Setup** > **Addon Modules**.
4. Find "GoCardless Open Banking" in the list and click **Activate**.
5. On the same page, configure the module access control permissions for admin roles.
6. Click **Save Changes**.

### 2. Backend Service Installation

The backend service handles API communication with financial institutions and transaction matching.

1. Set up a Python environment on your server or use a separate hosting service for the backend.
2. Create a PostgreSQL database for the backend service.
3. Copy the `flask_backend` folder to your desired location.
4. Install the required Python dependencies:
   ```
   pip install flask flask-sqlalchemy gunicorn psycopg2-binary requests stripe email-validator
   ```
5. Configure the database connection in environment variables:
   ```
   DATABASE_URL=postgresql://username:password@hostname:port/database
   ```
6. Set up additional environment variables:
   ```
   SESSION_SECRET=your_secure_random_string
   STRIPE_SECRET_KEY=your_stripe_secret_key
   STRIPE_CLIENT_ID=your_stripe_client_id
   ```
7. Start the backend service:
   ```
   gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
   ```
8. Configure your web server to proxy requests to the backend service (recommended).

### 3. Configure the WHMCS Module

1. In your WHMCS admin area, navigate to **Addons** > **GoCardless Open Banking**.
2. Enter your license key (if applicable).
3. Configure the connection to the backend service by specifying the API URL.
4. Save your settings.

### 4. Setting Up Bank Connections

1. Navigate to the **Open Banking** tab in the WHMCS admin area.
2. Click on **Add Bank Connection**.
3. Follow the prompts to connect to your bank account through GoCardless.
4. Once connected, your bank transactions will begin syncing automatically.

### 5. Setting Up Stripe Integration

1. Navigate to the **Stripe Integration** section in the Open Banking module.
2. Click on **Connect Stripe Account**.
3. Follow the OAuth flow to authorize access to your Stripe account.
4. Once connected, Stripe payments will be synchronized for reconciliation.

## Troubleshooting

- Check the module logs in **Utilities** > **System** > **Module Debug Log**.
- Verify that the backend service is running properly.
- Ensure your API credentials are correctly configured.
- Check database connectivity from the backend service.

## Support

For technical support, please contact support@payymo.com or visit our support portal at https://support.payymo.com.

## License

This software is licensed according to the terms of your service agreement. Unauthorized distribution is prohibited.