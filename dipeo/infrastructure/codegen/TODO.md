# Codegen Infrastructure Refactoring TODO

**Goal**: Reduce ~40% code duplication and create reusable modules for better maintainability.

**Status**: Planning Complete, Ready for Implementation

---

## Phase 1: Base Step Classes (High Impact, Low Risk) - ✅ PARTIALLY COMPLETE

**Objective**: Abstract common patterns in BuildStep subclasses into reusable base classes.

### Completed Tasks ✅

- [x] **1.1 Create `ir_builders/core/base_steps.py`**
  - [x] Implement `BaseExtractionStep` with template method pattern
  - [x] Implement `BaseAssemblerStep` with dependency injection
  - [x] Implement `BaseTransformStep` with common transform patterns
  - [x] Implement `BaseValidatorStep` with validation framework
  - [x] Add comprehensive docstrings and examples

- [x] **1.2 Deduplication: Refactor Extraction Steps** (5/7 completed)
  - [x] Migrate `ExtractNodeSpecsStep` to use `BaseExtractionStep`
  - [x] Migrate `ExtractEnumsStep` to use `BaseExtractionStep`
  - [x] Migrate `ExtractDomainModelsStep` to use `BaseExtractionStep`
  - [x] Migrate `ExtractIntegrationsStep` to use `BaseExtractionStep`
  - [x] Migrate `ExtractConversionsStep` to use `BaseExtractionStep`
  - [x] Remove duplicated code from original steps

- [x] **1.3 Deduplication: Refactor Assembler Steps** (1/3 completed)
  - [x] Migrate `BackendAssemblerStep` to use `BaseAssemblerStep`
  - [x] Remove duplicated dependency gathering logic
  - [x] Remove duplicated metadata creation logic
  - [x] Remove duplicated error handling code

- [x] **1.5 Testing & Validation** (Basic testing completed)
  - [x] Verify refactored steps integrate with existing pipeline
  - [x] Run integration test with BackendBuilder

**Achieved Reduction**: ~35% code reduction in migrated step modules (extraction, transform, and assembler steps)

### Completed Additional Tasks ✅

- [x] **1.2 Remaining Extraction Steps** (1/2 completed)
  - [x] Migrate `ExtractGraphQLOperationsStep` to use `BaseExtractionStep`
  - [ ] Migrate `ExtractGraphQLTypesStep` to use `BaseExtractionStep` (SKIPPED - uses utility functions that handle iteration internally)

- [x] **1.3 Remaining Assembler Steps** (2/2 completed)
  - [x] Migrate `FrontendAssemblerStep` to use `BaseAssemblerStep`
  - [x] Migrate `StrawberryAssemblerStep` to use `BaseAssemblerStep`

- [x] **1.4 Deduplication: Refactor Transform Steps** (3/3 completed)
  - [x] Migrate `TransformStrawberryTypesStep` to use `BaseTransformStep`
  - [x] Migrate `BuildOperationStringsStep` to use `BaseTransformStep`
  - [x] Migrate `GroupOperationsByEntityStep` to use `BaseTransformStep`

### Remaining Tasks (Lower Priority)

- [ ] **1.4 Additional Cleanup**
  - [ ] Remove duplicated type conversion setup
  - [ ] Remove duplicated data normalization logic

- [ ] **1.5 Comprehensive Testing**
  - [ ] Write unit tests for base step classes
  - [ ] Write integration tests with all builders
  - [ ] Verify all IR outputs remain identical
  - [ ] Run full codegen pipeline tests
  - [ ] Update documentation

---

## Phase 2: AST Processing Framework

**Objective**: Create unified AST traversal and extraction framework to eliminate scattered AST processing logic.

### Tasks

- [ ] **2.1 Create `ir_builders/ast/` module structure**
  - [ ] Create module directory and `__init__.py`
  - [ ] Design AST visitor interface
  - [ ] Design AST walker implementation
  - [ ] Design filter interfaces

- [ ] **2.2 Implement `ast/walker.py`**
  - [ ] Implement `ASTWalker` class with file traversal
  - [ ] Implement `ASTVisitor` abstract base class
  - [ ] Add visitor methods: `visit_interface`, `visit_enum`, `visit_type_alias`, etc.
  - [ ] Add pre/post hooks for each visit method
  - [ ] Add context passing for stateful visits

