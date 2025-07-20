# Frontend Generated Code Migration Plan

## Overview

This plan outlines how to leverage the new code generation system to improve type safety, reduce boilerplate, and maintain consistency in the DiPeO frontend.

## Current State Analysis

### What's Working Well
- GraphQL codegen already generates TypeScript types and React hooks
- Domain types are centralized in `@dipeo/domain-models`
- Clear separation between GraphQL and domain types
- ConversionService provides utility functions for type transformations

### Pain Points to Address
1. Manual type conversions between GraphQL and domain types
2. Repetitive ID type casting
3. Store type definitions maintained separately from domain models
4. Form validation not derived from schema
5. Inconsistent error handling patterns

## Implementation Plan

### Phase 1: Integrate Generated Type Mappings (Week 1)

#### 1.1 Replace Manual Conversions
**Current**: Manual conversion functions in various files
**New**: Use generated mappings from `generated-mappings.ts`

```typescript
// Before (manual)
const domainNode = {
  id: node.id as NodeID,
  type: node.type as NodeType,
  position: { x: node.position.x, y: node.position.y },
  data: node.data || {}
};

// After (generated)
import { convertGraphQLNodeToDomain } from '@/lib/graphql/types/generated-mappings';
const domainNode = convertGraphQLNodeToDomain(node);
```

**Action Items**:
- [ ] Update `useDiagramLoader.ts` to use generated converters
- [ ] Replace conversions in `DiagramPanel.tsx`
- [ ] Update store helpers to use generated mappings
- [ ] Remove redundant manual conversion functions

#### 1.2 Enhance ConversionService
Integrate generated converters into ConversionService for backward compatibility:

```typescript
// src/core/services/ConversionService.ts
import * as GeneratedMappings from '@/lib/graphql/types/generated-mappings';

export class ConversionService {
  // Existing methods remain for compatibility
  
  // New methods using generated code
  static convertGraphQLNode = GeneratedMappings.convertGraphQLNodeToDomain;
  static convertDomainNode = GeneratedMappings.convertDomainNodeToGraphQL;
  // ... etc
}
```

### Phase 2: Generate Store Types (Week 2)

#### 2.1 Create Store Type Generator
Add new generation script: `generate-store-types.ts`

```typescript
// dipeo/models/scripts/generate-store-types.ts
// Generate Zustand store interfaces from domain models
// Output: apps/web/src/core/store/generated-types.ts
```

**Generated Output Example**:
```typescript
// Generated store slice interfaces
export interface GeneratedNodeSlice {
  nodes: Map<NodeID, DomainNode>;
  addNode: (node: DomainNode) => void;
  updateNode: (id: NodeID, updates: Partial<DomainNode>) => void;
  deleteNode: (id: NodeID) => void;
}
```

#### 2.2 Migrate Store Slices
- [ ] Generate base store interfaces
- [ ] Extend generated interfaces with UI-specific properties
- [ ] Update `unifiedStore.types.ts` to use generated base types
- [ ] Ensure immer compatibility

### Phase 3: Form Validation Generation (Week 3)

#### 3.1 Extend Zod Schema Generation
Current Zod generation only covers node data schemas. Extend to:
- Input validation schemas
- GraphQL mutation input validation
- Form field configurations

#### 3.2 Create Form Hooks
Generate typed form hooks:

```typescript
// Generated: useCreateNodeForm.ts
export function useCreateNodeForm() {
  const schema = generatedCreateNodeSchema;
  const form = useForm<CreateNodeInput>({
    resolver: zodResolver(schema)
  });
  // ... generated form logic
}
```

### Phase 4: Enhanced GraphQL Integration (Week 4)

#### 4.1 Custom GraphQL Codegen Plugin
Create plugin to generate:
- Typed error handlers
- Result unwrappers
- Optimistic update helpers

```typescript
// Generated helper example
export function handleDiagramMutation<T>(
  result: DiagramResult,
  onSuccess: (diagram: DomainDiagram) => T
): T | null {
  if (result.success && result.diagram) {
    const domain = convertGraphQLDiagramToDomain(result.diagram);
    return onSuccess(domain);
  }
  handleGraphQLError(result.error);
  return null;
}
```

#### 4.2 Operation Wrappers
Generate wrappers for common operations:

