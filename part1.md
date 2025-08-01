# DiPeO Enum Refactoring Plan

## Overview

The DiPeO codebase has centralized enum definitions in `@dipeo/models/src/enums.ts`, but many parts of the code are still using string literals or manual conversions instead of importing and using these enums directly. This leads to:

- Type safety issues
- Maintenance challenges when enum values change
- Inconsistent naming across the codebase
- Potential runtime errors from typos

## ✅ Completed Work Summary

### Python Backend - High Priority Files (Completed)
1. **dipeo/domain/diagram/utils/strategy_common.py**
   - Added `NodeType` enum import
   - Replaced all node type string literals with `NodeType.X.value`
   
2. **dipeo/domain/llm/services/llm_domain_service.py**
   - Added `LLMService` enum import
   - Updated provider comparisons and validation rules
   
3. **dipeo/application/services/apikey_service.py**
   - Added `APIServiceType` enum import
   - Updated service validation logic
   
4. **dipeo/domain/validators/api_validator.py**
   - Added `APIServiceType` enum import
   - Updated API key format validation

## Available Enums in @dipeo/models/

The following enums are defined and should be used throughout the codebase:

1. **NodeType** - All node types (start, person_job, condition, etc.)
2. **HandleDirection** - input/output
3. **HandleLabel** - default, first, condtrue, condfalse, success, error, results
4. **DataType** - any, string, number, boolean, object, array
5. **MemoryView** - all_involved, sent_by_me, sent_to_me, system_and_me, conversation_pairs, all_messages
6. **MemoryProfile** - FULL, FOCUSED, MINIMAL, GOLDFISH, CUSTOM
7. **DiagramFormat** - native, light, readable
8. **DBBlockSubType** - fixed_prompt, file, code, api_tool
9. **ContentType** - raw_text, conversation_state, object, empty, generic, variable
10. **SupportedLanguage** - python, typescript, bash, shell
11. **HttpMethod** - GET, POST, PUT, DELETE, PATCH
12. **HookType** - shell, webhook, python, file
13. **HookTriggerMode** - none, manual, hook
14. **ExecutionStatus** - PENDING, RUNNING, PAUSED, COMPLETED, FAILED, ABORTED, SKIPPED
15. **NodeExecutionStatus** - Same as above + MAXITER_REACHED
16. **EventType** - Various execution events
17. **LLMService** - openai, anthropic, google, gemini, bedrock, vertex, deepseek
18. **APIServiceType** - All API services including LLMs + notion, slack, github, etc.
19. **NotionOperation** - CRUD operations for Notion
20. **ToolType** - web_search, web_search_preview, image_generation
21. **ToolSelection** - none, image, websearch

## Identified Problem Areas

### 1. Python Files Using String Literals

**Note**: Python files should import enums from `dipeo.diagram_generated` which contains the generated Python enums from the TypeScript definitions.

#### ✅ Completed High Priority Files:
- `dipeo/domain/diagram/utils/strategy_common.py` ✓
  - Added `NodeType` enum import
  - Replaced all node type string comparisons with enum values
  - Updated both import and export field mapping methods

- `dipeo/domain/llm/services/llm_domain_service.py` ✓
  - Added `LLMService` enum import
  - Updated provider comparisons and validation rules
  - Replaced string literals in token calculation methods

- `dipeo/application/services/apikey_service.py` ✓
  - Added `APIServiceType` enum import
  - Updated service validation to use enum values

- `dipeo/domain/validators/api_validator.py` ✓
  - Added `APIServiceType` enum import
  - Updated API key format validation

#### Medium Priority Files:
- `dipeo/application/execution/handlers/sub_diagram.py`
  - Execution status strings
  - Should use `ExecutionStatus` enum

- `dipeo/application/execution/iterators/simple_iterator.py`
  - Status comparisons
  - Should use `NodeExecutionStatus` enum

- `dipeo/core/dynamic/memory_filters.py`
  - Memory view comparisons
  - Should use `MemoryView` enum

### 2. TypeScript Files Using String Literals

**Note**: The frontend already has a good pattern established in `apps/web/src/core/types/domain.ts` which re-exports all enums from `@dipeo/domain-models`. This is the recommended import path for frontend code.

#### High Priority Files:
- `apps/web/src/features/diagram-editor/components/nodes/BaseNode.tsx`
  - Already imports `NodeType` and `NodeExecutionStatus` correctly ✓
  - Other files should follow this pattern

- `apps/web/src/features/diagram-editor/utils/diagramSerializer.ts`
  - Case statements with node type strings
  - Should use `NodeType` enum