- [ ] **2.3 Implement `ast/filters.py`**
  - [ ] Implement `FileFilter` with pattern matching
  - [ ] Implement `NodeFilter` with various filter strategies
  - [ ] Add common filter patterns (suffix, prefix, regex)
  - [ ] Add filter composition utilities (AND, OR, NOT)
  - [ ] Add filter presets for common patterns

- [ ] **2.4 Implement `ast/extractors.py`**
  - [ ] Create `InterfaceExtractor` (consolidate from utils.py)
  - [ ] Create `EnumExtractor` (consolidate from utils.py)
  - [ ] Create `TypeAliasExtractor` (consolidate from utils.py)
  - [ ] Create `ConstantExtractor` (consolidate from utils.py)
  - [ ] Create `BrandedScalarExtractor` (consolidate from utils.py)
  - [ ] Create `GraphQLInputTypeExtractor` (consolidate from utils.py)

- [ ] **2.5 Deduplication: Refactor `utils.py`**
  - [ ] Move `extract_interfaces_from_ast` → `InterfaceExtractor`
  - [ ] Move `extract_enums_from_ast` → `EnumExtractor`
  - [ ] Move `extract_type_aliases_from_ast` → `TypeAliasExtractor`
  - [ ] Move `extract_constants_from_ast` → `ConstantExtractor`
  - [ ] Move `extract_branded_scalars_from_ast` → `BrandedScalarExtractor`
  - [ ] Move `extract_graphql_input_types_from_ast` → `GraphQLInputTypeExtractor`
  - [ ] Mark old functions as deprecated
  - [ ] Add backward compatibility wrappers

- [ ] **2.6 Deduplication: Update Extraction Steps**
  - [ ] Update `ExtractDomainModelsStep` to use new AST framework
  - [ ] Update `ExtractEnumsStep` to use new AST framework
  - [ ] Update `ExtractGraphQLOperationsStep` to use new AST framework
  - [ ] Update `ExtractGraphQLTypesStep` to use new AST framework
  - [ ] Remove duplicated AST traversal logic
  - [ ] Remove duplicated file filtering logic

- [ ] **2.7 Testing & Validation**
  - [ ] Write unit tests for AST walker
  - [ ] Write unit tests for filters
  - [ ] Write unit tests for extractors
  - [ ] Test with real TypeScript AST data
  - [ ] Verify extraction results match old implementation
  - [ ] Update documentation with new AST framework

**Estimated Reduction**: ~15-20% code reduction in extraction logic

---

## Phase 3: Type System Consolidation

**Objective**: Merge three separate type conversion systems into one unified, configuration-driven system.

### Tasks

- [ ] **3.1 Create `ir_builders/type_system_unified/` module**
  - [ ] Create module directory and `__init__.py`
  - [ ] Design unified type conversion interface
  - [ ] Design configuration schema for type mappings
  - [ ] Create YAML configuration structure

- [ ] **3.2 Analyze Current Type Systems**
  - [ ] Document all conversions in `TypeConverter` (type_system/converter.py)
  - [ ] Document all conversions in `TypeConversionFilters` (templates/filters/)
  - [ ] Document all conversions in `StrawberryTypeResolver` (type_resolver.py)
  - [ ] Identify overlapping logic
  - [ ] Identify unique logic in each system
  - [ ] Create mapping matrix

- [ ] **3.3 Create Configuration Files**
  - [ ] Create `type_mappings.yaml` with all TypeScript → Python mappings
  - [ ] Create `graphql_mappings.yaml` with all GraphQL → Python mappings
  - [ ] Create `branded_types.yaml` with branded type definitions
  - [ ] Create `special_fields.yaml` with field-specific overrides
  - [ ] Create `strawberry_mappings.yaml` with Strawberry-specific rules
  - [ ] Add validation schema for configuration files

- [ ] **3.4 Implement `type_system_unified/converter.py`**
  - [ ] Implement `UnifiedTypeConverter` class
  - [ ] Add configuration loading from YAML
  - [ ] Implement `ts_to_python()` with config-driven logic
  - [ ] Implement `python_to_ts()` conversion
  - [ ] Implement `graphql_to_python()` with config-driven logic
  - [ ] Implement `python_to_graphql()` conversion
  - [ ] Implement `ts_to_strawberry()` for GraphQL schema
  - [ ] Add caching layer for performance
  - [ ] Add fallback logic for unmapped types

- [ ] **3.5 Implement `type_system_unified/registry.py`**
  - [ ] Create `TypeRegistry` for runtime type registration
  - [ ] Add methods for registering custom types
  - [ ] Add methods for registering branded types
  - [ ] Add methods for registering enum types
  - [ ] Add type lookup and validation
  - [ ] Add type hierarchy support

