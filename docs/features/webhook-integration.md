# Webhook Integration Guide

This guide explains how to use DiPeO's webhook integration feature to receive and process webhooks from external providers.

## Overview

DiPeO supports two webhook-related capabilities:

1. **Receiving Webhooks**: External services can send webhooks to DiPeO, which are then processed as events
2. **Subscribing to Webhooks**: Diagrams can subscribe to webhook events and trigger workflows

## Architecture

### Components

1. **Webhook Gateway** (`/webhooks/{provider}`): HTTP endpoint that receives webhooks
2. **Event Bus**: Distributes webhook events to subscribers
3. **Hook Node**: Subscribe to or send webhook events in diagrams
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

### Subscribing to Webhook Events

Use the `hook` node with webhook subscription configuration:

```yaml
- label: Wait for GitHub Push
  type: hook
  props:
    hook_type: webhook
    config:
      subscribe_to:
        provider: github
        event_name: push
        timeout: 300  # Wait up to 5 minutes
        filters:
          repository: "myorg/myrepo"  # Optional: filter specific events
```

### Processing Webhook Data

The webhook payload is available to downstream nodes:

```yaml
- label: Process Push Event
  type: person_job
  props:
    person_job_config:
      person: Assistant
      prompt: |
        A GitHub push event was received:
        Repository: {{payload.repository.full_name}}
        Commit: {{payload.head_commit.message}}
        Author: {{payload.pusher.name}}
        
        Generate a summary of the changes.
```

### Complete Example

```yaml
name: github_webhook_processor
description: Process GitHub webhook events

nodes:
  - label: start
    type: start

  - label: Subscribe to GitHub Events
    type: hook
    props:
      hook_type: webhook
      config:
        subscribe_to:
          provider: github
          event_name: push
          timeout: 600
    connections:
      - to: Analyze Changes

  - label: Analyze Changes
    type: person_job
    props:
      person_job_config:
        person: CodeReviewer
        prompt: |
          Review the following GitHub push:
          {{payload}}
          
          Identify:
          1. Critical changes
          2. Potential issues
          3. Suggested actions
    connections:
      - to: Notify Team

  - label: Notify Team
    type: integrated_api
    props:
      provider: slack
      operation: post_message
      config:
        channel: "#dev-team"
        text: "Code review completed for {{payload.repository.full_name}}"
    connections:
      - to: end

  - label: end
    type: end
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

### Custom Event Processing

For complex webhook logic, combine with other nodes:

```yaml
- label: Webhook Router
  type: condition
  props:
    condition: "payload.event_type == 'issue_opened'"
  connections:
    - to: Process Issue
      condition: true
    - to: Process Other
      condition: false
```

### Parallel Webhook Processing

Process multiple webhook sources simultaneously:

```yaml
- label: GitHub Webhook
  type: hook
  props:
    hook_type: webhook
    config:
      subscribe_to:
        provider: github

- label: Slack Webhook
  type: hook
  props:
    hook_type: webhook
    config:
      subscribe_to:
        provider: slack

# Both can run in parallel and merge later
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

**Webhook Subscription Mode:**

```yaml
type: hook
props:
  hook_type: webhook
  config:
    subscribe_to:
      provider: string        # Required: Provider name
      event_name: string      # Optional: Specific event to wait for
      timeout: number         # Optional: Timeout in seconds (default: 60)
      filters: object         # Optional: Key-value filters for payload
```

**Outgoing Webhook Mode:**

```yaml
type: hook
props:
  hook_type: webhook
  config:
    url: string              # Required: Webhook URL
    method: string           # Optional: HTTP method (default: POST)
    headers: object          # Optional: Additional headers
    timeout: number          # Optional: Request timeout
```

## See Also

- [Provider SDK Documentation](../projects/code-generation-guide.md)
- [Hook Node Reference](../nodes/hook.md)
- [Event Bus Architecture](../architecture/event-bus.md)
