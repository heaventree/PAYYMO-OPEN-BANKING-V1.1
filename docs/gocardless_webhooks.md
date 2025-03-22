# GoCardless Webhook Integration

This document explains how to set up and use GoCardless webhooks with Payymo.

## Overview

Webhooks allow GoCardless to send real-time notifications to Payymo when events occur, such as:
- New transactions being created
- Bank account details being updated
- Connections being revoked

By implementing webhook support, Payymo can receive updates in real-time rather than having to poll the GoCardless API for changes.

## Setup Requirements

To set up GoCardless webhooks, you'll need:

1. A PEM-encoded TLS client certificate and associated PEM-encoded private key
2. A publicly accessible endpoint for GoCardless to send webhook events to

## Configuration

### Environment Variables

Set the following environment variables to configure webhook support:

```
GOCARDLESS_WEBHOOK_CERT_PATH=/path/to/your/certificate.pem
GOCARDLESS_WEBHOOK_KEY_PATH=/path/to/your/private_key.pem
```

In development mode, certificate verification can be bypassed by setting:

```
FLASK_ENV=development
```

### GoCardless Partner Portal

1. Log in to the [GoCardless Partner Portal](https://developer.gocardless.com/partner-admin/)
2. Navigate to your application settings
3. Add the webhook endpoint URL: `https://your-domain.com/api/gocardless/webhook`
4. Upload your client certificate

## Testing Webhooks

To test webhook functionality:

1. Use GoCardless's webhook testing tool in the Partner Portal
2. Monitor Payymo's logs for webhook processing messages
3. Verify that webhook data is being correctly stored in the database

## Webhook Event Types

Payymo handles the following webhook event types:

| Resource Type | Event Type | Description |
|---------------|------------|-------------|
| transactions  | created    | New transaction has been created |
| accounts      | updated    | Bank account details have been updated |
| connections   | revoked    | Bank connection has been revoked |

## Security Considerations

- Webhook URLs should always use HTTPS
- Client certificate verification should be enabled in production
- Webhook payloads should be validated before processing

## Troubleshooting

If webhooks are not being received:

1. Check that the webhook URL is correctly registered in the GoCardless Partner Portal
2. Verify that the certificate and private key paths are correctly set
3. Check server logs for any webhook processing errors
4. Ensure the webhook endpoint is publicly accessible

If webhooks are received but not processed:

1. Check for certificate validation errors in the logs
2. Verify that the webhook payload format matches what's expected
3. Check for any database errors when storing webhook data