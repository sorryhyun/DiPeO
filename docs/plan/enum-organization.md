# Enum Organization Analysis

## Problem Statement

The DiPeO codebase has well-structured auto-generated enums from TypeScript but suffers from duplicate definitions, inconsistent organization of manual enums, and unclear boundaries between generated and custom enumerations.

## Current Architecture

### Three-Tier Enum System

```
TypeScript Sources (dipeo/models/src/)
           ↓ (code generation)
Generated Python Enums (dipeo/diagram_generated/enums.py)
           ↓ (imports/extends)  
Manual Python Enums (domain/*, infrastructure/*)
```

### Generated Enums (Source of Truth)

**Location:** `/dipeo/diagram_generated/enums.py`

**20 Core Enums:**
```python
# Data & Types
class DataType(str, Enum)
class ContentType(str, Enum)

# Execution
class NodeStatus(str, Enum)
class ExecutionStatus(str, Enum)

# Node Types
class NodeType(str, Enum)
class NodeCategory(str, Enum)

# Services
class LLMService(str, Enum)
class APIServiceType(str, Enum)

# ... 12 more
```

### Manual Domain Enums

**Scattered across modules:**

```python
# dipeo/domain/execution/execution_tracker.py
class FlowStatus(Enum):
    WAITING = "waiting"
    READY = "ready"
    
class CompletionStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"

# dipeo/domain/events/types.py  
class EventPriority(Enum):
    LOW = 1
    HIGH = 3

# dipeo/domain/base/validator.py
class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
```

## Key Issues

### 1. Duplicate RetryStrategy Definitions

**Three separate definitions:**

```python
# Location 1: dipeo/domain/integrations/api_value_objects/retry_policy.py
class RetryStrategy(Enum):
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    CONSTANT_DELAY = "constant_delay"

# Location 2: dipeo/infrastructure/integrations/drivers/integrated_api/manifest_schema.py
class RetryStrategy(str, Enum):
    exponential = "exponential"
    linear = "linear"
    fixed = "fixed"
    
# Location 3: Referenced but not defined consistently
```

**Problems:**
- Different value names for same concept
- Import conflicts
- Maintenance burden

### 2. Service Type Proliferation

**Multiple overlapping definitions:**

```python
# Generated
class LLMService(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    
class APIServiceType(str, Enum):
    OPENAI = "openai"
    GOOGLE = "google"

# Manual
class LLMServiceName(Enum):
    GPT_4 = "gpt-4"
    CLAUDE = "claude"
    
class ProviderType(Enum):
    OPENAI = "OpenAI"
    ANTHROPIC = "Anthropic"
```

### 3. Execution Phase Duplication

```python
# dipeo/infrastructure/llm/core/types.py
class ExecutionPhase(Enum):
    INITIALIZE = "initialize"
    EXECUTE = "execute"
    FINALIZE = "finalize"

# dipeo/infrastructure/integrations/claude_code/adapter.py  
class ClaudeCodeExecutionPhase(Enum):
    PRE_EXECUTION = "pre_execution"
    EXECUTION = "execution"
    POST_EXECUTION = "post_execution"
```

### 4. Inconsistent Naming Conventions

**Mixed patterns:**
```python
# Some use UPPER_CASE with lowercase values
class Status(Enum):
    PENDING = "pending"
    
# Some use UPPER_CASE with integer values
class Priority(Enum):
    HIGH = 1
    
# Some use PascalCase members (incorrect)
class NodeType(Enum):
    CodeJob = "code-job"  # Should be CODE_JOB
```

### 5. Scattered Related Enums

**Example: Execution-related enums in 4+ locations:**
- `NodeStatus` in generated
- `ExecutionStatus` in generated  
- `FlowStatus` in execution_tracker
- `CompletionStatus` in execution_tracker
- `ExecutionPhase` in infrastructure

## Refactoring Strategy

### Step 1: Consolidation Map

**Create unified enum hierarchy:**

```python
# In TypeScript sources (to be generated)
enums/
  core/
    - node_types.ts (all node-related)
    - execution.ts (all execution states)
    - services.ts (all service types)
  domain/
    - events.ts (event types, priorities)
    - validation.ts (severities, rules)
  infrastructure/
    - retry.ts (retry strategies)
    - providers.ts (provider configs)
```

### Step 2: Merge Duplicate Definitions

**RetryStrategy Consolidation:**
```python
# Single definition in TypeScript
enum RetryStrategy {
  EXPONENTIAL_BACKOFF = "exponential_backoff",
  LINEAR_BACKOFF = "linear_backoff",
  CONSTANT_DELAY = "constant_delay",
  NONE = "none"
}
```

