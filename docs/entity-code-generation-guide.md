# Entity-Based Code Generation Guide

## Overview

The DiPeO entity code generation system extends the existing TypeScript-to-Python model generation to automatically produce GraphQL resolvers and React hooks from simple entity definitions. This reduces boilerplate code by ~80% while maintaining type safety and consistency.

## Quick Start

### 1. Define an Entity

Create a new entity definition in `dipeo/models/src/entities/`:

```typescript
// dipeo/models/src/entities/task.entity.ts
import { defineEntity } from '../entity-config';

export const TaskEntity = defineEntity({
  name: 'Task',
  plural: 'tasks',
  
  fields: {
    id: { type: 'TaskID', generated: true },
    title: { type: 'string', required: true },
    description: { type: 'string', nullable: true },
    status: { type: 'string', default: 'pending' },
    priority: { type: 'number', default: 0 },
    dueDate: { type: 'Date', nullable: true },
    createdAt: { type: 'Date', generated: true },
    updatedAt: { type: 'Date', generated: true }
  },
  
  relations: {
    assignee: { type: 'Person', relation: 'one-to-one' },
    project: { type: 'Project', relation: 'many-to-one' }
  },
  
  operations: {
    create: {
      input: ['title', 'description', 'status', 'priority', 'dueDate', 'assigneeId', 'projectId']
    },
    update: {
      input: ['title', 'description', 'status', 'priority', 'dueDate'],
      partial: true
    },
    delete: true,
    list: {
      filters: ['status', 'assigneeId', 'projectId'],
      sortable: ['priority', 'dueDate', 'createdAt'],
      pagination: true
    },
    get: true
  },
  
  features: {
    timestamps: true,
    audit: true
  }
});
```

### 2. Run Code Generation

```bash
make codegen
```

This generates:

- **Backend**: GraphQL resolvers, queries, and types
- **Frontend**: React hooks, GraphQL documents, TypeScript types

### 3. Use Generated Code

#### Backend (Python)

The generated resolvers are automatically included in your GraphQL schema:

```python
# apps/server/dipeo_graphql/resolvers/generated/task_mutations.py
@strawberry.type
class TaskMutations:
    @strawberry.mutation
    async def create_task(self, input: CreateTaskInput, info: Info) -> TaskResult:
        # Auto-generated implementation
        ...
    
    @strawberry.mutation
    async def update_task(self, id: ID, input: UpdateTaskInput, info: Info) -> TaskResult:
        # Auto-generated implementation
        ...
```

#### Frontend (React)

Use the generated hooks in your components:

```typescript
// Using the composite operations hook
import { useTaskOperations } from '@/features/tasks/hooks';

function TaskList() {
  const { tasks, loading, create, update, delete: deleteTask } = useTaskOperations();
  
  const handleCreate = async () => {
    const result = await create({
      title: 'New Task',
      description: 'Task description',
      status: 'pending'
    });
    
    if (result?.success) {
      console.log('Task created:', result.task);
    }
  };
  
  // ... render UI
}
```

```typescript
// Using individual hooks
import { useCreateTask, useUpdateTask } from '@/features/tasks/hooks';

function TaskForm() {
  const [createTask, { loading: creating }] = useCreateTask();
  const [updateTask, { loading: updating }] = useUpdateTask();
  
  // ... use mutations
}
```

## Generated File Structure

```
dipeo/
├── models/
│   └── src/
│       └── entities/
│           └── task.entity.ts          # Your entity definition
│
apps/
├── server/
│   └── dipeo_graphql/
│       ├── resolvers/
│       │   └── generated/
│       │       └── task_mutations.py   # Generated mutations
│       ├── queries/
│       │   └── generated/
│       │       └── task_queries.py     # Generated queries
│       └── types/
│           └── generated/
│               └── task_types.py       # Generated GraphQL types
│
└── web/
    └── src/
        └── features/
            └── tasks/
                ├── graphql/
                │   └── task.graphql        # Generated GraphQL documents
                └── hooks/
                    └── generated/
                        └── useTaskOperations.ts  # Generated React hooks
```

## Advanced Features (Planned)

**Note**: The following features are defined in the entity schema but are not yet fully implemented in the code generation:

