# Example: Adding a New Node Type to DiPeO

This example demonstrates how development-focused subagents collaborate to add a new node type to DiPeO.

## Scenario
Adding a new "webhook" node type that can send HTTP callbacks during diagram execution.

## Subagent Collaboration Flow

### 1. TypeScript Architect - Design the Model
```typescript
// typescript-architect creates in /dipeo/models/src/node-specs/webhook.ts
export interface WebhookNode extends BaseNode {
  type: 'webhook';
  config: WebhookConfig;
}

export interface WebhookConfig {
  url: string;
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  headers?: Record<string, string>;
  body?: any;
  retry_policy?: RetryPolicy;
  timeout?: number;
}

export interface RetryPolicy {
  max_attempts: number;
  backoff_strategy: 'exponential' | 'linear' | 'fixed';
  initial_delay_ms: number;
}
```

### 2. Codegen Expert - Generate Python Code
```bash
# codegen-expert runs the generation pipeline
cd dipeo/models && pnpm build
make codegen
make diff-staged  # Review changes
make apply-test   # Apply with validation
make graphql-schema  # Update GraphQL
```

### 3. DiPeO Core - Implement Handler
```python
# dipeo-core creates /dipeo/application/execution/handlers/webhook.py
from dipeo.application.execution.handlers.base import BaseNodeHandler
from dipeo.infrastructure.patterns import EnvelopeFactory
import httpx

class WebhookHandler(BaseNodeHandler):
    async def execute(self, context):
        config = context.node.config

        async with httpx.AsyncClient(timeout=config.timeout) as client:
            try:
                response = await self._execute_with_retry(
                    client, config
                )
                return EnvelopeFactory.create_success({
                    'status_code': response.status_code,
                    'body': response.json(),
                    'headers': dict(response.headers)
                })
            except Exception as e:
                return EnvelopeFactory.create_error(str(e))

    async def _execute_with_retry(self, client, config):
        # Implement retry logic based on retry_policy
        pass
```

### 4. Web Developer - Add UI Components
```tsx
// web-developer creates /apps/web/src/components/nodes/WebhookNode.tsx
import React from 'react';
import { Handle, Position } from 'reactflow';
import { WebhookIcon } from '@/icons';

export const WebhookNode: React.FC<NodeProps> = ({ data }) => {
  return (
    <div className="webhook-node">
      <Handle type="target" position={Position.Top} />
      <div className="node-header">
        <WebhookIcon />
        <span>{data.label || 'Webhook'}</span>
      </div>
      <div className="node-config">
        <div className="url">{data.config.method} {data.config.url}</div>
      </div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

// Add to node type registry
export const nodeTypes = {
  webhook: WebhookNode,
  // ... other nodes
};
```

### 5. CLI Engineer - Add CLI Support
```python
# cli-engineer updates CLI to support webhook nodes in Light format
def validate_webhook_node(node_data):
    """Validate webhook node configuration."""
    required = ['url', 'method']
    for field in required:
        if field not in node_data.get('config', {}):
            raise ValueError(f"Webhook node missing required field: {field}")

    valid_methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
    if node_data['config']['method'] not in valid_methods:
        raise ValueError(f"Invalid HTTP method: {node_data['config']['method']}")
```

### 6. DiPeOCC Specialist - Update Conversion
```python
# dipeocc-specialist adds mapping for webhook-like operations
def convert_http_request(tool_call):
    """Convert HTTP request tool calls to webhook nodes."""
    return {
        'type': 'webhook',
        'config': {
            'url': tool_call['parameters']['url'],
            'method': tool_call['parameters'].get('method', 'POST'),
            'headers': tool_call['parameters'].get('headers', {}),
            'body': tool_call['parameters'].get('body'),
            'timeout': 30
        }
    }
```

## Testing the New Node

### Light YAML Example
```yaml
# Created collaboratively by all subagents
id: webhook-test
version: '1.0'
nodes:
  - id: start
    type: start

  - id: prepare_data
    type: person
    config:
      prompt: "Generate test data for webhook"
    needs: [start]

  - id: send_webhook
    type: webhook
    config:
      url: "https://webhook.site/unique-id"
      method: POST
      headers:
        Content-Type: "application/json"
      body: "{{prepare_data.output}}"
      retry_policy:
        max_attempts: 3
        backoff_strategy: exponential
        initial_delay_ms: 1000
    needs: [prepare_data]

  - id: log_response
    type: person
    config:
      prompt: "Log webhook response: {{send_webhook.output}}"
    needs: [send_webhook]
```

## Subagent Coordination Points

1. **TypeScript Architect** → **Codegen Expert**: Model ready for generation
2. **Codegen Expert** → **DiPeO Core**: Generated code ready for handler
3. **DiPeO Core** → **Web Developer**: Handler API defined for UI
4. **Web Developer** → **CLI Engineer**: UI schema for CLI validation
5. **CLI Engineer** → **DiPeOCC Specialist**: Node type for conversion
6. **All** → **Documentation**: Update respective docs

This collaborative approach ensures the new node type is fully integrated across all layers of DiPeO.