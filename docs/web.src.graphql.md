# GraphQL Frontend Development Guide

## Overview
The `/src/graphql` directory contains Apollo Client configuration and GraphQL operations for the DiPeO application.

## Directory Structure
```
/src/graphql/
├── client.ts           # Apollo Client setup
├── queries/           # GraphQL operations organized by domain
│   ├── apiKeys.graphql
│   ├── diagrams.graphql
│   ├── executions.graphql
│   └── ...
└── types/             # TypeScript type mappings
```

## Apollo Client Configuration

The client supports both HTTP (queries/mutations) and WebSocket (subscriptions) connections:

```typescript
// Import the pre-configured client
import { apolloClient } from '@/graphql/client';

// Client automatically handles:
// - File uploads via apollo-upload-client
// - WebSocket subscriptions with auto-reconnect
// - Proper cache policies for DiPeO types
```

## Using Generated Types & Hooks

All GraphQL operations are automatically generated as typed hooks:

```typescript
// Import generated hooks from __generated__/graphql
import { 
  useGetDiagramQuery,
  useExecuteDiagramMutation,
  useExecutionUpdatesSubscription 
} from '@/__generated__/graphql';

// Usage example
const { data, loading, error } = useGetDiagramQuery({
  variables: { id: diagramId }
});

const [executeDiagram] = useExecuteDiagramMutation({
  onCompleted: (data) => {
    console.log('Execution started:', data.executeDiagram.executionId);
  }
});
```

## Type Mappings

The `types/graphql-mappings.ts` file provides utilities for converting between different type representations:

```typescript
import { 
  diagramToStoreMaps,      // Convert arrays to Maps for efficient lookups
  storeMapsToArrays,       // Convert Maps back to arrays for GraphQL
  nodeKindToGraphQLType,   // Convert node types
  areHandlesCompatible     // Check handle compatibility
} from '@/graphql/types';
```

## Best Practices

1. **Use Generated Hooks**: Always use the auto-generated hooks for type safety
2. **Cache Management**: The client is configured with appropriate cache policies - avoid manual cache manipulation
3. **Error Handling**: Wrap mutations in try-catch blocks or use the `onError` callback
4. **Subscriptions**: Clean up subscriptions properly using the returned unsubscribe function

## Common Patterns

```typescript
// Query with loading state
const DiagramViewer = ({ id }) => {
  const { data, loading } = useGetDiagramQuery({ 
    variables: { id },
    skip: !id  // Skip query if no ID
  });
  
  if (loading) return <Spinner />;
  return <Canvas diagram={data?.diagram} />;
};

// Mutation with optimistic response
const [createNode] = useCreateNodeMutation({
  optimisticResponse: {
    createNode: {
      success: true,
      node: tempNode,
      __typename: 'NodeOperationResult'
    }
  }
});

// Subscription for real-time updates
useExecutionUpdatesSubscription({
  variables: { executionId },
  onSubscriptionData: ({ subscriptionData }) => {
    updateExecutionState(subscriptionData.data?.executionUpdates);
  }
});
```

## File Upload Support

The client supports file uploads through the GraphQL layer:

```typescript
const [uploadDiagram] = useUploadDiagramMutation();

// File input handler
const handleFileSelect = async (file: File) => {
  await uploadDiagram({ 
    variables: { file, validateOnly: false } 
  });
};
```