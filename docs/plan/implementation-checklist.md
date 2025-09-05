# DiPeO v1.0 Refactoring Implementation Checklist

## Overall Progress
- ✅ **Phase 1: Foundation** - COMPLETED (2025-09-05)
- ⏳ **Phase 2: Core Cleanup** - Next
- ⏳ **Phase 3: Architecture Refactoring** - Pending
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

## Phase 2: Core Cleanup (Weeks 3-4)

### Deprecated Code Removal
- [ ] **Remove deprecated validator keys**
  ```python
  # dipeo/application/registry/keys.py
  - [ ] Remove API_VALIDATOR
  - [ ] Remove FILE_VALIDATOR
  - [ ] Remove DATA_VALIDATOR
  - [ ] Remove SCHEMA_VALIDATOR
  - [ ] Remove CONFIG_VALIDATOR
  - [ ] Remove INPUT_VALIDATOR
  ```

- [ ] **Complete NodeOutput migration**
  ```python
  - [ ] Search for all NodeOutput references
  - [ ] Replace with Envelope pattern
  - [ ] Update serialization functions
  - [ ] Remove NODE_OUTPUT_REPOSITORY key
  - [ ] Delete legacy NodeOutput classes
  ```

- [ ] **Clean up service registry**
  ```python
  - [ ] Remove DOMAIN_SERVICE_REGISTRY
  - [ ] Remove API_KEY_STORAGE
  - [ ] Remove commented LLM_REGISTRY
  - [ ] Verify no broken dependencies
  ```

### Enum Consolidation
- [ ] **Unify RetryStrategy definitions**
  ```typescript
  # dipeo/models/src/core/enums/
  - [ ] Create single RetryStrategy in TypeScript
  - [ ] Remove Python duplicates
  - [ ] Update all imports
  ```

- [ ] **Consolidate service type enums**
  ```typescript
  - [ ] Merge LLMService, APIServiceType
  - [ ] Create unified ServiceProvider enum
  - [ ] Update service configurations
  ```

- [ ] **Standardize enum naming**
  ```python
  - [ ] All members use UPPER_SNAKE_CASE
  - [ ] All values use lowercase
  - [ ] Fix any PascalCase members
  ```

## Phase 3: Architecture Refactoring (Weeks 5-7)

### Interface Segregation
- [ ] **Split DiagramPort interface**
  ```python
  # dipeo/domain/diagram/ports.py
  - [ ] Create DiagramFilePort (I/O operations)
  - [ ] Create DiagramFormatPort (conversions)
  - [ ] Create DiagramRepositoryPort (CRUD)
  - [ ] Create DiagramCompilerPort (compilation)
  - [ ] Add compatibility adapter
  ```

- [ ] **Remove unnecessary adapters**
  ```python
  - [ ] Identify pass-through adapters
  - [ ] Remove StateRepositoryAdapter
  - [ ] Direct service connections
  - [ ] Update dependency injection
  ```

- [ ] **Simplify BaseService**
  ```python
  - [ ] Convert to optional mixins
  - [ ] Create LoggingMixin
  - [ ] Create CachingMixin
  - [ ] Update service implementations
  ```

### Type Safety Improvements
- [ ] **Fix Result dataclass**
  ```python
  # dipeo/domain/type_defs.py
  - [ ] Implement Ok/Err classes OR
  - [ ] Add proper type guards
  - [ ] Remove type: ignore
  - [ ] Update all Result usage
  ```

- [ ] **Fix JSON type definitions**
  ```python
  - [ ] Replace Dict[str, Any] with recursive type
  - [ ] Use TypedDict where appropriate
  - [ ] Update JSON handling code
  ```

- [ ] **Add missing type annotations**
  ```python
  - [ ] All public methods have return types
  - [ ] Replace Any with specific types
  - [ ] Fix protocol implementations
  - [ ] Resolve forward references
  ```

## Phase 4: Standardization (Weeks 8-9)

### Naming Convention Alignment
- [ ] **Python code conventions**
  ```python
  - [ ] All fields use snake_case
  - [ ] All methods use snake_case
  - [ ] All variables use snake_case
  - [ ] Add compatibility aliases
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
  - [ ] Test GraphQL schema
  ```

### Protocol Consolidation
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
- [ ] `# type: ignore` reduced from 17 to <5 (Current: 17 - Phase 2)
- [ ] 0 mypy errors in strict mode (Gradual typing configured - Phase 3)
- [x] ~~0 wildcard imports~~ Strategy clarified: OK in templates/generated code
- [ ] 0 deprecated code markers (Current: 28 - Phase 2)
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

### Key Decisions
- Keep wildcards in templates/generated code, restrict only in manual code
- Use Pydantic Field(alias=...) for camelCase compatibility
- Apply mypy strictly only to domain and registry modules initially
