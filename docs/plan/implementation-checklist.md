# DiPeO v1.0 Refactoring Implementation Checklist

## Overall Progress
- ✅ **Phase 1: Foundation** - COMPLETED (2025-09-05)
- ✅ **Phase 2: Core Cleanup** - COMPLETED (2025-09-05)
- ⏳ **Phase 3: Architecture Refactoring** - In Progress
- ⏳ **Phase 4: Standardization** - Pending
- ⏳ **Phase 5: Validation & Documentation** - Pending

## Pre-Refactoring Setup

### Environment Preparation ✅
- [x] Create feature branch: `git checkout -b refactor-v1-preparation`
- [x] Backup current state: `git tag pre-refactor-backup`
- [x] Set up stricter tooling:
  - [x] Configure mypy with gradual typing
  - [x] Update ruff configuration for naming conventions
  - [x] Add pre-commit hooks for code quality
- [x] Document current metrics (type ignores, deprecated count, etc.)

### Team Preparation
- [ ] Review refactoring roadmap with team
- [ ] Assign phase owners
- [ ] Set up daily standup for refactoring period
- [ ] Create communication channel for issues

## Phase 1: Foundation (Weeks 1-2) ✅ COMPLETED 2025-09-05

### Code Generation Pipeline Fix ✅
- [x] **Update TypeScript to Python name conversion**
  ```python
  # projects/codegen/templates/models/python_models.j2
  - [x] Add camelCase to snake_case converter (using snake_case filter)
  - [x] Update field name generation with Pydantic aliases
  - [x] Test with sample nodes
  ```

- [x] **Wildcard imports strategy clarified** *(Decision: Keep in templates)*
  ```python
  # Note: Wildcard imports are intentional in templates for flexibility
  - Templates use wildcards (OK)
  - Generated code uses wildcards (OK)  
  - Manual code avoids wildcards (enforced by linting)
  ```

- [x] **Regenerate all code**
  ```bash
  - [x] make codegen
  - [x] make diff-staged  # Review changes
  - [x] make apply-syntax-only
  - [x] make graphql-schema
  ```

### Tooling & Standards ✅
- [x] **Create coding standards document**
  - [x] Python naming conventions
  - [x] Type annotation requirements
  - [x] Import organization rules
  - [x] Enum definition guidelines

- [x] **Update CI/CD pipeline**
  - [x] Add mypy check (permissive mode)
  - [x] Add naming convention check (ruff N rules)
  - [x] Add pre-commit hooks with bandit security scanning
  - [x] Add import organization check

## Phase 2: Core Cleanup (Weeks 3-4) ✅ COMPLETED 2025-09-05

### Deprecated Code Removal ✅
- [x] **Remove deprecated validator keys**
  ```python
  # dipeo/application/registry/keys.py
  - [x] Remove API_VALIDATOR
  - [x] Remove FILE_VALIDATOR
  - [x] Remove DATA_VALIDATOR
  - [x] Remove SCHEMA_VALIDATOR
  - [x] Remove CONFIG_VALIDATOR
  - [x] Remove INPUT_VALIDATOR
  ```

- [x] **Complete NodeOutput migration** ✅
  ```python
  - [x] Search for all NodeOutput references
  - [x] Replace with Envelope pattern (already done)
  - [x] Update serialization functions (using SerializedEnvelope alias)
  - [x] Remove NODE_OUTPUT_REPOSITORY key
  - [x] Delete legacy NodeOutput classes (none found)
  ```

- [x] **Clean up service registry** ✅
  ```python
  - [x] Remove DOMAIN_SERVICE_REGISTRY
  - [x] Remove API_KEY_STORAGE
  - [x] Remove commented LLM_REGISTRY (already removed)
  - [x] Verify no broken dependencies
  ```

### Enum Consolidation ✅ COMPLETED
- [x] **Unify RetryStrategy definitions** ✅
  ```typescript
  # dipeo/models/src/core/enums/
  - [x] Create single RetryStrategy in TypeScript
  - [x] Remove Python duplicates (now import from generated)
  - [x] Update all imports
  ```

- [x] **Consolidate service type enums** ✅ *(Investigated - kept separate for different purposes)*
  ```typescript
  - [ ] Merge LLMService, APIServiceType
  - [ ] Create unified ServiceProvider enum
  - [ ] Update service configurations
  ```

- [x] **Standardize enum naming** ✅
  ```python
  - [x] All members use UPPER_SNAKE_CASE
  - [x] All values use lowercase (Status, EventType, HttpMethod)
  - [x] Fixed PascalCase members
  ```

## Phase 3: Architecture Refactoring (Weeks 5-7) ⏳ IN PROGRESS 2025-09-05

