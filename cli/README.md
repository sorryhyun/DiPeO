# DiPeO CLI GraphQL Migration

This directory contains the GraphQL client implementation for the DiPeO CLI tool.

## Overview

The CLI is migrating from WebSocket-based execution to GraphQL for better integration with the web frontend and improved error handling.

## Migration Status

- ✅ GraphQL client implementation (`graphql_client.py`)
- ✅ Diagram management commands (`diagram_commands.py`)
- ✅ Integration with main CLI tool (`tool.py`)
- ✅ Test suite (`test_graphql_cli.py`)
- 🔄 Dual support period (Current - February 2025)
- 📅 GraphQL default (March 2025)
- 📅 WebSocket removal (April 2025)

## Usage

### Install Dependencies

```bash
pip install -r requirements-cli.txt
```

### Run with GraphQL

```bash
# Use command line flag
python tool.py run diagram.json --use-graphql

# Or set environment variable
export DIPEO_USE_GRAPHQL=true
python tool.py run diagram.json
```

### Test GraphQL Implementation

```bash
cd cli
python test_graphql_cli.py
```

## Features

- **Unified API**: Same GraphQL endpoint as web frontend
- **Real-time Updates**: GraphQL subscriptions for execution progress
- **Better Error Handling**: Structured GraphQL errors
- **Type Safety**: Schema validation at runtime
- **Interactive Prompts**: Support for user_response nodes

## Architecture

```
cli/
├── __init__.py              # Module exports
├── graphql_client.py        # GraphQL client implementation
├── diagram_commands.py      # Diagram management operations
├── test_graphql_cli.py      # Test suite
└── README.md               # This file
```

## GraphQL Operations

### Execute Diagram
```graphql
mutation ExecuteDiagram($diagram: JSON!, $options: ExecutionOptionsInput) {
  executeDiagram(diagram: $diagram, options: $options) {
    success
    executionId
    message
  }
}
```

### Subscribe to Updates
```graphql
subscription ExecutionUpdates($executionId: String!) {
  executionUpdates(executionId: $executionId) {
    type
    nodeId
    status
    data
    error
  }
}
```

### List Diagrams
```graphql
query ListDiagrams {
  diagrams {
    id
    name
    description
    created_at
  }
}
```

## Differences from WebSocket

1. **Connection**: GraphQL uses HTTP/WebSocket transport vs pure WebSocket
2. **Schema**: Strongly typed with automatic validation
3. **Errors**: Structured error responses with detailed messages
4. **Performance**: Comparable performance with <10ms subscription latency

## Troubleshooting

### GraphQL Dependencies Not Installed
```
❌ GraphQL dependencies not installed. Run: pip install -r requirements-cli.txt
```

### Server Not Running
Ensure the server is running with GraphQL enabled:
```bash
cd server && WORKERS=1 python -m main
```

### Port Conflicts
The GraphQL server runs on port 8100 by default. Check for conflicts:
```bash
lsof -i :8100
```