- [ ] **3.6 Implement `type_system_unified/resolver.py`**
  - [ ] Create `UnifiedTypeResolver` (merge StrawberryTypeResolver logic)
  - [ ] Add field resolution with context awareness
  - [ ] Add conversion method generation
  - [ ] Add import statement generation
  - [ ] Add default value generation
  - [ ] Integrate with UnifiedTypeConverter

- [ ] **3.7 Deduplication: Migrate from `TypeConverter`**
  - [ ] Identify all usage points of `TypeConverter` in codebase
  - [ ] Replace with `UnifiedTypeConverter` in extraction steps
  - [ ] Replace in transform steps
  - [ ] Replace in template filters
  - [ ] Verify identical output
  - [ ] Mark `TypeConverter` as deprecated

- [ ] **3.8 Deduplication: Migrate from `TypeConversionFilters`**
  - [ ] Identify all template usage of `TypeConversionFilters`
  - [ ] Create filter adapters for template compatibility
  - [ ] Update Jinja2 filter registration
  - [ ] Replace filter calls in templates
  - [ ] Verify generated code is identical
  - [ ] Remove duplicated conversion logic

- [ ] **3.9 Deduplication: Migrate from `StrawberryTypeResolver`**
  - [ ] Identify usage in `type_resolver.py`
  - [ ] Move scalar mappings to configuration
  - [ ] Move JSON type detection to configuration
  - [ ] Move manual conversion types to configuration
  - [ ] Integrate resolver logic into `UnifiedTypeResolver`
  - [ ] Update Strawberry template to use unified system
  - [ ] Remove `StrawberryTypeResolver` class

- [ ] **3.10 Testing & Validation**
  - [ ] Write comprehensive unit tests for `UnifiedTypeConverter`
  - [ ] Test all TypeScript → Python conversions
  - [ ] Test all GraphQL → Python conversions
  - [ ] Test all Strawberry-specific conversions
  - [ ] Test with edge cases (unions, literals, branded types)
  - [ ] Run full codegen and compare outputs
  - [ ] Performance benchmarks vs old system
  - [ ] Update documentation with new type system

**Estimated Reduction**: ~30-35% code reduction in type conversion logic

---

## Phase 4: Field Processing Module

**Objective**: Consolidate duplicated field transformation and processing logic.

### Tasks

- [ ] **4.1 Create `ir_builders/field_processing/` module**
  - [ ] Create module directory and `__init__.py`
  - [ ] Design field processing interfaces
  - [ ] Design transformation pipeline

- [ ] **4.2 Implement `field_processing/transformer.py`**
  - [ ] Create `FieldTransformer` class
  - [ ] Implement `transform_property()` method
  - [ ] Implement `transform_variable()` method
  - [ ] Implement `transform_field()` method
  - [ ] Implement `transform_graphql_field()` method
  - [ ] Add type conversion integration
  - [ ] Add validation integration

- [ ] **4.3 Implement `field_processing/normalizer.py`**
  - [ ] Create `FieldNormalizer` class
  - [ ] Implement field name normalization (camelCase, snake_case, etc.)
  - [ ] Implement type normalization
  - [ ] Implement default value normalization
  - [ ] Add optional/required field handling

- [ ] **4.4 Implement `field_processing/validator.py`**
  - [ ] Create `FieldValidator` class
  - [ ] Implement field schema validation
  - [ ] Implement type compatibility validation
  - [ ] Implement required field validation
  - [ ] Add custom validation rules support

- [ ] **4.5 Deduplication: Extract from `domain_models.py`**
  - [ ] Extract `_convert_property_to_field` → `FieldTransformer.transform_property`
  - [ ] Extract field type conversion logic
  - [ ] Extract field description handling
  - [ ] Update `ExtractDomainModelsStep` to use `FieldTransformer`
  - [ ] Remove duplicated logic

- [ ] **4.6 Deduplication: Extract from `graphql_operations.py`**
  - [ ] Extract `_transform_variables` → `FieldTransformer.transform_variable`
  - [ ] Extract `_transform_fields` → `FieldTransformer.transform_field`
  - [ ] Extract `_build_variable_declarations` to transformer
  - [ ] Extract `_build_field_selections` to transformer
  - [ ] Update `ExtractGraphQLOperationsStep` to use new transformer
  - [ ] Remove duplicated logic