### Custom Business Logic

Add custom logic to operations:

```typescript
operations: {
  create: {
    input: ['title', 'assigneeId'],
    customLogic: `
      # Send notification to assignee
      if input.assignee_id:
          await notification_service.notify_task_assigned(
              user_id=input.assignee_id,
              task_title=input.title
          )
    `
  }
}
```

⚠️ **Known Issues**: 
- Custom logic indentation is currently broken
- Service references need proper context access

### Custom Operations

Define operations beyond CRUD:

```typescript
operations: {
  custom: {
    completeTask: {
      name: 'completeTask',
      type: 'mutation',
      input: ['taskId', 'completionNotes'],
      returns: 'Task',
      implementation: `
        task = await task_service.get(task_id)
        if not task:
            raise ValueError("Task not found")
        
        task.status = "completed"
        task.completed_at = datetime.now()
        task.completion_notes = completion_notes
        
        return await task_service.update(task)
      `
    }
  }
}
```

### Field Validation

Add validation rules:

```typescript
fields: {
  email: {
    type: 'string',
    required: true,
    validation: {
      pattern: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$',
      custom: 'validate_email_domain'
    }
  },
  age: {
    type: 'number',
    validation: {
      min: 0,
      max: 150
    }
  }
}
```

⚠️ **Not Implemented**: Validation rules are parsed but not yet used in generated code

## Best Practices

1. **Naming Conventions**
   - Use PascalCase for entity names (e.g., `TaskEntity`)
   - Use lowercase plural for the `plural` field
   - Use camelCase for field names

2. **ID Types**
   - Always use branded types for IDs (e.g., `TaskID`, `PersonID`)
   - Mark ID fields as `generated: true`

3. **Relations**
   - Define both sides of relationships when possible
   - Use the `inverse` property to specify the reverse relation

4. **Operations**
   - Start with basic CRUD, add custom operations as needed
   - Keep custom logic minimal and focused
   - Use service layer for complex business logic

5. **Features**
   - Enable `timestamps` for audit trails
   - Use `softDelete` for data retention
   - Enable `cache` for frequently accessed entities

## Extending the System

### Adding New Field Types

1. Add the type to `FieldType` in `entity-config.ts`
2. Update type mappings in generators
3. Add validation rules if needed

### Adding New Features

1. Add to `FeaturesDefinition` interface
2. Update generators to handle the feature
3. Document the feature behavior

### Custom Generators

Create additional generators by:

1. Creating a new script in `dipeo/models/scripts/`
2. Following the pattern of existing generators
3. Adding to the `generate-entities.ts` orchestrator
4. Updating `package.json` scripts

## Troubleshooting

### Common Issues

1. **Generated files not appearing**
   - Check entity file naming (must end with `.entity.ts`)
   - Verify entity export name
   - Check console for generation errors

2. **Type errors in generated code**
   - Ensure all field types are defined
   - Check relation types exist
   - Verify branded types are imported

3. **Missing hooks or resolvers**
   - Verify operations are defined in entity
   - Check output paths in generator
   - Run `make codegen` again

### Debug Mode

Enable verbose logging:

```bash
DEBUG=codegen make codegen
```

## Current Status

The entity code generation system is functional but has several known issues that need to be addressed. See [TODO.md](./TODO.md) for a detailed list of remaining work and improvements.

### What's Working
- ✅ Entity definition schema
- ✅ Basic CRUD operation generation
- ✅ React hook generation
- ✅ GraphQL document generation
- ✅ File structure and organization

### Known Issues
- ❌ Model imports assume entities exist in `dipeo.models`
- ❌ Custom logic indentation is broken
- ❌ Service references need proper context access
- ❌ Some type imports are missing
- ❌ Manual integration still required

## Future Enhancements

See [TODO.md](./TODO.md) for a comprehensive list of planned improvements, including:

1. **Real-time Subscriptions**: Auto-generate GraphQL subscriptions
2. **Testing**: Generate unit tests for operations
3. **Documentation**: Auto-generate API documentation
4. **Migration**: Generate database migrations from model changes
5. **Validation**: Enhanced client-side validation generation
6. **Automatic Integration**: AST-based file modifications
7. **Service Generation**: Auto-generate service implementations