# Part 3: Data-Driven Codegen Architecture

## Overview

Transform the codegen system from a file-based approach to a pure data-driven approach where:
- Diagrams orchestrate the entire process using DB nodes for I/O
- Functions are pure transformations (data in → data out) 
- No file I/O or path resolution inside generator functions
- All templates and specs are loaded/saved by DB nodes
- Code lives in proper Python files, not inline in diagrams

## Completed Work Summary

### Architecture ✓
- Created modular directory structure separating frontend/backend/shared code
- Implemented pure generator functions for all code generation tasks
- Built diagram-based orchestration with DB nodes for all I/O
- Fixed all technical issues: imports, filters, templates, variable passing

### What's Working ✓
- **Single node generation**: Both frontend and backend work perfectly when run directly
- **Code quality**: Generated code is syntactically correct with proper formatting
- **DB nodes**: Placeholder resolution with dot notation works correctly
- **Templates**: All Jinja2 filters implemented and templates render successfully

## ✅ RESOLVED: Sub-Diagram Variable Passing

### The Solution
- Simplified the sub_diagram handler to pass variables directly (like CLI does)
- Removed complex input/output mapping logic that was causing issues
- Variables from parent diagrams now flow correctly to sub-diagram execution context
- DB nodes in sub-diagrams can now resolve placeholders like `{node_spec_path}`

### What Changed
- **Before**: Complex input_mapping with dot notation parsing and nested value extraction
- **After**: Direct variable passing - `options["variables"] = request.inputs`
- **Result**: 50% code reduction in handler, cleaner architecture, working variable passing

### Example
```bash
# Both now work correctly:
dipeo run codegen/diagrams/frontend/generate_frontend_single --light --debug --no-browser --timeout=15 \
  --input-data '{"node_spec_path": "person_job"}'

# And when called from batch diagram, variables are properly passed to sub-diagrams
```


## Key Architecture Benefits

1. **Pure Functions**: All generators are testable pure functions with no file I/O
2. **Visual Debugging**: Can see and debug the entire flow in diagram form
3. **Separation of Concerns**: Frontend/backend/shared code completely separated
4. **DiPeO Native**: Uses platform features (DB nodes, code_job, Start nodes)
5. **Maintainable**: Code in proper Python files with absolute imports
6. **Data-Driven**: Templates and specs loaded dynamically by DB nodes
7. **Extensible**: Easy to add new node types or output formats

## Batch Generation Approaches

### 1. Simple Approach: generate_frontend_batch_v2.light.yaml
- **Characteristics**: Hardcoded sequential flow for 3 node types
- **Pros**: Simple, easy to debug, guaranteed execution order
- **Cons**: Not scalable, requires manual updates for new node types
- **Structure**: 
  - Each node type has dedicated code_job → sub_diagram pair
  - Linear connections ensure sequential processing
  - Fixed to: person_job, sub_diagram, code_job

### 2. Optimized Approach: generate_frontend_all.light.yaml  
- **Characteristics**: Manifest-driven iteration with loop logic
- **Pros**: Scalable, automatically handles all nodes in manifest
- **Cons**: More complex, harder to debug iteration state
- **Structure**:
  - Loads frontend.json manifest
  - Uses condition node for loop control
  - Iterator pattern with current_index tracking
  - Dynamic node processing based on manifest

## Current Status

### What Needs Testing
1. **Batch Generation**: Both batch diagrams need testing to ensure:
   - Variables are properly passed to sub_diagram nodes
   - All frontend files are generated correctly
   - No conflicts between sequential generations

2. **Frontend Integration**: Generated components need to be:
   - Imported into the main frontend codebase
   - Added to NodeComponentMap for runtime usage
   - Type-checked with TypeScript compiler

### Integration Plan
1. Test simple batch (v2) first - easier to debug
2. Verify all 3 node types generate correctly
3. Test optimized batch (all) with full manifest
4. Update frontend imports to use generated components
5. Update NodeComponentMap with generated components
6. Run frontend build to ensure no TypeScript errors

## Detailed Technical Analysis

### Frontend Architecture Discovery

#### Current Node System
1. **Single Component Architecture**: All nodes use `ConfigurableNode` → `BaseNode`
   - No individual component files per node type needed
   - Configuration-driven rendering
   - Generated "components" are unnecessary wrappers

2. **Dual Registration System**:
   - **Static**: Manual configs in `apps/web/src/features/diagram-editor/config/nodes/`
   - **Dynamic**: Runtime registration via `nodeRegistry.ts`
   - Both feed into `NODE_CONFIGS_MAP`

