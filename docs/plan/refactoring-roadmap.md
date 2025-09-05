# DiPeO Refactoring Roadmap

## Executive Summary

Based on comprehensive codebase analysis, this roadmap outlines the refactoring strategy for DiPeO v1.0. The refactoring addresses five major areas: architecture patterns, naming conventions, type safety, code organization, and technical debt removal.

## Current State Assessment

The DiPeO codebase demonstrates solid architectural foundations but suffers from:
- **Over-engineered abstractions** creating unnecessary complexity
- **Inconsistent conventions** from TypeScript-to-Python code generation
- **Type safety gaps** undermining confidence in static typing
- **Scattered organization** of related functionality
- **Accumulated technical debt** from rapid iteration

## Refactoring Phases

### Phase 1: Foundation (Weeks 1-2)
**Goal:** Establish conventions and tooling

1. **Setup & Tooling**
   - Configure stricter mypy settings
   - Update pre-commit hooks for naming conventions
   - Create automated code quality checks
   - Document coding standards

2. **Code Generation Fixes**
   - Fix TypeScript to Python naming conversion (camelCase → snake_case)
   - Eliminate wildcard imports in templates
   - Add proper type annotations to generated code

### Phase 2: Core Cleanup (Weeks 3-4)
**Goal:** Remove technical debt and consolidate foundations

1. **Deprecated Code Removal**
   - Remove all deprecated service registry keys
   - Complete NodeOutput → Envelope migration
   - Clean up legacy compatibility shims
   - Remove unused TypeScript/frontend code

2. **Enum Consolidation**
   - Unify duplicate RetryStrategy definitions
   - Consolidate service/provider type enums
   - Migrate key domain enums to TypeScript sources
   - Standardize enum naming conventions

### Phase 3: Architecture Refactoring (Weeks 5-7)
**Goal:** Simplify and clarify architectural patterns

1. **Interface Segregation**
   - Split monolithic DiagramPort into focused interfaces
   - Apply single responsibility principle
   - Remove unnecessary adapter layers
   - Simplify BaseService pattern

2. **Type Safety Improvements**
   - Fix Result dataclass type safety
   - Replace temporary JSON type definitions
   - Resolve forward reference issues
   - Add missing type annotations

### Phase 4: Standardization (Weeks 8-9)
**Goal:** Achieve consistent patterns throughout

1. **Naming Convention Alignment**
   - Apply snake_case throughout Python code
   - Standardize service registry keys
   - Update GraphQL resolver naming
   - Create field aliases for backward compatibility

2. **Protocol & Pattern Consistency**
   - Consolidate overlapping protocols
   - Standardize repository patterns
   - Unify event bus implementations
   - Document pattern usage

### Phase 5: Validation & Documentation (Week 10)
**Goal:** Ensure quality and maintainability

1. **Quality Assurance**
   - Run comprehensive type checking
   - Execute all tests with strict mode
   - Performance benchmarking
   - Security audit

2. **Documentation**
   - Update architecture documentation
   - Create migration guides
   - Document new patterns and conventions
   - Update CLAUDE.md with new practices

## Priority Matrix

### Critical (Do First)
- Fix code generation naming conversion
- Remove deprecated service registry keys
- Fix Result dataclass type safety
- Split DiagramPort interface

### High (Core Functionality)
- Complete NodeOutput migration
- Consolidate duplicate enums
- Eliminate wildcard imports
- Standardize service registry keys

### Medium (Quality of Life)
- Fix GraphQL resolver naming
- Improve JSON type definitions
- Consolidate protocols
- Add missing type annotations

### Low (Nice to Have)
- Documentation improvements
- Performance optimizations
- Additional tooling
- Enhanced error messages

## Risk Assessment

### High Risk Areas
1. **Code Generation Changes** - Affects all generated code
   - Mitigation: Thorough testing, gradual rollout
   
2. **Interface Segregation** - Major architectural change
   - Mitigation: Create adapters for backward compatibility

3. **Service Registry Cleanup** - Could break dependencies
   - Mitigation: Deprecation period with warnings

### Medium Risk Areas
1. **Enum Consolidation** - Touches many files
   - Mitigation: Automated refactoring tools

2. **Type System Changes** - Could expose hidden bugs
   - Mitigation: Incremental type checking

### Low Risk Areas
1. **Documentation Updates** - No runtime impact
2. **Deprecated Code Removal** - Already unused
3. **Naming Convention Fixes** - With aliases, backward compatible

## Success Metrics

### Quantitative
- Reduce `# type: ignore` from 17 to <5
- Achieve 0 mypy errors in strict mode
- Eliminate all wildcard imports
- Remove 100% of deprecated code
- Reduce interface count by 30%

### Qualitative
- Improved developer experience
- Faster onboarding for new contributors
- Clearer architectural boundaries
- Better IDE support and autocomplete
- Reduced cognitive load

## Implementation Guidelines

### For Each Change
1. **Document** the change in migration notes
2. **Test** thoroughly with existing functionality
3. **Provide** backward compatibility where needed
4. **Update** relevant documentation
5. **Communicate** breaking changes clearly

### Review Checkpoints
- Weekly progress reviews
- Bi-weekly architecture reviews
- Phase completion retrospectives
- Final v1.0 readiness assessment

## Next Steps

1. Review and approve this roadmap
2. Create detailed task breakdown for Phase 1
3. Set up monitoring and tracking
4. Begin Phase 1 implementation
5. Schedule regular check-ins

## Appendix

Detailed analysis reports available in:
- `protocol-analysis.md` - Interface architecture findings
- `naming-conventions.md` - Convention inconsistencies
- `type-safety.md` - Type system issues
- `enum-organization.md` - Enum consolidation opportunities
- `technical-debt.md` - Deprecated code inventory