# Part 3: Data-Driven Codegen Architecture

## Overview

Transform the codegen system from a file-based approach to a pure data-driven approach where:
- Diagrams orchestrate the entire process using DB nodes for I/O
- Functions are pure transformations (data in → data out) 
- No file I/O or path resolution inside generator functions
- All templates and specs are loaded/saved by DB nodes
- Code lives in proper Python files, not inline in diagrams

## Phase 1: Core Architecture (COMPLETED ✓)

### What Was Accomplished

1. **Created Directory Structure**:
   - Separated frontend and backend generators
   - Organized code into logical modules
   - Clear separation of concerns

2. **Implemented Pure Generators**:
   - Frontend: TypeScript model, node config, field config, node registry
   - Backend: Pydantic model, GraphQL schema, static nodes, conversions
   - All generators are pure functions (no file I/O)

3. **Created Light Diagrams**:
   - Frontend single/batch generation diagrams with proper labels
   - Backend single/batch generation diagrams with proper labels
   - Master orchestrator diagram
   - All using DB nodes for I/O operations

4. **Shared Utilities**:
   - Template environment with Jinja2
   - Custom filters for code generation
   - Type mappers for TypeScript and Python
   - Helper functions for UI and Pydantic

## Phase 2: Diagram Testing and Debugging (COMPLETED ✓)

### What Was Accomplished

1. **Fixed Inline Code Execution** ✓:
   - Simplified code_job handler to use explicit `code` and `filePath` fields
   - Fixed field mapping in `strategy_common.py` to keep fields separate
   - Successfully tested with `simple_db_test` diagram

2. **Fixed CLI Path Resolution** ✓:
   - Simplified to support `files/` directory paths
   - Can now use `dipeo run codegen/diagrams/test/simple_db_test` directly
   - Automatically prepends `files/` when needed

3. **Removed Unused Job Node** ✓:
   - Deleted `JobNodeData` from TypeScript models
   - Updated all references in Python code
   - Regenerated all models and conversions

4. **Updated Documentation** ✓:
   - Updated CLAUDE.md and CLAUDE.local.md with correct codegen diagram paths
   - Clarified that codegen diagrams are in `files/codegen/diagrams/`

## Phase 2.5: Test Single Node Generation (NEXT)

### What Needs Testing

1. **Frontend Single Node Generation**:
   ```bash
   dipeo run codegen/diagrams/frontend/generate_frontend_single --light --debug \
     --no-browser --timeout=15 --input-data '{"node_spec_path": "person_job"}'
   ```
   - Generates TypeScript model, node config, and field config
   - Uses template: `files/codegen/templates/frontend/*.j2`
   - Outputs to: `dipeo/models/src/nodes/`, `apps/web/src/features/`, etc.

2. **Backend Single Node Generation**:
   ```bash
   dipeo run codegen/diagrams/backend/generate_backend_single --light --debug \
     --no-browser --timeout=15 --input-data '{"node_spec_path": "person_job"}'
   ```
   - Generates Pydantic model, GraphQL schema, and static node
   - Uses template: `files/codegen/templates/backend/*.j2`
   - Outputs to: `dipeo/diagram_generated/`, `apps/server/src/graphql/`, etc.

### Key Observations

Both diagrams use:
- `code_type: file` for generator code (need to update to `language: python` + `filePath`)
- `code_type: python` with inline `code` for extracting node type
- Dynamic path resolution with `{node_spec_path}` and `{node_type}` placeholders
- DB nodes for all file I/O operations

### Issues to Fix Before Testing

1. **Update code_job props** in both diagrams:
   - Change `code_type: file` to `language: python`
   - Change `source_details` to `filePath`
   - Keep inline code blocks as-is (already using correct format)

2. **Verify generator code exists**:
   - Check all files in `files/codegen/code/frontend/generators/`
   - Check all files in `files/codegen/code/backend/generators/`

3. **Verify node specifications exist**:
   - Need at least `files/codegen/specifications/nodes/person_job.json`
   - Other test nodes: `condition.json`, `db.json`, etc.

## Phase 3: Advanced Features (FUTURE)

### 1. Dynamic Path Resolution

Current issue: DB nodes use hardcoded paths with `{node_type}` placeholders.

Solution needed:
- Dynamic path calculation in code_job nodes
- Pass calculated paths to DB nodes via labels
- Support for custom output locations

### 2. Code_job with Multiple Inline Code Blocks

**Issue**: Current code_job implementation only supports a single code block or file reference.

**Proposed Enhancement**:
```yaml
- label: Multi-Step Processing
  type: code_job
  position: {x: 400, y: 300}
  props:
    code_type: python
    # Multiple code blocks executed in sequence
    code_blocks:
      - name: validate_input
        code: |
          # First block: Validate input
          if not spec_data or 'type' not in spec_data:
              raise ValueError("Invalid spec data")
          validated_spec = spec_data
          
      - name: transform_data
        code: |
          # Second block: Transform data (can access previous results)
          transformed = {
              **validated_spec,
              'timestamp': datetime.now().isoformat(),
              'version': '1.0.0'
          }
          
      - name: prepare_output
        code: |
          # Third block: Prepare final output
          result = {
              'data': transformed,
              'status': 'success',
              'metadata': {'blocks_executed': 3}
          }
```

**Benefits**:
- Step-by-step processing with intermediate results
- Better error handling (know which block failed)
- Easier debugging and testing
- Can share context between blocks
- More readable than one large code block

**Implementation Considerations**:
- Each block has access to previous blocks' variables
- Error in any block stops execution
- Optional continue_on_error flag per block
- Return value from last block is the node output

### 3. Validation and Error Handling

- JSON Schema validation for specifications
- Template validation before generation
- Comprehensive error messages
- Rollback on failure

### 4. Performance Optimizations

- Parallel generation for multiple nodes
- Template caching
- Incremental generation (only changed specs)

## Immediate Next Steps

1. **Fix Inline Code Execution** (Priority: Critical)
   - Simplify code_job handler implementation
   - Choose one approach: file-only, separate nodes, or proper property handling
   - Current complex implementation with `__pydantic_extra__` is not working

2. **Fix CLI Path Resolution** (Priority: Critical)
   ```bash
   # Should work without relative paths:
   dipeo run codegen/diagrams/test/simple_db_test --light --debug --no-browser
   
   # Not this:
   dipeo run ../codegen/diagrams/test/simple_db_test --light --debug --no-browser
   ```

3. **Remove Job Node** (Priority: High)
   - Delete JobNodeData from TypeScript models
   - Regenerate all models
   - Ensure only CodeJobNode is used

4. **Test Single Node Generation** (Priority: High)
   ```bash
   # After fixing inline code execution
   dipeo run codegen/diagrams/frontend/generate_frontend_single --light --debug \
     --no-browser --timeout=15 --input-data '{"node_spec_path": "person_job"}'
   ```

5. **Test Batch and Full Pipeline** (Priority: Medium)
   - Only after single node generation works
   - May need to implement batch processors
   - Test master orchestrator

## Key Architecture Benefits

1. **Pure Functions**: All generators are testable pure functions
2. **Visual Debugging**: Can see and debug the entire flow
3. **Separation of Concerns**: Frontend/backend completely separated
4. **DiPeO Native**: Uses platform features (DB nodes, sub-diagrams)
5. **Maintainable**: Code in files, not embedded in YAML