- `apps/web/src/features/diagram-editor/components/DiagramCanvas.tsx`
  - Node type checks
  - Should use `NodeType` enum

#### Medium Priority Files:
- `apps/web/src/features/diagram-editor/adapters/DiagramAdapter.ts`
  - Node type and memory view strings
  - Should import enums

- `apps/web/src/shared/contexts/CanvasContext.tsx`
  - Node type comparisons
  - Should use `NodeType` enum

### 3. Common Patterns to Refactor

#### Pattern 1: String Comparisons
```python
# Before
if node_type == "start":
    # ...
elif node_type == "person_job":
    # ...

# After
from dipeo.diagram_generated import NodeType

if node_type == NodeType.START.value:
    # ...
elif node_type == NodeType.PERSON_JOB.value:
    # ...
```

#### Pattern 2: Provider Checks
```python
# Before
if provider.lower() == "openai":
    # ...

# After
from dipeo.diagram_generated import LLMService

if provider.lower() == LLMService.OPENAI.value:
    # ...
```

#### Pattern 3: TypeScript Comparisons
```typescript
// Before
if (node.type === "start") {
    // ...
}

// After
import { NodeType } from '@dipeo/models';

if (node.type === NodeType.START) {
    // ...
}
```

## Migration Strategy

### Phase 1: Import Enums (Low Risk)
1. Add enum imports to all identified files
2. Replace string literals with enum values
3. Run existing tests to ensure no breaking changes

### Phase 2: Type Annotations (Medium Risk)
1. Update function signatures to use enum types
2. Add proper type hints in Python files
3. Update TypeScript interfaces to use enums

### Phase 3: Validation Updates (Higher Risk)
1. Update validators to check against enum values
2. Add enum validation at API boundaries
3. Update error messages to reference enum names

## Implementation Plan

### Step 1: Python Backend Refactoring
✅ **High Priority Files Completed:**
- Domain layer: `strategy_common.py`, `llm_domain_service.py`, `api_validator.py` ✓
- Application layer: `apikey_service.py` ✓

**Remaining Python Files:**
- Medium priority files still need enum refactoring:
  - `dipeo/application/execution/handlers/sub_diagram.py` (ExecutionStatus)
  - `dipeo/application/execution/iterators/simple_iterator.py` (NodeExecutionStatus)
  - `dipeo/core/dynamic/memory_filters.py` (MemoryView)

### Step 2: TypeScript Frontend Refactoring
- Update core type definitions
- Refactor React components
- Update utility functions

### Step 3: Code Generation Updates
- Ensure generated code uses enums consistently
- Update templates if needed
- Regenerate all code

## Existing Good Patterns

Some files already follow best practices:

### Python Example (dipeo/domain/diagram/utils/strategy_common.py) - Now Updated
```python
from dipeo.diagram_generated import (
    HandleDirection,
    HandleLabel,
    NodeID,
    DataType,
    ContentType,
    NodeType,  # Added during refactoring
)
```

### TypeScript Example (apps/web/src/core/types/domain.ts)
```typescript
export {
  NodeType,
  HandleDirection,
  HandleLabel,
  // ... other enums
} from '@dipeo/domain-models';
```

## Benefits

1. **Type Safety**: Compile-time checking for valid values
2. **Maintainability**: Single source of truth for all constants
3. **IDE Support**: Better autocomplete and refactoring tools
4. **Error Prevention**: No more typos in string literals
5. **Documentation**: Enums are self-documenting

## Testing Strategy

1. **Unit Tests**: Ensure all enum comparisons work correctly
2. **Integration Tests**: Verify API contracts remain intact
3. **E2E Tests**: Confirm UI behavior unchanged
4. **Manual Testing**: Test critical workflows

## Rollback Plan

If issues arise:
1. Revert enum changes in affected files
2. Keep enum imports for gradual migration
3. Document any edge cases discovered

## Timeline Estimate

- Phase 1: 2-3 days
- Phase 2: 1-2 days
- Phase 3: 1-2 days
- Testing: 1-2 days

Total: ~1 week for complete migration

## Next Steps

1. ✅ Get approval for refactoring plan
2. ✅ Create feature branch for changes
3. ✅ Complete high-priority Python files
4. Complete remaining medium-priority Python files:
   - `sub_diagram.py` (ExecutionStatus enum)
   - `simple_iterator.py` (NodeExecutionStatus enum)
   - `memory_filters.py` (MemoryView enum)
5. Proceed with TypeScript files
6. Update tests as needed
7. Submit PR with comprehensive testing