### Interface Segregation ✅ COMPLETED
- [x] **Split DiagramPort interface** ✅ 
  ```python
  # dipeo/domain/diagram/segregated_ports.py (new file created)
  - [x] Create DiagramFilePort (I/O operations)
  - [x] Create DiagramFormatPort (conversions)
  - [x] Create DiagramRepositoryPort (CRUD)
  - [x] DiagramCompilerPort already exists (no change needed)
  - [x] Add UnifiedDiagramPortAdapter for compatibility
  ```

- [x] **Remove unnecessary adapters** ✅
  ```python
  - [x] Identified pass-through adapters:
    * StateRepositoryAdapter - removed successfully
    * StateServiceAdapter - kept (provides useful abstraction)
    * StateCacheAdapter - kept (provides caching layer)
  - [x] Remove StateRepositoryAdapter
  - [x] Direct service connections (EventBasedStateStore implements protocol directly)
  - [x] Update dependency injection
  ```

- [x] **Simplify BaseService** ✅
  ```python
  # dipeo/domain/base/mixins.py (new file created)
  - [x] Created optional mixins:
    * LoggingMixin - logging with decorators
    * ValidationMixin - field and type validation
    * ConfigurationMixin - config management
    * CachingMixin - in-memory caching with TTL
    * InitializationMixin - initialization tracking
  - [x] Update service implementations to use mixins (DiagramService, LLMInfraService)
  ```

### Type Safety Improvements ✅ PARTIALLY COMPLETED
- [x] **Fix Result dataclass** ✅
  ```python
  # dipeo/domain/type_defs.py
  - [x] Added proper type guards (no type: ignore needed)
  - [x] Enhanced with map, map_err, and_then methods
  - [x] Added unwrap_or_else for computed defaults
  - [ ] Update all Result usage across codebase
  ```

- [x] **Fix JSON type definitions** ✅
  ```python
  - [x] Replaced Dict[str, Any] with recursive JsonValue type
  - [x] Added JsonObject and JsonArray type aliases
  - [x] Proper forward references for recursion
  - [ ] Update JSON handling code to use new types
  ```

- [ ] **Add missing type annotations**
  ```python
  - [ ] All public methods have return types
  - [ ] Replace Any with specific types
  - [ ] Fix protocol implementations
  - [ ] Resolve forward references
  ```

## Phase 4: Standardization (Weeks 8-9) ⏳ IN PROGRESS

### Enum Organization ✅ COMPLETED (2025-09-05)
- [x] **Add missing enums to TypeScript**
  ```typescript
  - [x] FlowStatus, CompletionStatus in execution.ts
  - [x] ExecutionPhase in execution.ts
  - [x] EventPriority, Severity in validation.ts (new file)
  ```

- [x] **Consolidate duplicate enums**
  ```python
  - [x] Remove manual FlowStatus, CompletionStatus definitions
  - [x] Remove manual ExecutionPhase definitions
  - [x] Remove manual EventPriority, Severity definitions
  - [x] Remove ClaudeCodeExecutionPhase (use ExecutionPhase)
  - [x] Create LLMServiceName alias for compatibility
  ```

- [x] **Update imports and dependencies**
  ```python
  - [x] All Python files use generated enums
  - [x] GraphQL schema updated with new enums
  - [x] Frontend TypeScript types regenerated
  ```

### Naming Convention Alignment ⏳ PENDING
- [ ] **Python code conventions**
  ```python
  - [ ] All fields use snake_case
  - [ ] All methods use snake_case
  - [ ] All variables use snake_case
  - [x] Add compatibility aliases (for enums)
  ```

- [ ] **Service registry standardization**
  ```python
  # dipeo/application/registry/keys.py
  - [ ] Use underscore pattern consistently
  - [ ] Update all dot notation keys
  - [ ] Update service lookups
  ```

- [ ] **GraphQL resolver updates**
  ```python
  # dipeo/application/graphql/
  - [ ] Use snake_case internally
  - [ ] Add field aliases for GraphQL
  - [x] Test GraphQL schema (enum updates)
  ```

### Protocol Consolidation ⏳ PENDING
- [ ] **Event system unification**
  ```python
  - [ ] Keep single EventBus protocol
  - [ ] Remove EventEmitter, MessageBus
  - [ ] Update all event publishers
  - [ ] Update all event consumers
  ```

- [ ] **Repository pattern cleanup**
  ```python
  - [ ] Separate persistence from business logic
  - [ ] Move business logic to services
  - [ ] Clean repository interfaces
  ```

## Phase 5: Validation & Documentation (Week 10)

### Quality Assurance
- [ ] **Type checking**
  ```bash
  - [ ] mypy dipeo/ --strict
  - [ ] Fix all type errors
  - [ ] Remove unnecessary type: ignore
  ```

- [ ] **Test execution**
  ```bash
  - [ ] pytest (backend)
  - [ ] pnpm test (frontend)
  - [ ] Integration tests
  - [ ] Example diagrams
  ```