**Service Types Consolidation:**
```python
# Unified service enum
enum ServiceProvider {
  OPENAI = "openai",
  ANTHROPIC = "anthropic",
  GOOGLE = "google",
  AZURE = "azure"
}

enum ServiceType {
  LLM = "llm",
  EMBEDDING = "embedding",
  SEARCH = "search"
}
```

### Step 3: Standardize Naming

**Enforce conventions:**
```python
class EnumName(str, Enum):  # PascalCase class
    MEMBER_NAME = "value"    # UPPER_SNAKE_CASE members
    ANOTHER_ONE = "value2"   # Consistent style
```

### Step 4: Create Migration Aliases

**For backward compatibility:**
```python
# Old location (deprecated)
from dipeo.diagram_generated.enums import RetryStrategy

# Add deprecation warning
import warnings

class RetryStrategy(RetryStrategy):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "Import from diagram_generated.enums instead",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)
```

### Step 5: Document Organization

**Create enum guidelines:**
```markdown
## Enum Organization Rules

1. **Core System Enums**: Define in TypeScript, generate to Python
2. **Domain-Specific**: Keep in Python if truly domain-only
3. **Infrastructure**: Evaluate for promotion to core
4. **Naming**: UPPER_SNAKE_CASE members always
5. **Values**: Lowercase strings for consistency
```

## Implementation Plan

### Phase 1: Analysis & Planning (Day 1-2)
1. Complete enum inventory
2. Create consolidation mapping
3. Identify true duplicates vs similar concepts

### Phase 2: TypeScript Updates (Day 3-4)
1. Reorganize TypeScript enum sources
2. Add missing core enums
3. Fix naming conventions in sources

### Phase 3: Generation Update (Day 5)
1. Regenerate Python enums
2. Verify all imports still work
3. Add compatibility imports

### Phase 4: Manual Enum Cleanup (Day 6-7)
1. Remove duplicate manual definitions
2. Update imports to use generated versions
3. Consolidate related enums

### Phase 5: Documentation (Day 8)
1. Document enum organization
2. Create migration guide
3. Update developer guidelines

## Migration Examples

### Before (Scattered)
```python
# File 1
from dipeo.domain.integrations.api_value_objects.retry_policy import RetryStrategy

# File 2  
from dipeo.infrastructure.integrations.drivers.integrated_api.manifest_schema import RetryStrategy

# Conflict!
```

### After (Unified)
```python
# All files
from dipeo.diagram_generated.enums import RetryStrategy

# Single source of truth
```

### Service Types Migration
```python
# Before
if provider == LLMService.OPENAI:
    ...
elif provider == ProviderType.OPENAI:
    ...
elif provider == "openai":
    ...

# After  
if provider == ServiceProvider.OPENAI:
    # Single, consistent check
```

## Expected Benefits

### Quantitative
- Reduce enum definitions by 40%
- Eliminate 100% of duplicates
- Single import source for core enums
- 0 naming convention violations

### Qualitative
- Clear enum organization
- No import conflicts
- Easier to find enums
- Consistent usage patterns
- Better IDE support

## Risk Mitigation

### Risk: Breaking Changes
**Mitigation:** 
- Compatibility imports during transition
- Deprecation warnings
- Phased migration

### Risk: Missing Business Logic
**Mitigation:**
- Careful analysis of enum usage
- Preserve domain-specific enums
- Review with domain experts

### Risk: Generation Overwrites
**Mitigation:**
- Never modify generated files
- All changes in TypeScript sources
- Clear separation of generated vs manual

## Special Considerations

### GraphQL Enum Mapping
```python
# Ensure GraphQL schema compatibility
@strawberry.enum
class NodeStatusGraphQL:
    PENDING = NodeStatus.PENDING.value
    RUNNING = NodeStatus.RUNNING.value
    # Map generated enums to GraphQL
```

### Database Enum Columns
```python
# Preserve database compatibility  
class ExecutionRecord:
    status = Column(
        Enum(ExecutionStatus),
        default=ExecutionStatus.PENDING
    )
    # Ensure migrations handle enum changes
```

### External API Compatibility
```python
# Maintain external API contracts
def to_external_format(internal: RetryStrategy) -> str:
    mapping = {
        RetryStrategy.EXPONENTIAL_BACKOFF: "exponential",
        RetryStrategy.LINEAR_BACKOFF: "linear",
    }
    return mapping.get(internal, internal.value)
```

## Conclusion

The enum organization can be significantly improved by consolidating duplicates, standardizing naming, and establishing clear boundaries between generated and manual enums. The key is maintaining backward compatibility while moving toward a single source of truth for each enum concept.