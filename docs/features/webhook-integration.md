# Webhook Integration

DiPeO provides webhook integration for sending HTTP requests to external services and receiving webhooks from external providers.

## Overview

DiPeO supports two webhook capabilities:

1. **Receiving Webhooks**: External services send webhooks to DiPeO's HTTP endpoint
2. **Sending Webhooks**: Diagrams send HTTP requests to external endpoints via hook nodes

## Architecture

### Components

1. **Webhook Gateway** (`/webhooks/{provider}`): HTTP endpoint receiving webhooks from external services
2. **Event Bus**: Distributes webhook events internally
3. **Hook Node**: Sends HTTP requests to webhook endpoints
4. **Provider Registry**: Manages webhook configurations per provider

### Event Flow

```
External Service → Webhook Gateway → Validate → Normalize → Event Bus → Hook Node → Diagram Execution
```

## Setting Up Webhook Reception

### 1. Configure Provider Manifest

Add webhook event definitions to your provider's manifest:

```yaml
# integrations/github/provider.yaml
name: github
version: 1.0.0
base_url: https://api.github.com

webhook_events:
  - name: push
    description: Repository push event
    payload_schema: schema://github.push.json
    example_payload:
      repository:
        full_name: "user/repo"
      pusher:
        name: "developer"
      
  - name: pull_request
    description: Pull request event
    payload_schema: schema://github.pr.json

metadata:
  webhook_config:
    signature_header: X-Hub-Signature-256
    signature_algorithm: hmac_sha256
    secret: "{{env.GITHUB_WEBHOOK_SECRET}}"
```

### 2. Configure Webhook URL

Point your external service to:
```
https://your-dipeo-server.com/webhooks/{provider}
```

For example:
- GitHub: `https://your-dipeo-server.com/webhooks/github`
- Slack: `https://your-dipeo-server.com/webhooks/slack`
- Stripe: `https://your-dipeo-server.com/webhooks/stripe`

## Using Webhooks in Diagrams

### Sending Outgoing Webhooks

Use the `hook` node to send HTTP requests to external webhook endpoints:

```yaml
- label: Send Webhook
  type: hook
  props:
    hook_type: webhook
    config:
      url: https://api.example.com/webhook
      method: POST  # Optional: default is POST
      headers:  # Optional: custom headers
        X-Custom-Header: value
      timeout: 30  # Optional: request timeout in seconds
```

### Processing Webhook Responses

Webhook responses are available to downstream nodes:

```yaml
- label: Process Response
  type: code_job
  props:
    code: |
      # webhook_response contains the response from the webhook
      status = webhook_response.get('status', 'unknown')
      result = f"Webhook returned: {status}"
```

### Complete Example

```yaml
version: light

nodes:
  - label: Start
    type: start

  - label: Prepare Payload
    type: code_job
    props:
      code: |
        payload_data = {
          "event": "deployment_complete",
          "service": "api-server",
          "version": "1.2.3"
        }

  - label: Send Notification
    type: hook
    props:
      hook_type: webhook
      config:
        url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
        method: POST
        timeout: 15

  - label: Log Result
    type: code_job
    props:
      code: |
        print(f"Notification sent: {webhook_response}")

  - label: End
    type: endpoint

connections:
  - from: Start
    to: Prepare Payload
  - from: Prepare Payload
    to: Send Notification
    label: payload_data
  - from: Send Notification
    to: Log Result
    label: webhook_response
  - from: Log Result
    to: End
```

## Security

### Signature Validation

DiPeO automatically validates webhook signatures when configured:

```yaml
metadata:
  webhook_config:
    signature_header: X-Slack-Signature  # Header containing signature
    signature_algorithm: hmac_sha256     # Algorithm used
    secret: "{{env.SLACK_WEBHOOK_SECRET}}"  # Shared secret
```

Supported algorithms:
- `hmac_sha256` (Most common - GitHub, Slack, Stripe)

### Best Practices

1. **Always use signature validation** for production webhooks
2. **Set appropriate timeouts** to avoid hanging diagrams
3. **Use filters** to process only relevant events
4. **Store secrets securely** in environment variables
5. **Monitor webhook endpoints** for failures and attacks

## Testing Webhooks

### Test Endpoint

Check webhook configuration:
```bash
curl https://your-server.com/webhooks/github/test
```

Response:
```json
{
  "provider": "github",
  "webhook_support": true,
  "webhook_url": "/webhooks/github",
  "supported_events": [
    {
      "name": "push",
      "description": "Repository push event",
      "has_schema": true
    }
  ],
  "signature_validation": true,
  "signature_header": "X-Hub-Signature-256"
}
```

### Local Testing

Use ngrok or similar for local webhook testing:

```bash
# Start DiPeO server
make dev-server

# In another terminal, expose local server
ngrok http 8000

# Configure external service with ngrok URL
# https://abc123.ngrok.io/webhooks/github
```

## Troubleshooting

### Common Issues

1. **"Provider not found"**: Ensure provider manifest is loaded
2. **"Invalid signature"**: Check webhook secret configuration
3. **"Timeout waiting for webhook"**: Increase timeout or check filters
4. **"Event not received"**: Verify webhook URL and provider configuration

### Debug Mode

Enable debug logging to see webhook processing:

```bash
export DIPEO_LOG_LEVEL=DEBUG
dipeo run webhook_diagram --debug
```

## Advanced Usage

### Conditional Webhook Sending

Send webhooks based on conditions:

```yaml
- label: Check Status
  type: condition
  props:
    condition_type: custom
    expression: deployment_status == 'success'

- label: Send Success Webhook
  type: hook
  props:
    hook_type: webhook
    config:
      url: https://api.example.com/success
connections:
  - from: Check Status_condtrue
    to: Send Success Webhook
```

### Multiple Webhook Endpoints

Send notifications to multiple services:

```yaml
- label: Notify Slack
  type: hook
  props:
    hook_type: webhook
    config:
      url: https://hooks.slack.com/...

- label: Notify Discord
  type: hook
  props:
    hook_type: webhook
    config:
      url: https://discord.com/api/webhooks/...
```

## API Reference

### Webhook Gateway Endpoint

**POST** `/webhooks/{provider}`

Receives webhooks from external providers.

**Headers:**
- Provider-specific signature headers
- `Content-Type: application/json`

**Response:**
```json
{
  "status": "processed",
  "provider": "github",
  "event": "push",
  "execution_id": "webhook-github-1234567890"
}
```

### Hook Node Configuration

**Outgoing Webhook:**

```yaml
type: hook
props:
  hook_type: webhook
  config:
    url: string              # Required: Webhook URL
    method: string           # Optional: HTTP method (default: POST)
    headers: object          # Optional: Additional headers
    timeout: number          # Optional: Request timeout in seconds (default: 30)
```

## See Also

- [Provider SDK Documentation](../projects/code-generation-guide.md)
- [Hook Node Reference](../nodes/hook.md)
- [Event Bus Architecture](../architecture/event-bus.md)
