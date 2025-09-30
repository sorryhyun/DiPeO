# Type Conversion Mapping Matrix

This document analyzes all type conversions across the three existing systems and identifies overlaps and unique logic.

## System Overview

### 1. TypeConverter (`type_system/converter.py`)
- **Purpose**: Core type conversion utilities
- **Conversions**:
  - TypeScript → Python
  - TypeScript → GraphQL
  - GraphQL → TypeScript
  - GraphQL → Python

### 2. TypeConversionFilters (`templates/filters/type_conversion_filters.py`)
- **Purpose**: Jinja2 template filters
- **Conversions**:
  - TypeScript → Python (with field context)
  - GraphQL → Python
  - TypeScript GraphQL Input → Python

### 3. StrawberryTypeResolver (`type_resolver.py`)
- **Purpose**: Strawberry GraphQL type resolution
- **Conversions**:
  - Python → Strawberry GraphQL types
  - Field-level type resolution with context

---

## TypeScript → Python Mappings

### Base Type Mappings (Common across all systems)

| TypeScript Type | TypeConverter | TypeConversionFilters | Unified Mapping |
|-----------------|---------------|----------------------|-----------------|
| `string` | `str` | `str` | `str` |
| `number` | `float` | `float` (or `int` for integer fields) | `float` (context: `int` for specific fields) |
| `boolean` | `bool` | `bool` | `bool` |
| `any` | `Any` | `Any` | `Any` |
| `unknown` | `Any` | `Any` | `Any` |
| `void` | `None` | `None` | `None` |
| `null` | `None` | `None` | `None` |
| `undefined` | `None` | `None` | `None` |
| `Date` | `datetime` | N/A | `datetime` |
| `object` | `Dict[str, Any]` | `Dict[str, Any]` | `Dict[str, Any]` |
| `Object` | `Dict[str, Any]` | N/A | `Dict[str, Any]` |
| `bigint` | N/A | `int` | `int` |
| `symbol` | N/A | `str` | `str` |
| `never` | N/A | `Any` | `Any` |

### Integer Field Detection

**TypeConversionFilters** has logic to convert `number` → `int` for specific fields:
```python
INTEGER_FIELDS = {
    "maxIteration", "sequence", "messageCount", "timeout", "timeoutSeconds",
    "durationSeconds", "maxTokens", "statusCode", "totalTokens", "promptTokens",
    "completionTokens", "input", "output", "cached", "total", "retries",
    "maxRetries", "port", "x", "y", "width", "height", "count", "index",
    "limit", "offset", "page", "pageSize", "size", "length", "version"
}
```

**Decision**: Move to configuration YAML under `field_overrides`.

### Complex Type Patterns

| Pattern | TypeConverter | TypeConversionFilters | Unified Approach |
|---------|---------------|----------------------|------------------|
| **Arrays** | | | |
| `T[]` | `List[T]` | `List[T]` | `List[T]` |
| `Array<T>` | `List[T]` | `List[T]` | `List[T]` |
| `ReadonlyArray<T>` | `Sequence[T]` | N/A | `Sequence[T]` |
| **Optional** | | | |
| `T \| undefined` | `Optional[T]` | `Optional[T]` | `Optional[T]` |
| `T \| null` | `Optional[T]` | `Optional[T]` | `Optional[T]` |
| **Unions** | | | |
| `A \| B \| C` | `Union[A, B, C]` | `Union[A, B, C]` | `Union[A, B, C]` |
| **Literals** | | | |
| `'value'` | `Literal['value']` | `Literal["value"]` | `Literal["value"]` |
| `true` | `Literal[True]` | `Literal[True]` | `Literal[True]` |
| `false` | `Literal[False]` | `Literal[False]` | `Literal[False]` |
| **Records** | | | |
| `Record<K, V>` | `Dict[K, V]` | `Dict[K, V]` | `Dict[K, V]` |
| `Map<K, V>` | N/A | `Dict[K, V]` | `Dict[K, V]` |
| **Generics** | | | |
| `Promise<T>` | `Awaitable[T]` | N/A | `Awaitable[T]` |
| `Partial<T>` | `Partial[T]` | N/A | `Partial[T]` |
| `Required<T>` | `Required[T]` | N/A | `Required[T]` |
| **Tuples** | | | |
| `[A, B, C]` | `tuple[A, B, C]` | N/A | `tuple[A, B, C]` |

### Branded Types

**TypeConverter**:
```python
def _try_branded_scalar(self, ts_type: str) -> Optional[str]:
    if "&" in ts_type and "__brand" in ts_type:
        match = re.search(r"'__brand':\s*'([^']+)'", ts_type)
        if match:
            brand = match.group(1)
            return brand if brand.endswith("ID") else brand
    return None
```