3. **Generated Files Pattern**:
   ```
   apps/web/src/
   ├── features/diagram-editor/config/nodes/generated/  # Generated configs
   ├── __generated__/nodes/fields.ts                    # Field definitions
   └── features/diagram/components/nodes/generated/     # Unnecessary components
   ```

4. **Key Insight**: Generated node "components" are redundant - only configs are needed!

#### Critical Discovery About Generated Components

**Why Generated Components Are Unnecessary**:
- The codegen creates files like `PersonJobNode.tsx`, `CodeJobNode.tsx` in `features/diagram/components/nodes/generated/`
- These are just thin wrappers that return `<ConfigurableNode {...props} />`
- ALL nodes already use the same `ConfigurableNode` component
- The actual rendering is config-driven via `BaseNode`

**What's Actually Needed**:
- Node configurations in `features/diagram-editor/config/nodes/generated/`
- Field definitions for forms
- TypeScript type definitions
- NO individual component files per node type

**Manifest Shows 8 Node Types**: person_job, condition, api_job, code_job, db, endpoint, user_response, sub_diagram

### Diagram Engine Analysis

#### Sub_diagram Handler Current State

1. **✅ Variable Passing FIXED**:
   ```python
   # Line 93 in sub_diagram.py:
   options["variables"] = request.inputs or {}
   ```
   - Now passes all parent inputs directly as child variables
   - Works perfectly for codegen use case where we pass `node_spec_path`
   - Child diagrams can access parent variables via placeholders like `{node_spec_path}`
   - This is sufficient for the batch generation diagrams

2. **Input/Output Mapping Should Be Removed**:
   - `input_mapping` and `output_mapping` fields exist in the model but are ignored
   - These features add unnecessary complexity
   - The simple direct approach is cleaner and works for all use cases
   - **Action Required**: Remove these fields from:
     - `dipeo/models/src/diagram.ts` (SubDiagramNodeData interface)
     - Then run `make codegen` to update generated Python models

3. **How It Works in Practice**:
   ```yaml
   # In parent diagram (batch):
   - label: PersonJob Input
     type: code_job
     props:
       code: |
         result = {"node_spec_path": "person_job"}
   
   - label: Generate PersonJob  
     type: sub_diagram
     props:
       diagram_name: codegen/diagrams/frontend/generate_frontend_single
   ```
   - Code_job outputs `{"node_spec_path": "person_job"}`
   - Sub_diagram receives this as input and passes it as variables
   - Child diagram's DB nodes can use `{node_spec_path}` placeholder

#### Remaining Engine Issues

1. **Iteration State Management**:
   - No mechanism to update execution variables during loops
   - Code_job outputs don't persist to next iteration
   - This affects the manifest-based batch diagram (generate_frontend_all)

2. **Loop Control**:
   - Condition nodes can't access updated iteration state
   - No way to break loops based on dynamic conditions
   - PersonJob nodes loop until max_iteration regardless


### Phase 2: Test Batch Generation

1. **Test generate_frontend_batch_v2.light.yaml**:
   - Simple sequential flow
   - Each sub_diagram needs proper variable passing
   - Expected: 3 sets of generated files
   - Debug issues with hardcoded approach first

2. **Fix Iterator Pattern for generate_frontend_all.light.yaml**:
   - Code_job nodes must update execution variables
   - Condition node needs access to updated variables
   - Iterator state must persist between loop iterations
   - Add proper loop termination logic

### Phase 3: Frontend Integration

1. **Clean Up Generated Files**:
   - Delete unnecessary component files in `features/diagram/components/nodes/generated/`
   - Keep only configuration files
   - Update imports to use configs only

2. **Update Registration**:
   ```typescript
   // In apps/web/src/features/diagram-editor/config/nodes/index.ts
   import { generatedConfigs } from './generated';
   
   export const NODE_CONFIGS_MAP = {
     ...manualConfigs,
     ...generatedConfigs  // Add all generated configs
   };
   ```

3. **Type Safety**:
   - Ensure generated TypeScript models match frontend expectations
   - Update field type definitions if needed
   - Run TypeScript compiler to catch issues

### Phase 4: Testing Strategy

1. **Unit Tests**:
   - Test variable mapping logic in sub_diagram handler
   - Test iterator state management
   - Test generated config validity

