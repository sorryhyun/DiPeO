# DiPeO v1.0 Refactoring Implementation Checklist

## Pre-Refactoring Setup

### Environment Preparation
- [ ] Create feature branch: `git checkout -b refactor/v1-preparation`
- [ ] Backup current state: `git tag pre-refactor-backup`
- [ ] Set up stricter tooling:
  - [ ] Configure mypy with gradual typing
  - [ ] Update ruff configuration for naming conventions
  - [ ] Add pre-commit hooks for code quality
- [ ] Document current metrics (type ignores, deprecated count, etc.)

### Team Preparation
- [ ] Review refactoring roadmap with team
- [ ] Assign phase owners
- [ ] Set up daily standup for refactoring period
- [ ] Create communication channel for issues

## Phase 1: Foundation (Weeks 1-2)

### Code Generation Pipeline Fix
- [ ] **Update TypeScript to Python name conversion**
  ```python
  # projects/codegen/generator.py
  - [ ] Add camelCase to snake_case converter
  - [ ] Update field name generation
  - [ ] Test with sample nodes
  ```

- [ ] **Eliminate wildcard imports**
  ```python
  # projects/codegen/templates/
  - [ ] Update import statements in templates
  - [ ] Use explicit imports only
  - [ ] Verify no namespace pollution
  ```

- [ ] **Regenerate all code**
  ```bash
  - [ ] make codegen
  - [ ] make diff-staged  # Review changes
  - [ ] make apply-syntax-only
  - [ ] Run all tests
  ```

### Tooling & Standards
- [ ] **Create coding standards document**
  - [ ] Python naming conventions
  - [ ] Type annotation requirements
  - [ ] Import organization rules
  - [ ] Enum definition guidelines

- [ ] **Update CI/CD pipeline**
  - [ ] Add mypy check (permissive mode)
  - [ ] Add naming convention check
  - [ ] Add deprecated code detection
  - [ ] Add import organization check

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
- [ ] `# type: ignore` reduced from 17 to <5
- [ ] 0 mypy errors in strict mode
- [ ] 0 wildcard imports
- [ ] 0 deprecated code markers
- [ ] 0 camelCase in Python code
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

**Start Date:** _____________
**Target Completion:** _____________
**Actual Completion:** _____________

**Notes:**
_Space for tracking issues, decisions, and learnings during refactoring_