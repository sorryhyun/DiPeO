# API Deprecation Notice

## Summary

DiPeO is migrating from REST + WebSocket to GraphQL. The following REST endpoints are deprecated and will be removed on **February 1, 2025**.

## Deprecated Endpoints

All deprecated endpoints return the following headers:
- `X-Deprecated: true`
- `X-Deprecation-Message: <GraphQL alternative>`
- `Sunset: 2025-02-01`

### Diagram Management
| Method | Endpoint | GraphQL Alternative |
|--------|----------|-------------------|
| GET | `/api/diagrams` | `query { diagrams }` |
| GET | `/api/diagrams/{id}` | `query { diagram(id: $id) }` |
| POST | `/api/diagrams/save` | `mutation saveDiagram` |
| POST | `/api/diagrams/convert` | `mutation convertDiagram` |
| GET | `/api/diagrams/executions` | `query { executions }` |
| GET | `/api/diagrams/execution-capabilities` | `query { executionCapabilities }` |

### API Key Management
| Method | Endpoint | GraphQL Alternative |
|--------|----------|-------------------|
| GET | `/api/api-keys` | `query { persons { apiKeys } }` |
| POST | `/api/api-keys` | `mutation createApiKey` |
| PUT | `/api/api-keys/{id}` | `mutation updateApiKey` |
| DELETE | `/api/api-keys/{id}` | `mutation deleteApiKey` |
| POST | `/api/api-keys/test` | `mutation testApiKey` |

### File Operations
| Method | Endpoint | GraphQL Alternative |
|--------|----------|-------------------|
| POST | `/api/files/upload` | `mutation uploadFile` |

### Conversations
| Method | Endpoint | GraphQL Alternative |
|--------|----------|-------------------|
| GET | `/api/conversations` | `query { conversations }` |
| POST | `/api/conversations/clear` | `mutation clearConversations` |

### Model Operations
| Method | Endpoint | GraphQL Alternative |
|--------|----------|-------------------|
| POST | `/api/models/initialize` | `mutation initializeModel` |
| POST | `/api/import-yaml` | `mutation importYamlDiagram` |

## Endpoints That Will Remain

### Health Checks (Kubernetes)
- GET `/api/health/live` - Liveness probe
- GET `/api/health/ready` - Readiness probe
- GET `/api/diagrams/health` - Application health (may be removed later)

### WebSocket (CLI Support)
- WS `/api/ws` - Required for CLI tool until migration

### Metrics
- GET `/metrics` - Prometheus metrics

## How to Disable Deprecated Endpoints

Set the environment variable:
```bash
ENABLE_DEPRECATED_REST=false
```

This will:
- Remove all deprecated REST endpoints
- Keep health checks and WebSocket
- Force all clients to use GraphQL

## Migration Resources

- [GraphQL Migration Guide](./graphql-migration-guide.md)
- GraphQL Playground: http://localhost:8000/graphql
- Schema Documentation: Available in GraphQL Playground

## Timeline

- **Now**: Deprecation warnings added to all REST responses
- **January 2025**: Final reminder to migrate
- **February 1, 2025**: REST endpoints removed
- **March 2025**: CLI tool GraphQL support
- **April 2025**: WebSocket deprecation (pending CLI migration)