```typescript
// Generated: diagramOperations.ts
export const DiagramOperations = {
  async create(input: CreateDiagramInput): Promise<DomainDiagram> {
    const result = await client.mutate({
      mutation: CREATE_DIAGRAM,
      variables: { input }
    });
    return handleDiagramMutation(result.data.createDiagram, d => d);
  }
};
```

### Phase 5: Type-Safe Component Props (Week 5)

#### 5.1 Generate Component Interfaces
For each node type, generate:
- Props interfaces
- Default props
- Type guards

```typescript
// Generated: nodeComponentTypes.ts
export interface PersonJobNodeProps extends BaseNodeProps {
  data: PersonJobNodeData;
  // ... other typed props
}

export const isPersonJobNode = (node: DomainNode): node is PersonJobNode => {
  return node.type === NodeType.PERSON_JOB;
};
```

## Migration Strategy

### Incremental Adoption
1. **New Features First**: All new features use generated code
2. **High-Traffic Areas**: Migrate frequently-used components first
3. **Compatibility Layer**: Maintain backward compatibility during transition
4. **Feature Flags**: Use flags to toggle between old/new implementations

### File Organization
```
apps/web/src/
├── core/
│   ├── generated/          # All generated core types
│   │   ├── store-types.ts
│   │   └── validators.ts
│   └── types/              # Manual type augmentations
├── lib/
│   └── graphql/
│       ├── generated/      # GraphQL codegen output
│       └── types/
│           └── generated-mappings.ts
└── features/
    └── */
        └── generated/      # Feature-specific generated code
```

### Developer Workflow

#### Pre-commit Hook
```bash
#!/bin/sh
# .husky/pre-commit
pnpm run codegen:check || {
  echo "Generated files are out of date. Run 'make codegen'"
  exit 1
}
```

#### Watch Mode Development
```json
// package.json
{
  "scripts": {
    "dev": "concurrently \"pnpm codegen:watch\" \"vite\"",
    "codegen:watch": "nodemon --watch '../dipeo/models/src/**/*' --exec 'make codegen'"
  }
}
```

## Success Metrics

1. **Type Safety**: Zero runtime type errors
2. **Developer Velocity**: 50% reduction in boilerplate code
3. **Consistency**: 100% alignment between frontend/backend types
4. **Maintainability**: Single source of truth for all types

## Risk Mitigation

### Potential Issues & Solutions

1. **Breaking Changes**
   - Solution: Versioned generation with migration guides
   - Compatibility shims during transition

2. **Performance Impact**
   - Solution: Lazy load generated modules
   - Tree-shake unused conversions

3. **Developer Learning Curve**
   - Solution: Comprehensive documentation
   - CLI tools for common tasks
   - IDE snippets for generated imports

4. **Build Time Increase**
   - Solution: Incremental generation
   - Cache unchanged outputs
   - Parallel generation tasks

## Timeline

- **Week 1**: Integrate type mappings, update core components
- **Week 2**: Generate store types, migrate state management
- **Week 3**: Form validation generation, update forms
- **Week 4**: Enhanced GraphQL integration
- **Week 5**: Component prop generation, final migration
- **Week 6**: Documentation, training, optimization

## Next Steps

1. [ ] Review and approve plan
2. [ ] Set up generation pipeline
3. [ ] Create migration guide
4. [ ] Begin Phase 1 implementation
5. [ ] Schedule team training session

## Example: Adding a New Feature

With the new system, adding a "Comment" feature:

1. **Define in TypeScript** (`dipeo/models/src/diagram.ts`):
   ```typescript
   interface Comment {
     id: CommentID;
     text: string;
     nodeId: NodeID;
     userId: string;
     createdAt: Date;
   }
   ```

2. **Run Generation**: `make codegen`

3. **Use in Frontend**:
   ```typescript
   import { useCreateCommentMutation } from '@/__generated__/graphql';
   import { convertGraphQLCommentToDomain } from '@/lib/graphql/types/generated-mappings';
   
   const [createComment] = useCreateCommentMutation({
     update(cache, { data }) {
       if (data?.createComment.success) {
         const comment = convertGraphQLCommentToDomain(data.createComment.comment);
         // Type-safe update
       }
     }
   });
   ```

Everything is type-safe from database to UI!