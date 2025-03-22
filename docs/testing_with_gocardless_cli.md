# Testing with GoCardless CLI

The GoCardless CLI (`gc-cli`) is a powerful tool for testing the GoCardless API integration without going through the full OAuth flow. This guide explains how to use it with Payymo.

## Installation

To install the GoCardless CLI:

```bash
npm install -g @gocardless/developer-tools
```

Or visit the [GoCardless Developer Tools](https://developer.gocardless.com/developer-tools/gc-cli) page for alternative installation methods.

## Configuration

1. After installation, set up the CLI with your GoCardless credentials:

```bash
gc-cli setup
```

2. When prompted, enter your Client ID and Client Secret from the GoCardless Partner Portal.

## Testing Bank Connections

### 1. List Available Test Banks

```bash
gc-cli open-banking list-banks
```

This shows all available test banks in the GoCardless sandbox.

### 2. Simulate a Bank Connection

```bash
gc-cli open-banking create-requisition \
  --institution-id={BANK_ID} \
  --redirect-url=http://localhost:5000/api/gocardless/callback \
  --reference="Payymo Test Connection"
```

This will initiate a connection with a test bank and provide a link to complete authentication.

### 3. Get Accounts for a Connection

Once a connection is established:

```bash
gc-cli open-banking list-accounts --requisition-id={REQUISITION_ID}
```

### 4. Simulate Transactions

For testing with mock transactions:

```bash
gc-cli open-banking list-transactions \
  --account-id={ACCOUNT_ID} \
  --date-from=2025-01-01 \
  --date-to=2025-03-22
```

## Testing Webhooks

The GoCardless CLI can also simulate webhook events:

```bash
gc-cli webhooks send \
  --url=https://your-payymo-instance.replit.app/api/gocardless/webhook \
  --cert-path=./certs/webhook_cert.pem \
  --key-path=./certs/webhook_key.pem \
  --event-type=transactions.created \
  --payload='{"data": {"id": "tr_123456", "amount": 50.00, "currency": "GBP", "description": "Test Payment"}}'
```

This sends a mock webhook event to your webhook endpoint using your certificates.

## Integration with Payymo's Test Environment

When testing with gc-cli, you can bypass the OAuth flow and directly feed test data into Payymo:

1. Create test transactions using gc-cli
2. Use the Payymo API to manually add these transactions using the included test files:

```bash
# Import test transactions
curl -X POST https://your-payymo-instance.replit.app/api/testing/import-transactions \
  -H "Content-Type: application/json" \
  -d @docs/test-transactions.json

# Simulate a webhook event
curl -X POST https://your-payymo-instance.replit.app/api/testing/simulated-webhook \
  -H "Content-Type: application/json" \
  -d @docs/test-webhook.json
```

We've included sample test files in the `docs` directory:
- `test-transactions.json`: Sample bank transactions for testing
- `test-webhook.json`: Sample webhook event for testing

> Note: Payymo's testing API endpoints are only available in development mode.

## Additional Resources

- [GoCardless Developer Documentation](https://developer.gocardless.com/api-reference)
- [GoCardless CLI GitHub Repository](https://github.com/gocardless/developer-tools)
- [GoCardless Open Banking Sandbox Guide](https://developer.gocardless.com/open-banking/integration-guide/sandbox-testing)