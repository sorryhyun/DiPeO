# DiPeO GraphQL Migration Guide

## Overview

DiPeO is migrating from a REST + WebSocket architecture to a unified GraphQL API. This guide helps users and developers understand the changes and how to adapt their integrations.

## Migration Status

### ✅ Completed
- **Backend GraphQL Implementation**: Full schema with queries, mutations, and subscriptions
- **Frontend Apollo Integration**: React components can use GraphQL with feature flags
- **Real-time Updates**: Redis pub/sub for <10ms latency (down from 100ms polling)
- **REST Endpoint Migration**: All major REST endpoints have GraphQL equivalents

### 🚧 In Progress
- **CLI Tool Migration**: Currently depends on WebSocket, needs GraphQL client
- **Documentation**: API reference and examples

### 📅 Planned
- **REST Endpoint Removal**: After deprecation period (target: February 2025)
- **WebSocket Simplification**: After CLI migration

## Enabling GraphQL Mode

### Frontend
```bash
# Via URL parameter
http://localhost:3000?useGraphQL=true

# Via environment variable
VITE_USE_GRAPHQL=true pnpm dev:web
```

### Backend
GraphQL is always available at `/graphql` alongside REST endpoints.

To disable deprecated REST endpoints:
```bash
ENABLE_DEPRECATED_REST=false python -m apps.server.main
```

## API Comparison

### Listing Diagrams

**REST (Deprecated)**
```bash
GET /api/diagrams
```

**GraphQL**
```graphql
query {
  diagrams {
    id
    name
    description
    created_at
    updated_at
  }
}
```

### Executing a Diagram

**WebSocket (Legacy)**
```javascript
ws.send({
  type: 'execute_diagram',
  diagram: diagramData,
  options: { timeout: 300 }
});
```

**GraphQL**
```graphql
mutation ExecuteDiagram($diagram: JSON!, $options: ExecutionOptionsInput) {
  executeDiagram(diagram: $diagram, options: $options) {
    success
    executionId
    message
  }
}

# Then subscribe to updates
subscription ExecutionUpdates($executionId: String!) {
  executionUpdates(executionId: $executionId) {
    type
    executionId
    nodeId
    status
    data
    error
  }
}
```

### Managing API Keys

**REST (Deprecated)**
```bash
GET /api/api-keys
POST /api/api-keys
DELETE /api/api-keys/{key_id}
```

**GraphQL**
```graphql
# List persons with API keys
query {
  persons {
    id
    name
    apiKeys {
      id
      name
      provider
      model
    }
  }
}

# Create API key
mutation CreateApiKey($personId: String!, $input: ApiKeyInput!) {
  createApiKey(personId: $personId, apiKey: $input) {
    success
    message
  }
}
```

## Migration Checklist

### For Frontend Developers
- [ ] Enable GraphQL mode with feature flag
- [ ] Test your workflows with GraphQL enabled
- [ ] Report any issues or missing functionality
- [ ] Update any custom API integrations

### For API Consumers
- [ ] Review deprecation headers in REST responses
- [ ] Note the `Sunset` header date (February 2025)
- [ ] Migrate to GraphQL endpoints
- [ ] Test with `ENABLE_DEPRECATED_REST=false`

### For CLI Users
- [ ] Continue using the CLI as normal (WebSocket still supported)
- [ ] Watch for updates on GraphQL support in the CLI

## Performance Improvements

The GraphQL migration brings significant performance benefits:

- **Real-time Updates**: <10ms latency via Redis pub/sub (was 100ms polling)
- **Reduced Network Traffic**: Request only needed fields
- **Automatic Caching**: Apollo Client caches and deduplicates requests
- **Batch Operations**: Multiple operations in a single request

## Deprecation Timeline

1. **Now - January 2025**: Both REST and GraphQL available
2. **February 2025**: REST endpoints removed (except health checks)
3. **March 2025**: CLI tool migrated to GraphQL
4. **April 2025**: WebSocket endpoint simplified or removed

## Getting Help

- GraphQL Playground: http://localhost:8000/graphql
- Schema Documentation: Auto-generated in GraphQL Playground
- Issues: Report problems in the DiPeO repository

## Example: Full Migration

### Before (REST + WebSocket)
```javascript
// List diagrams
const response = await fetch('/api/diagrams');
const diagrams = await response.json();

// Execute diagram
const ws = new WebSocket('ws://localhost:8000/api/ws');
ws.send(JSON.stringify({
  type: 'execute_diagram',
  diagram: selectedDiagram
}));

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  handleExecutionUpdate(message);
};
```

### After (GraphQL)
```javascript
// List diagrams
const { data } = await apolloClient.query({
  query: gql`
    query GetDiagrams {
      diagrams {
        id
        name
        nodes { id type }
        arrows { id source target }
      }
    }
  `
});

// Execute diagram
const { data: execResult } = await apolloClient.mutate({
  mutation: gql`
    mutation Execute($diagram: JSON!) {
      executeDiagram(diagram: $diagram) {
        success
        executionId
      }
    }
  `,
  variables: { diagram: selectedDiagram }
});

// Subscribe to updates
const subscription = apolloClient.subscribe({
  query: gql`
    subscription Updates($id: String!) {
      executionUpdates(executionId: $id) {
        type
        nodeId
        status
        data
      }
    }
  `,
  variables: { id: execResult.executeDiagram.executionId }
}).subscribe({
  next: ({ data }) => handleExecutionUpdate(data.executionUpdates)
});
```

## Benefits of GraphQL

1. **Single Endpoint**: All operations through `/graphql`
2. **Type Safety**: Auto-generated TypeScript types
3. **Efficient Queries**: Request only needed data
4. **Real-time Subscriptions**: Built-in WebSocket support
5. **Self-Documenting**: Interactive schema explorer
6. **Better Developer Experience**: Modern tooling and ecosystem