#!/bin/bash
# Payymo Backend Service Installation Script

echo "========================================"
echo "Payymo Backend Service Installation"
echo "========================================"
echo

# Check if Python 3 is installed
if command -v python3 &>/dev/null; then
    python_version=$(python3 --version)
    echo "✓ $python_version detected"
else
    echo "✗ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is installed
if command -v pip3 &>/dev/null; then
    pip_version=$(pip3 --version)
    echo "✓ $pip_version detected"
else
    echo "✗ pip3 not found. Please install pip for Python 3."
    exit 1
fi

# Install required packages
echo
echo "Installing required Python packages..."
pip3 install flask flask-sqlalchemy gunicorn psycopg2-binary requests stripe email-validator

# Check if PostgreSQL is available
if command -v psql &>/dev/null; then
    psql_version=$(psql --version)
    echo "✓ $psql_version detected"
else
    echo "✗ PostgreSQL client not found. Make sure PostgreSQL is installed and properly configured."
fi

# Configure environment
echo
echo "========================================="
echo "Backend Service Configuration"
echo "========================================="
echo
echo "Please provide the following configuration details:"
echo

read -p "PostgreSQL Host [localhost]: " pg_host
pg_host=${pg_host:-localhost}

read -p "PostgreSQL Port [5432]: " pg_port
pg_port=${pg_port:-5432}

read -p "PostgreSQL Database: " pg_db
while [[ -z "$pg_db" ]]; do
    echo "Database name is required."
    read -p "PostgreSQL Database: " pg_db
done

read -p "PostgreSQL Username: " pg_user
while [[ -z "$pg_user" ]]; do
    echo "Username is required."
    read -p "PostgreSQL Username: " pg_user
done

read -sp "PostgreSQL Password: " pg_pass
echo
while [[ -z "$pg_pass" ]]; do
    echo "Password is required."
    read -sp "PostgreSQL Password: " pg_pass
    echo
done

read -p "Session Secret (random string for security): " session_secret
while [[ -z "$session_secret" ]]; do
    session_secret=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 32)
    echo "Generated random session secret: $session_secret"
done

read -p "Stripe Secret Key (optional): " stripe_secret
read -p "Stripe Client ID (optional): " stripe_client_id

# Create environment file
echo
echo "Creating environment configuration file..."
cat > .env << EOL
DATABASE_URL=postgresql://${pg_user}:${pg_pass}@${pg_host}:${pg_port}/${pg_db}
SESSION_SECRET=${session_secret}
STRIPE_SECRET_KEY=${stripe_secret}
STRIPE_CLIENT_ID=${stripe_client_id}
EOL

echo "✓ Environment configuration saved to .env"

# Create a systemd service file
echo
echo "Creating systemd service file..."
cat > payymo-backend.service << EOL
[Unit]
Description=Payymo Backend Service
After=network.target

[Service]
User=$(whoami)
WorkingDirectory=$(pwd)
ExecStart=$(which gunicorn) --bind 0.0.0.0:5000 --reuse-port --reload main:app
Restart=always
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=$(pwd)/.env

[Install]
WantedBy=multi-user.target
EOL

echo "✓ Systemd service file created as payymo-backend.service"
echo
echo "To install the service:"
echo "1. Copy the service file to /etc/systemd/system/"
echo "   sudo cp payymo-backend.service /etc/systemd/system/"
echo
echo "2. Enable and start the service:"
echo "   sudo systemctl enable payymo-backend.service"
echo "   sudo systemctl start payymo-backend.service"
echo
echo "3. Check service status:"
echo "   sudo systemctl status payymo-backend.service"
echo
echo "========================================"
echo "Installation Completed!"
echo "========================================"
echo
echo "Remember to update your WHMCS module configuration to point to this backend service."
echo "Backend URL: http://your-server-ip:5000 (or set up a proxy with your web server)"