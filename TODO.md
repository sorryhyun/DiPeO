# TODO - IR Builders Migration Completion

## Overview

The IR builders have been partially migrated from legacy monolithic files to a new pipeline-based architecture. However, several legacy files are still being used by the new builders and need to be fully migrated before they can be removed.

## Current Migration Status

### ✅ Completed - New Architecture
- `ir_builders/builders/` - New pipeline-based builders (backend.py, frontend.py, strawberry.py)
- `ir_builders/modules/` - Reusable step modules for extraction/transformation
- `ir_builders/core/` - Pipeline orchestration framework (context, steps, base)
- `ir_builders/validators/` - Validation framework for IR data

### ⚠️ Legacy Dependencies Still Active

**Critical Dependencies Blocking Removal:**
1. **`strawberry_builders.py`** - Referenced in `builders/strawberry.py:242, 370`:
   - `build_complete_ir()` - Assembles final strawberry IR
   - `build_domain_ir()` - Builds domain type IR structure
   - `build_operations_ir()` - Builds GraphQL operations IR
   - `validate_strawberry_ir()` - Validates assembled IR

2. **`backend_extractors.py`** - Referenced in `builders/backend.py:69`:
   - `extract_typescript_indexes()` - Extracts TypeScript index files

**Other Legacy Files (Potentially Removable):**
- `backend_builders.py` - Contains build utility functions
- `strawberry_extractors.py` - GraphQL extraction logic (moved to modules)
- `strawberry_transformers.py` - Type transformation logic (moved to modules)
- `strawberry_config.py` - Configuration handling (still used)
- `frontend.py` - Legacy frontend builder (replaced by builders/frontend.py)
- `base.py` - Legacy base class (replaced by core/base.py)
- `utils.py` - Shared utilities (may still be needed)

## Migration Plan

### Phase 1: Migrate Critical Functions to Modules

#### 1.1 Move Strawberry Builder Functions
**Target:** Create `modules/strawberry_assembly.py`
- Extract `build_complete_ir()`, `build_domain_ir()`, `build_operations_ir()` from `strawberry_builders.py`
- Convert to step classes following existing module patterns:
  - `BuildDomainIRStep`
  - `BuildOperationsIRStep`
  - `BuildCompleteIRStep`

#### 1.2 Move Strawberry Validation
**Target:** Enhance `validators/strawberry.py`
- Move `validate_strawberry_ir()` from `strawberry_builders.py`
- Integrate into existing validation framework

#### 1.3 Move TypeScript Index Extraction
**Target:** Create `modules/typescript_indexes.py`
- Extract `extract_typescript_indexes()` from `backend_extractors.py`
- Convert to step class: `ExtractTypescriptIndexesStep`

### Phase 2: Update New Builders

#### 2.1 Update `builders/strawberry.py`
- Replace imports from `strawberry_builders` with new module imports
- Update `StrawberryAssemblerStep` to use new step classes instead of direct function calls
- Ensure pipeline dependencies are correct

#### 2.2 Update `builders/backend.py`
- Replace import from `backend_extractors` with new module import
- Add `ExtractTypescriptIndexesStep` to pipeline

### Phase 3: Verification & Safe Removal

#### 3.1 Verify No External References
```bash
# Search for any remaining references to legacy files
grep -r "backend_extractors\|strawberry_builders\|backend_builders" \
  --exclude-dir=__pycache__ \
  --exclude-dir=.git \
  /home/sorryhyun/PycharmProjects/DiPeO
```

#### 3.2 Test Complete Pipeline
```bash
make codegen          # Generate code with new pipeline
make diff-staged      # Review changes
make apply-test       # Apply with server test
```

#### 3.3 Remove Legacy Files
**Priority Order (safest first):**
1. `backend_extractors.py` - Single function dependency
2. `strawberry_builders.py` - Multiple function dependencies
3. `backend_builders.py` - May have external references
4. `strawberry_extractors.py` - Already migrated to modules
5. `strawberry_transformers.py` - Already migrated to modules
6. `frontend.py` - Check for external usage first
7. `base.py` - Check for external usage first

### Phase 4: Clean Dependencies & Documentation

#### 4.1 Update Registry
- Verify `ir_registry.py` uses new builders correctly
- Update any remaining imports or references

#### 4.2 Update Documentation
- Update `dipeo/infrastructure/codegen/CLAUDE.md`
- Remove references to legacy files
- Update architecture diagrams if needed

## Implementation Priority

1. **Start with `extract_typescript_indexes`** (simple, single function)
2. **Move strawberry builder functions** (complex, multiple functions)
3. **Validate and test** after each migration step
4. **Remove files** only after confirming zero external dependencies

## Risk Mitigation

- **Test after each phase** - Don't batch all changes
- **Keep legacy files** until complete verification
- **Check git history** for any external usage patterns
- **Run full codegen pipeline** before final removal
- **Backup IR snapshots** for comparison testing

## Success Criteria

- [ ] All new builders use only `modules/`, `core/`, `validators/` imports
- [ ] Legacy files have zero references in codebase
- [ ] `make codegen && make apply-test` passes completely
- [ ] Generated code output matches pre-migration behavior
- [ ] Documentation reflects new architecture only