- [ ] **Performance validation**
  ```bash
  - [ ] Benchmark key operations
  - [ ] Compare with pre-refactor
  - [ ] Profile memory usage
  ```

### Documentation Updates
- [ ] **Architecture documentation**
  - [ ] Update architecture diagrams
  - [ ] Document new patterns
  - [ ] Update interface descriptions

- [ ] **Migration guides**
  - [ ] Breaking changes list
  - [ ] Migration examples
  - [ ] Compatibility notes

- [ ] **Developer guides**
  - [ ] Update CLAUDE.md
  - [ ] Update CONTRIBUTING.md
  - [ ] Update README.md

## Post-Refactoring

### Cleanup
- [ ] Remove temporary compatibility code
- [ ] Delete backup branches
- [ ] Archive old documentation

### Communication
- [ ] Announce v1.0 changes
- [ ] Publish migration guide
- [ ] Update external documentation

### Monitoring
- [ ] Monitor error logs
- [ ] Track performance metrics
- [ ] Gather developer feedback

## Success Criteria

### Quantitative Metrics
- [ ] `# type: ignore` reduced from 17 to <5 (Current: 17 - Phase 3 target)
- [ ] 0 mypy errors in strict mode (Gradual typing configured - Phase 3)
- [x] ~~0 wildcard imports~~ Strategy clarified: OK in templates/generated code
- [x] 0 deprecated code markers (Completed in Phase 2 - all deprecated keys removed)
- [x] 0 camelCase in Python generated code (Fixed with aliases)
- [ ] All tests passing
- [ ] Performance within 5% of baseline

### Qualitative Goals
- [ ] Improved developer experience confirmed
- [ ] Clearer architecture boundaries
- [ ] Better IDE autocomplete
- [ ] Reduced onboarding time
- [ ] Positive team feedback

## Emergency Rollback Plan

If critical issues arise:

1. **Immediate rollback**
   ```bash
   git checkout pre-refactor-backup
   git push --force-with-lease
   ```

2. **Partial rollback**
   ```bash
   git revert <commit-range>
   ```

3. **Hot fixes**
   - Keep compatibility shims
   - Restore deprecated code
   - Document issues for next attempt

## Final Sign-off

### Technical Review
- [ ] Code review by senior developer
- [ ] Architecture review by tech lead
- [ ] Security review if applicable

### Stakeholder Approval
- [ ] Product owner sign-off
- [ ] Team consensus
- [ ] Documentation complete

### Release Preparation
- [ ] Version bump to 1.0.0
- [ ] Update changelog
- [ ] Tag release
- [ ] Merge to main branch

---

**Start Date:** 2025-09-05
**Target Completion:** 10 weeks from start
**Actual Completion:** _____________

**Notes:**

### Phase 1 Learnings (2025-09-05)
- Wildcard imports in templates are intentional for flexibility
- Snake_case conversion must preserve aliases for GraphQL/JSON compatibility  
- Pre-commit hooks essential for catching issues early
- Gradual typing allows incremental improvement without blocking progress

### Phase 2 Learnings (2025-09-05)
- NodeOutput to Envelope migration was already mostly complete (using alias)
- RetryStrategy unified in TypeScript with all variants for both domain and infrastructure
- Deprecated keys cleaned up from registry, fixed import errors in bootstrap containers
- Service type enum consolidation: LLMService and APIServiceType serve different purposes (kept separate)
- StateRepositoryAdapter successfully removed - EventBasedStateStore now implements protocol directly
- Mixins provide cleaner composition than monolithic BaseService inheritance
- Enum standardization: Updated Status, EventType, HttpMethod to use lowercase values
- Services migrated to use mixins (DiagramService, LLMInfraService) for logging/initialization

### Phase 3 Learnings (2025-09-05)
- Created segregated interfaces for DiagramPort following Interface Segregation Principle
- Implemented optional mixins (Logging, Validation, Configuration, Caching, Initialization) to replace monolithic BaseService
- Fixed Result dataclass type safety without needing type: ignore by adding proper null checks
- Improved JSON type definitions with proper recursive types using forward references
- Identified StateRepositoryAdapter as unnecessary pass-through that can be removed

### Phase 4 Learnings (2025-09-05) - Enum Organization
- Successfully migrated 5 manual enums to TypeScript generation (FlowStatus, CompletionStatus, ExecutionPhase, EventPriority, Severity)
- Created new validation.ts file for validation and priority-related enums
- Maintained backward compatibility with aliases (LLMServiceName = LLMService)
- Infrastructure-specific enums kept as manual (AuthStrategy, StreamingMode, ChecksumAlgorithm)
- All imports updated to use generated enums without breaking changes
- GraphQL schema and frontend types automatically updated with new enums

### Key Decisions
- Keep wildcards in templates/generated code, restrict only in manual code
- Use Pydantic Field(alias=...) for camelCase compatibility
- Apply mypy strictly only to domain and registry modules initially