**TypeConversionFilters**:
```python
BRANDED_IDS = {
    "NodeID", "ArrowID", "HandleID", "PersonID", "ApiKeyID", "DiagramID",
    "ExecutionID", "HookID", "TaskID", "MessageID", "ConversationID",
    "AgentID", "ToolID", "FileID"
}
```

**Decision**: Move to configuration YAML under `branded_types`.

### Historical Aliases (TypeConverter only)

```python
if ts_type == "SerializedNodeOutput":
    return "SerializedEnvelope"
if ts_type == "PersonMemoryMessage":
    return "Message"
```

**Decision**: Move to configuration YAML under `type_aliases`.

---

## GraphQL Mappings

### TypeScript → GraphQL (TypeConverter)

| TypeScript | GraphQL |
|------------|---------|
| `string` | `String` |
| `number` | `Float` |
| `boolean` | `Boolean` |
| `any` | `JSONScalar` |
| `unknown` | `JSONScalar` |
| `Date` | `DateTime` |
| `Record<string, any>` | `JSONScalar` |
| `object` | `JSONScalar` |
| `T[]` | `[T]` |

### GraphQL → TypeScript (TypeConverter)

| GraphQL | TypeScript |
|---------|------------|
| `String` | `string` |
| `Int` | `number` |
| `Float` | `number` |
| `Boolean` | `boolean` |
| `ID` | `string` |
| `DateTime` | `string` |
| `JSON` | `any` |
| `JSONScalar` | `any` |
| `Upload` | `Upload` |
| `[T]` | `T[]` |

### GraphQL → Python (TypeConverter)

Implemented as:
```python
def graphql_to_python(self, graphql_type: str) -> str:
    ts_type = self.graphql_to_ts(graphql_type)
    return self.ts_to_python(ts_type)
```

---

## Strawberry Type Resolution

### Scalar Mappings (StrawberryTypeResolver)

```python
SCALAR_MAPPINGS = {
    "CliSessionID": "CliSessionIDScalar",
    "NodeID": "NodeIDScalar",
    "ArrowID": "ArrowIDScalar",
    "HandleID": "HandleIDScalar",
    "PersonID": "PersonIDScalar",
    "ApiKeyID": "ApiKeyIDScalar",
    "DiagramID": "DiagramIDScalar",
    "ExecutionID": "ExecutionIDScalar",
    "FileID": "FileIDScalar",
    "HookID": "HookIDScalar",
    "TaskID": "TaskIDScalar",
}
```

### JSON Types

```python
JSON_TYPES = {
    "JsonDict", "JsonValue", "JSONScalar",
    "Dict[str, Any]", "dict[str, Any]",
    "Dict[str, str]", "dict[str, str]",
    "Dict[str, JSONScalar]", "dict[str, JSONScalar]",
}
```

### Manual Conversion Types

Types requiring custom `from_pydantic()` methods:
```python
MANUAL_CONVERSION_TYPES = {
    "DomainDiagram", "ExecutionMetrics", "ExecutionState", "ExecutionOptions",
    "ExecutionUpdate", "ExecutionLogEntry", "DomainNode", "DomainArrow",
    "DomainPerson", "CliSession", "Message", "Conversation"
}
```

### Pydantic Decorator Types

Types that can use `@strawberry.experimental.pydantic.type`:
```python
PYDANTIC_DECORATOR_TYPES = {
    "KeepalivePayload", "ConversationMetadata", "Vec2", "DomainHandle",
    "PersonLLMConfig", "DomainApiKey", "DiagramMetadata", "NodeState",
    "NodeMetrics", "Bottleneck", "EnvelopeMeta", "SerializedEnvelope",
    "InteractivePromptData", "NodeDefinition", "File", "ToolConfig",
    "WebSearchResult", "ImageGenerationResult", "ToolOutput",
    "LLMRequestOptions", "NodeUpdate", "InteractivePrompt"
}
```

---

## TypeScript GraphQL Input → Python (TypeConversionFilters)

Special handling for GraphQL codegen input patterns:

| Pattern | Python Type |
|---------|-------------|
| `Scalars['ID']['input']` | `str` |
| `Scalars['String']['input']` | `str` |
| `Scalars['Int']['input']` | `int` |
| `Scalars['Float']['input']` | `float` |
| `Scalars['Boolean']['input']` | `bool` |
| `Scalars['DateTime']['input']` | `datetime` |
| `Scalars['JSON']['input']` | `JSON` |
| `InputMaybe<T>` | `Optional[T]` |
| `Array<T>` | `List[T]` |
| `Maybe<T>` | `Optional[T]` |

---

## Overlapping Logic

### 1. TypeScript → Python Conversion
- **TypeConverter**: Core implementation with branded scalars, unions, generics
- **TypeConversionFilters**: Adds caching, field context, integer field detection
- **Duplication**: ~70% overlap in base type mappings and array/union handling

### 2. Optional Type Detection
- **TypeConverter**: `_handle_union_type()` checks for `null`/`undefined`
- **TypeConversionFilters**: Separate `is_optional_type()` method
- **Duplication**: Same logic implemented differently

