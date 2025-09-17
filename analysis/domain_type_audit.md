# Domain Type Simplification Audit

## Overview
This audit analyzes the Strawberry types in `dipeo/diagram_generated/graphql/domain_types.py` to identify opportunities for simplification using `@strawberry.experimental.pydantic.type` decorators and shared scalar helpers.

## Current Structure Analysis

### Total Statistics
- **File Size**: 622 lines
- **Total Strawberry Types**: 35 types
- **Types with from_pydantic methods**: 13 types
- **Simple types without conversion**: 22 types

## Types Categorization

### 1. Simple Wrapper Types (Can use @strawberry.experimental.pydantic.type)

These types directly map Pydantic fields with minimal transformation and are prime candidates for automatic conversion:

#### Types with from_pydantic but simple field mapping:
- **CliSessionType** - Direct field mapping with enum conversion for status
- **MessageType** - Direct field mapping, all simple types
- **ConversationType** - Simple nested type conversion
- **DomainNodeType** - Direct mapping with Vec2 position and enum conversion
- **DomainArrowType** - Direct mapping with enum conversion
- **DomainPersonType** - Direct mapping with enum conversion
- **KeepalivePayloadType** - Simple field mapping

#### Types without from_pydantic (already simple):
- **ConversationMetadataType** - All primitive fields
- **Vec2Type** - Simple x,y coordinates
- **DomainHandleType** - Direct field mapping with enums
- **PersonLLMConfigType** - Direct field mapping
- **DomainApiKeyType** - Direct field mapping
- **DiagramMetadataType** - All primitive/optional fields
- **LLMUsageType** - Simple numeric fields
- **NodeStateType** - Status and timestamp fields
- **NodeMetricsType** - Numeric metrics fields
- **BottleneckType** - Simple fields
- **EnvelopeMetaType** - Metadata fields
- **SerializedEnvelopeType** - Simple envelope structure
- **InteractivePromptDataType** - Direct field mapping
- **NodeDefinitionType** - Direct field mapping
- **FileType** - File metadata fields
- **ToolConfigType** - Configuration fields
- **WebSearchResultType** - Search result fields
- **ImageGenerationResultType** - Generation result fields
- **ToolOutputType** - Output fields
- **LLMRequestOptionsType** - Request option fields
- **NodeUpdateType** - Update event fields
- **InteractivePromptType** - Prompt fields

### 2. Complex Types Requiring Manual Handling

These types have complex conversion logic or nested structures that benefit from custom from_pydantic methods:

- **DomainDiagramType** - Complex nested conversion of nodes, handles, arrows, persons lists
- **ExecutionMetricsType** - Complex nested structure with metrics aggregation
- **ExecutionStateType** - Complex state management with multiple nested types
- **ExecutionOptionsType** - Complex options with nested configurations
- **ExecutionUpdateType** - Complex update structure with discriminated unions
- **ExecutionLogEntryType** - Complex log structure with nested fields

### 3. Scalar Type Usage

Current scalar imports and definitions:
```python
# Imported scalars
- CliSessionIDScalar
- NodeIDScalar
- ArrowIDScalar
- HandleIDScalar
- PersonIDScalar
- ApiKeyIDScalar
- DiagramIDScalar
- HookIDScalar (fallback to ID)
- TaskIDScalar (fallback to ID)
- ExecutionIDScalar
- FileIDScalar

# JSON scalar for complex objects
- JSONScalar (from strawberry.scalars)

# Temporary definitions
- SerializedNodeOutput = JSONScalar
```

## Recommendations

### Phase 3 Implementation Plan

1. **Create shared scalar helpers file** (`dipeo/diagram_generated/graphql/scalar_aliases.py`):
   - Consolidate all scalar type definitions
   - Remove duplicate declarations
   - Provide proper types for HookIDScalar and TaskIDScalar

2. **Update template to use @strawberry.experimental.pydantic.type**:
   - Apply to 29 simple wrapper types (listed above)
   - Keep manual definitions for 6 complex types
   - Expected line reduction: ~40-50% (approx. 250-300 lines)

3. **Template modifications needed**:
   - Add logic to detect simple vs complex types
   - Generate @strawberry.experimental.pydantic.type for simple types
   - Retain custom class definitions for complex types
   - Import scalars from shared file

4. **Validation requirements**:
   - Ensure enum conversions work with pydantic decorator
   - Verify nested type conversions
   - Test GraphQL schema generation
   - Validate TypeScript type generation

## Expected Benefits

1. **Code Reduction**: Approximately 250-300 lines removed (40-50% reduction)
2. **Maintenance**: Simpler templates, less boilerplate
3. **Consistency**: Automatic synchronization with Pydantic models
4. **Performance**: Potential performance improvements from Strawberry's optimized conversion

## Risk Assessment

- **Low Risk**: Simple types with direct field mapping
- **Medium Risk**: Types with enum conversions (need testing)
- **High Risk**: Complex nested types (keep manual conversion)

## Next Steps

1. Create scalar_aliases.py with all scalar definitions
2. Update strawberry_types.j2 template to detect type complexity
3. Implement @strawberry.experimental.pydantic.type for simple types
4. Test with make codegen and validation
5. Document any edge cases or limitations discovered
