# Payymo Installation Guide

This document provides detailed instructions for installing both components of the Payymo integration:
1. The WHMCS addon module
2. The backend service

## Prerequisites

### System Requirements
- WHMCS 8.0 or later
- PHP 7.4 or later
- PostgreSQL 12 or later
- Python 3.8 or later
- Web server with SSL (Apache or Nginx recommended)

### Required Services
- GoCardless Open Banking API access (for bank connections)
- Stripe account (for Stripe payment processing)
- Valid Payymo license key

## 1. WHMCS Module Installation

### Step 1: Upload Module Files
1. Extract the module files from the package
2. Upload the contents of the `whmcs_module` directory to your WHMCS root directory
3. Ensure all files are uploaded to the correct locations (see below):

```
modules/addons/gocardless_openbanking/
├── gocardless_openbanking.php
├── hooks.php
├── lib/
│   ├── Admin.php
│   ├── ApiClient.php
│   ├── CronJob.php
│   ├── Database.php
│   ├── Helper.php
│   ├── Invoice.php
│   ├── License.php
│   ├── Logger.php
│   └── Matcher.php
└── templates/
    └── admin/
        ├── configuration.tpl
        ├── license.tpl
        ├── logs.tpl
        ├── matches.tpl
        ├── overview.tpl
        └── transactions.tpl
```

### Step 2: Activate the Module
1. Log in to your WHMCS admin area
2. Navigate to `Setup > Addon Modules`
3. Find "GoCardless Open Banking" in the list
4. Click "Activate"

### Step 3: Configure Module Settings
1. After activation, click "Configure"
2. Enter your Payymo license key
3. Configure the backend service URL (e.g., `https://payymo-backend.yourdomain.com`)
4. Save the settings

## 2. Backend Service Installation

The backend service can be installed in two ways:
- **Option A**: Using the automated installation script (recommended)
- **Option B**: Manual installation

### Option A: Automated Installation

1. Upload the entire `flask_backend` directory to your server
2. Make the installation script executable:
   ```
   chmod +x install_backend.sh
   ```
3. Run the installation script:
   ```
   ./install_backend.sh
   ```
4. Follow the on-screen prompts to complete the installation

### Option B: Manual Installation

#### Step 1: Set Up PostgreSQL Database
1. Create a new PostgreSQL database:
   ```
   sudo -u postgres createuser -P payymo_user
   sudo -u postgres createdb -O payymo_user payymo_db
   ```
2. Note the database connection details for later use

#### Step 2: Install Python Dependencies
1. Create a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install the required packages:
   ```
   pip install -r payymo_requirements.txt
   ```

#### Step 3: Configure Environment Variables
1. Create a `.env` file in the `flask_backend` directory:
   ```
   DATABASE_URL=postgresql://payymo_user:password@localhost:5432/payymo_db
   STRIPE_CLIENT_ID=your_stripe_client_id
   STRIPE_SECRET_KEY=your_stripe_secret_key
   GOCARDLESS_CLIENT_ID=your_gocardless_client_id
   GOCARDLESS_CLIENT_SECRET=your_gocardless_client_secret
   SESSION_SECRET=random_secure_string
   ```

#### Step 4: Set Up the Application as a Service
1. Create a systemd service file:
   ```
   sudo nano /etc/systemd/system/payymo-backend.service
   ```
2. Add the following content:
   ```
   [Unit]
   Description=Payymo Backend Service
   After=network.target postgresql.service

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/flask_backend
   Environment="PATH=/path/to/venv/bin"
   EnvironmentFile=/path/to/flask_backend/.env
   ExecStart=/path/to/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 main:app

   [Install]
   WantedBy=multi-user.target
   ```
3. Enable and start the service:
   ```
   sudo systemctl daemon-reload
   sudo systemctl enable payymo-backend
   sudo systemctl start payymo-backend
   ```

#### Step 5: Configure Web Server (Nginx example)
1. Create a new Nginx site configuration:
   ```
   sudo nano /etc/nginx/sites-available/payymo-backend
   ```
2. Add the following content:
   ```
   server {
       listen 443 ssl;
       server_name payymo-backend.yourdomain.com;

       ssl_certificate /path/to/ssl/certificate.crt;
       ssl_certificate_key /path/to/ssl/private.key;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
3. Enable the site:
   ```
   sudo ln -s /etc/nginx/sites-available/payymo-backend /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

## 3. Testing the Installation

### Verify Backend Service
1. Check that the backend service is running:
   ```
   sudo systemctl status payymo-backend
   ```
2. Test the API endpoint:
   ```
   curl https://payymo-backend.yourdomain.com/api/health-check
   ```
   Should return: `{"status":"ok"}`

### Verify WHMCS Module
1. Log in to your WHMCS admin area
2. Navigate to `Addons > GoCardless Open Banking`
3. You should see the dashboard with no errors
4. Go to Settings and verify that the connection to the backend service is successful

## 4. Configuring OAuth Credentials

### GoCardless Configuration
1. Register a developer account at GoCardless
2. Create a new application
3. Configure the redirect URI: `https://payymo-backend.yourdomain.com/api/gocardless/callback`
4. Copy the Client ID and Client Secret
5. Add these credentials to your `.env` file

### Stripe Configuration
1. Create a Stripe application in the Stripe Dashboard
2. Configure the redirect URI: `https://payymo-backend.yourdomain.com/api/stripe/callback`
3. Copy the Client ID and Secret Key
4. Add these credentials to your `.env` file

## 5. Setting Up Cron Jobs

Create cron jobs to automatically sync transactions and process matches:

```
# Sync transactions every hour
0 * * * * cd /path/to/flask_backend && /path/to/venv/bin/python cron/fetch_transactions.py

# Process matches every 15 minutes
*/15 * * * * cd /path/to/flask_backend && /path/to/venv/bin/python cron/process_matches.py
```

## Troubleshooting

For common issues and their solutions, please refer to the [Troubleshooting Guide](docs/troubleshooting.md).

## Next Steps

After completing the installation, refer to the [Usage Guide](docs/usage_guide.md) for instructions on:
- Connecting bank accounts
- Setting up Stripe integration
- Managing transactions
- Configuring automatic matching rules

## Support

If you encounter any issues during installation, please contact our support team:
- Email: support@payymo.com
- Support Portal: https://support.payymo.com