### 3. Branded ID Handling
- **TypeConverter**: `_try_branded_scalar()` with regex parsing
- **TypeConversionFilters**: `BRANDED_IDS` set with membership check
- **StrawberryTypeResolver**: `SCALAR_MAPPINGS` dict
- **Duplication**: Three different ways to handle the same thing

### 4. Default Value Generation
- **TypeConversionFilters**: `get_default_value()` method
- **StrawberryTypeResolver**: `_get_default_value()` method
- **Duplication**: Same logic for lists, dicts, optional types

---

## Unique Logic by System

### TypeConverter (Unique)
1. Historical aliases: `SerializedNodeOutput` → `SerializedEnvelope`
2. `Promise<T>` → `Awaitable[T]` conversion
3. `Partial<T>` and `Required<T>` handling
4. Tuple type conversion: `[A, B]` → `tuple[A, B]`
5. Inline object signature parsing: `{ [key: string]: Foo }`

### TypeConversionFilters (Unique)
1. Field context-aware type resolution (`python_type_with_context`)
2. Import statement generation (`get_python_imports`)
3. Empty object type inference (`infer_empty_object_type`)
4. GraphQL input pattern handling (`Scalars['Type']['input']`)
5. Type caching for performance

### StrawberryTypeResolver (Unique)
1. Field resolution with Strawberry type mapping
2. Conversion method generation for `from_pydantic()`
3. Type categorization: manual vs decorator
4. Domain model list handling (`List[Domain*]` → `List[Domain*Type]`)
5. Context-aware field conversion expressions

---

## Configuration Schema Design

Based on this analysis, the unified system should have:

### 1. `type_mappings.yaml`
```yaml
base_types:
  typescript_to_python:
    string: str
    number: float
    boolean: bool
    # ...

  typescript_to_graphql:
    string: String
    number: Float
    # ...

  graphql_to_typescript:
    String: string
    Int: number
    # ...

branded_types:
  - NodeID
  - DiagramID
  - ExecutionID
  # ...

type_aliases:
  SerializedNodeOutput: SerializedEnvelope
  PersonMemoryMessage: Message

field_overrides:
  integer_fields:
    - maxIteration
    - sequence
    - timeout
    # ...
```

### 2. `graphql_mappings.yaml`
```yaml
scalar_mappings:
  NodeID: NodeIDScalar
  DiagramID: DiagramIDScalar
  # ...

json_types:
  - JsonDict
  - JsonValue
  - JSONScalar
  - "Dict[str, Any]"
  # ...

manual_conversion_types:
  - DomainDiagram
  - ExecutionState
  # ...

pydantic_decorator_types:
  - KeepalivePayload
  - Vec2
  # ...
```

### 3. `special_fields.yaml`
```yaml
context_aware_mappings:
  method: HttpMethod
  sub_type: DBBlockSubType
  service: LLMService
  # ...

json_field_patterns:
  - data
  - variables
  - metadata
  - "*_data"
  # ...
```

---

## Estimated Code Reduction

| Component | Current LOC | Unified LOC | Reduction |
|-----------|-------------|-------------|-----------|
| TypeConverter | ~325 | ~200 (delegate to config) | 38% |
| TypeConversionFilters | ~620 | ~150 (delegate to UnifiedTypeConverter) | 76% |
| StrawberryTypeResolver | ~610 | ~300 (delegate to UnifiedTypeResolver) | 51% |
| **Total** | **~1555** | **~650 + config** | **~58%** |

Plus:
- YAML configuration: ~200 lines
- UnifiedTypeConverter: ~400 lines
- TypeRegistry: ~150 lines
- UnifiedTypeResolver: ~300 lines

**Total new system**: ~1700 lines (includes tests and documentation)
**Net reduction**: ~150-200 lines, but with much better maintainability

---

## Migration Strategy

1. ✅ Create configuration files
2. ✅ Implement UnifiedTypeConverter (consolidates TypeConverter + TypeConversionFilters)
3. ✅ Implement TypeRegistry (runtime registration)
4. ✅ Implement UnifiedTypeResolver (consolidates StrawberryTypeResolver logic)
5. Update usage:
   - Replace TypeConverter calls → UnifiedTypeConverter
   - Replace TypeConversionFilters → UnifiedTypeConverter methods
   - Replace StrawberryTypeResolver → UnifiedTypeResolver
6. Add backward compatibility wrappers
7. Mark old modules as deprecated

---

## Benefits of Unified System

1. **Single Source of Truth**: All type mappings in YAML configuration
2. **Consistency**: Same conversion logic across all use cases
3. **Maintainability**: Add new type mappings without code changes
4. **Testability**: Easy to test with different configurations
5. **Extensibility**: Runtime type registration via TypeRegistry
6. **Performance**: Centralized caching strategy
7. **Documentation**: Configuration files serve as documentation