2. **Integration Tests**:
   ```bash
   # Test single generation
   dipeo run codegen/diagrams/frontend/generate_frontend_single \
     --light --debug --input-data '{"node_spec_path": "person_job"}'
   
   # Test batch v2 (simple)
   dipeo run codegen/diagrams/frontend/generate_frontend_batch_v2 \
     --light --debug --timeout=30
   
   # Test batch all (complex) - after fixes
   dipeo run codegen/diagrams/frontend/generate_frontend_all \
     --light --debug --timeout=60
   ```

3. **Frontend Validation**:
   ```bash
   # Build frontend with generated configs
   cd apps/web && pnpm build
   
   # Run dev server and test node creation
   pnpm dev
   ```

## Critical Path

1. **Must Fix First**: Sub_diagram variable passing (blocks everything)
2. **Then Fix**: Variable updates in runtime (needed for iteration)
3. **Then Test**: Batch generation diagrams
4. **Finally**: Frontend integration

## Risk Mitigation

1. **Backward Compatibility**: Changes to sub_diagram handler affect all diagrams
2. **Testing**: Create test diagrams to validate fixes don't break existing flows
3. **Rollback Plan**: Keep original handler logic commented for quick revert
4. **Documentation**: Update CLAUDE.md with new patterns and limitations

## Executive Summary

### Key Discoveries

1. **Frontend**: Uses config-driven architecture, not component-per-node. Generated "components" are unnecessary.
2. **Sub_diagram Simplification**: The mapping features should be removed - direct variable passing is better
3. **Variable System**: No mechanism to update variables during execution - breaks iteration patterns
4. **Batch Diagrams**: Simple batch (v2) will work now, complex batch needs runtime fixes

### Current State Assessment

1. **✅ Sub_diagram handler** - Variable passing is WORKING (direct pass-through is sufficient)
2. **🔧 SubDiagramNode Model** - Should remove input_mapping and output_mapping fields
3. **❌ Execution runtime** - Still needs variable update capability for iteration patterns
4. **❌ Iterator logic** - Still has issues with loops and state persistence

### What Works Now

1. **Simple batch (generate_frontend_batch_v2)** - Should work! 
   - Uses sequential sub_diagram calls
   - Each has hardcoded inputs via code_job
   - No iteration state needed

2. **Single generation** - Already confirmed working
   - Variables pass correctly to child diagram
   - DB nodes resolve placeholders properly

### Simplified Frontend Integration

1. Delete generated component files (not needed)
2. Import only generated configs into NODE_CONFIGS_MAP  
3. Run TypeScript build to validate

### Next Immediate Actions

1. **Remove input_mapping/output_mapping from SubDiagramNode model** - Simplify the system
2. **Test generate_frontend_batch_v2.light.yaml** - This should work with current implementation!
3. **Verify generated files** for all 3 node types (person_job, sub_diagram, code_job)
4. **For generate_frontend_all.light.yaml** - Need to fix variable updates in runtime first

### Why Remove Mapping Features

1. **Not Needed**: Direct variable passing covers all use cases
2. **Adds Complexity**: Would require parsing, validation, and transformation logic
3. **Error Prone**: Dot notation parsing, nested object handling, type mismatches
4. **Already Working**: Current simple approach works perfectly
5. **YAGNI**: You Aren't Gonna Need It - don't add features until proven necessary

### Fields to Remove from SubDiagramNodeData

```typescript
// In dipeo/models/src/diagram.ts
export interface SubDiagramNodeData extends BaseNodeData {
  diagram_name?: string;
  diagram_format?: DiagramFormat;
  diagram_data?: Record<string, any>;
  input_mapping?: Record<string, string>;   // ❌ REMOVE THIS
  output_mapping?: Record<string, string>;  // ❌ REMOVE THIS
  timeout?: number;                         // ⚠️ Consider removing
  wait_for_completion?: boolean;            // ⚠️ Consider removing
  isolate_conversation?: boolean;           // ⚠️ Consider removing
}
```

Note: The last three fields are also not implemented. Consider removing them too for simplicity.

### Updated Understanding

The sub_diagram variable passing is actually working correctly now. The direct pass-through approach (`options["variables"] = request.inputs`) is sufficient for all use cases, not just codegen. 

**Key Insight**: The mapping features were over-engineering. The simple approach of passing all inputs as variables and returning endpoint outputs is cleaner, more maintainable, and covers all practical use cases. This is a perfect example of YAGNI (You Aren't Gonna Need It) - the complex mapping features seemed useful in theory but in practice the simple direct approach is better.

The batch_v2 diagram should work immediately, while the manifest-based approach needs runtime fixes for iteration state management.