- [ ] **4.7 Deduplication: Extract from `ui_configs.py`**
  - [ ] Extract field config generation logic
  - [ ] Extract TypeScript model field generation
  - [ ] Consolidate with `FieldTransformer`
  - [ ] Update UI config steps to use unified transformer

- [ ] **4.8 Testing & Validation**
  - [ ] Write unit tests for `FieldTransformer`
  - [ ] Write unit tests for `FieldNormalizer`
  - [ ] Write unit tests for `FieldValidator`
  - [ ] Test with real field definitions
  - [ ] Verify IR outputs are identical
  - [ ] Update documentation

**Estimated Reduction**: ~20-25% code reduction in field processing logic

---

## Phase 5: Enhanced Dependency Management

**Objective**: Improve step dependency management with decorators and better validation.

### Tasks

- [ ] **5.1 Design Dependency Decorator System**
  - [ ] Design `@depends_on` decorator interface
  - [ ] Design automatic dependency injection
  - [ ] Design dependency validation rules

- [ ] **5.2 Implement `core/decorators.py`**
  - [ ] Implement `@depends_on` decorator
  - [ ] Implement `@optional_dependency` decorator
  - [ ] Implement `@inject_dependencies` for automatic injection
  - [ ] Add dependency metadata tracking
  - [ ] Add dependency cycle detection

- [ ] **5.3 Enhance `core/steps.py`**
  - [ ] Add support for dependency decorators
  - [ ] Add automatic dependency injection in `execute()`
  - [ ] Add dependency validation in `PipelineOrchestrator`
  - [ ] Add circular dependency detection
  - [ ] Add missing dependency detection
  - [ ] Improve error messages for dependency issues

- [ ] **5.4 Deduplication: Update Existing Steps**
  - [ ] Add `@depends_on` to transform steps
  - [ ] Add `@depends_on` to assembler steps
  - [ ] Add `@depends_on` to validator steps
  - [ ] Remove manual dependency management code
  - [ ] Remove manual context data fetching
  - [ ] Simplify step execute methods

- [ ] **5.5 Testing & Validation**
  - [ ] Write tests for dependency decorators
  - [ ] Write tests for dependency injection
  - [ ] Write tests for cycle detection
  - [ ] Test with complex dependency graphs
  - [ ] Update documentation

**Estimated Reduction**: ~10-15% code reduction in dependency management

---

## Phase 6: Common Patterns Library

**Objective**: Extract frequently used patterns into reusable mixins and utilities.

### Tasks

- [ ] **6.1 Create `ir_builders/common/` module**
  - [ ] Create module directory and `__init__.py`
  - [ ] Identify common patterns across all steps
  - [ ] Design mixin interfaces

- [ ] **6.2 Implement `common/mixins.py`**
  - [ ] Implement `DeduplicationMixin` with set-based deduplication
  - [ ] Implement `ErrorHandlingMixin` with consistent error formatting
  - [ ] Implement `MetadataGeneratorMixin` for consistent metadata
  - [ ] Implement `CachingMixin` for step-level caching
  - [ ] Implement `LoggingMixin` for consistent logging
  - [ ] Implement `ValidationMixin` for input validation

- [ ] **6.3 Implement `common/patterns.py`**
  - [ ] Define common file patterns (node specs, domain models, etc.)
  - [ ] Define naming conventions (camelCase, snake_case conversions)
  - [ ] Define default values for common types
  - [ ] Define common field names and their types
  - [ ] Define common validation rules

- [ ] **6.4 Implement `common/constants.py`**
  - [ ] Move hardcoded strings to constants
  - [ ] Move magic numbers to named constants
  - [ ] Move file patterns to constants
  - [ ] Move type mappings to constants (reference to config)
  - [ ] Add constant documentation

- [ ] **6.5 Deduplication: Apply Mixins to Steps**
  - [ ] Add `DeduplicationMixin` to extraction steps
  - [ ] Add `ErrorHandlingMixin` to all steps
  - [ ] Add `MetadataGeneratorMixin` to assembler steps
  - [ ] Add `LoggingMixin` to complex steps
  - [ ] Remove duplicated code from steps

- [ ] **6.6 Deduplication: Replace Hardcoded Values**
  - [ ] Replace file patterns with constants
  - [ ] Replace naming convention logic with pattern utilities
  - [ ] Replace default values with pattern utilities
  - [ ] Replace validation logic with validation mixin

- [ ] **6.7 Testing & Validation**
  - [ ] Write tests for each mixin
  - [ ] Write tests for pattern utilities
  - [ ] Test mixin composition
  - [ ] Verify no behavior changes
  - [ ] Update documentation

