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