**Estimated Reduction**: ~10-15% code reduction through pattern consolidation

---

## Cross-Phase Tasks

### Documentation

- [ ] **Create comprehensive refactoring documentation**
  - [ ] Document new architecture in `ARCHITECTURE.md`
  - [ ] Update `CLAUDE.md` with new module structure
  - [ ] Create migration guide for contributors
  - [ ] Add examples for each new base class
  - [ ] Add examples for using new type system
  - [ ] Create troubleshooting guide

- [ ] **Update code generation guide**
  - [ ] Update `docs/projects/code-generation-guide.md`
  - [ ] Add section on base step classes
  - [ ] Add section on AST framework
  - [ ] Add section on unified type system
  - [ ] Add section on field processing
  - [ ] Add examples of creating custom steps

### Testing

- [ ] **Create comprehensive test suite**
  - [ ] Unit tests for all new base classes
  - [ ] Unit tests for all new utilities
  - [ ] Integration tests for refactored builders
  - [ ] End-to-end tests for full codegen pipeline
  - [ ] Regression tests comparing old vs new outputs
  - [ ] Performance benchmarks

- [ ] **Create golden fixtures**
  - [ ] Capture outputs from current implementation
  - [ ] Create test fixtures for edge cases
  - [ ] Add fixture validation tests

### Migration

- [ ] **Deprecation strategy**
  - [ ] Mark old modules as deprecated with clear warnings
  - [ ] Add deprecation timeline (1-2 releases)
  - [ ] Create backward compatibility wrappers
  - [ ] Add migration utilities for automated refactoring

- [ ] **Gradual rollout**
  - [ ] Phase 1: Deploy base steps (lowest risk)
  - [ ] Phase 2: Deploy AST framework
  - [ ] Phase 3: Deploy unified type system (highest impact)
  - [ ] Phase 4: Deploy field processing
  - [ ] Phase 5: Deploy dependency management
  - [ ] Phase 6: Deploy common patterns
  - [ ] Final: Remove deprecated code

### Code Review & Quality

- [ ] **Code review checklist**
  - [ ] Verify no behavior changes in IR outputs
  - [ ] Verify performance is equal or better
  - [ ] Verify backward compatibility
  - [ ] Verify test coverage > 80%
  - [ ] Verify documentation is complete
  - [ ] Verify examples work correctly

---

## Success Metrics

### Quantitative
- [ ] **Code Reduction**: Achieve 40% reduction in duplicated code
- [ ] **Test Coverage**: Maintain or improve test coverage (target: 85%+)
- [ ] **Performance**: No regression in codegen time (target: ±5%)
- [ ] **Lines of Code**: Reduce total LOC in codegen module by 30-40%

### Qualitative
- [ ] **Maintainability**: Easier to add new IR builders
- [ ] **Clarity**: Clearer separation of concerns
- [ ] **Consistency**: Uniform patterns across all steps
- [ ] **Documentation**: Complete and accurate documentation
- [ ] **Developer Experience**: Positive feedback from contributors

---

## Notes

### Implementation Order Rationale
1. **Phase 1 first**: High impact, low risk, immediate value
2. **Phase 4 second**: High duplication reduction in field processing
3. **Phase 2 third**: Foundation for cleaner extraction
4. **Phase 3 fourth**: Significant consolidation, but higher risk
5. **Phase 5 fifth**: Quality of life improvement
6. **Phase 6 last**: Final polish and consolidation

### Risk Mitigation
- Keep old code alongside new during migration
- Comprehensive regression testing at each phase
- Gradual rollout with ability to rollback
- Backward compatibility wrappers for smooth transition

### Timeline Estimate
- **Phase 1**: 1-2 weeks
- **Phase 2**: 2-3 weeks
- **Phase 3**: 3-4 weeks (most complex)
- **Phase 4**: 1-2 weeks
- **Phase 5**: 1 week
- **Phase 6**: 1-2 weeks
- **Total**: 9-14 weeks for complete refactoring

### Deduplication Impact Summary
- **Phase 1**: ~25-30% reduction in step modules
- **Phase 2**: ~15-20% reduction in extraction logic
- **Phase 3**: ~30-35% reduction in type conversion logic
- **Phase 4**: ~20-25% reduction in field processing
- **Phase 5**: ~10-15% reduction in dependency management
- **Phase 6**: ~10-15% reduction through pattern consolidation
- **Overall**: ~40% total reduction in duplicated code