# Naming Conventions Analysis

## Problem Statement

The DiPeO codebase exhibits systematic naming convention violations, primarily from TypeScript-to-Python code generation that preserves JavaScript naming patterns in Python code, violating PEP8 standards.

## Current State

### TypeScript Source Conventions (Correct)
```typescript
interface CodeJob {
    filePath: string;      // ✓ camelCase for TS
    functionName: string;  // ✓ correct for JavaScript
}
```

### Generated Python (Incorrect)
```python
@dataclass
class CodeJob:
    filePath: str      # ✗ Should be file_path
    functionName: str  # ✗ Should be function_name
```

### Manual Python (Mixed)
```python
# Some follow PEP8
execution_state: Dict
node_outputs: List

# Some don't
nodeId: str  # From generated code influence
retryCount: int
```

## Comprehensive Issues

### 1. Field Naming in Dataclasses

**Locations:**
- `/dipeo/diagram_generated/generated_nodes.py`
- `/dipeo/diagram_generated/domain_models.py`

**Examples:**
```python
# Current (incorrect)
filePath: Optional[str]
functionName: Optional[str]
maxRetries: int
timeoutSeconds: float
errorMessage: str

# Should be
file_path: Optional[str]
function_name: Optional[str]
max_retries: int
timeout_seconds: float
error_message: str
```

### 2. Service Registry Keys

**Location:** `/dipeo/application/registry/keys.py`

**Inconsistent patterns:**
```python
# Underscore style
LLM_SERVICE = ServiceKey["LLMServicePort"]("llm_service")
EXECUTION_SERVICE = ServiceKey["ExecutionServicePort"]("execution_service")

# Dot notation style
COMPILE_DIAGRAM_USE_CASE = ServiceKey["CompileDiagramUseCase"]("diagram.use_case.compile")
EXECUTE_DIAGRAM_USE_CASE = ServiceKey["ExecuteDiagramUseCase"]("diagram.use_case.execute")

# Mixed
NODE_HANDLER_REGISTRY = ServiceKey["NodeHandlerRegistry"]("node.handler.registry")
```

### 3. GraphQL Resolver Methods

**Location:** `/dipeo/application/graphql/types/domain_types.py`

```python
# Current (matching GraphQL schema)
def nodeCount(self) -> int:
def arrowCount(self) -> int:
def lastModified(self) -> datetime:

# Python convention would be
def node_count(self) -> int:
def arrow_count(self) -> int:
def last_modified(self) -> datetime:
```

### 4. Enum Value Naming

**Mixed patterns across enums:**
```python
# Some use UPPER_CASE
class Status(Enum):
    PENDING = "pending"
    COMPLETED = "completed"

# Some use PascalCase  
class NodeType(Enum):
    CodeJob = "code-job"
    Condition = "condition"
```

## Root Causes

### 1. Direct TypeScript Translation
The code generation directly maps TypeScript field names without transformation:

**TypeScript spec:**
```typescript
{ name: "filePath", type: "string" }
```

**Python generation:**
```python
filePath: str  # Direct copy, no conversion
```

### 2. GraphQL Schema Constraints
GraphQL expects camelCase fields, influencing Python resolver naming:
```graphql
type Diagram {
    nodeCount: Int!  # Forces camelCase in resolvers
}
```

### 3. Legacy Migration
Early code used camelCase, new code tries to use snake_case, creating inconsistency.

### 4. Multi-language Team
Developers from different language backgrounds contributing without consistent guidelines.

## Refactoring Strategy

### Phase 1: Code Generation Fix

**Modify generation templates to convert naming:**

```python
def to_python_name(ts_name: str) -> str:
    # Convert camelCase to snake_case
    # filePath -> file_path
    # maxRetries -> max_retries
    return re.sub('([A-Z])', r'_\1', ts_name).lower().lstrip('_')
```

**Update template:**
```python
# Before
field_name = spec['name']

# After  
field_name = to_python_name(spec['name'])
```

### Phase 2: Service Registry Standardization

**Choose single pattern (recommend underscore):**
```python
# Standardize all to underscore
COMPILE_DIAGRAM_USE_CASE = ServiceKey["CompileDiagramUseCase"]("compile_diagram_use_case")
EXECUTE_DIAGRAM_USE_CASE = ServiceKey["ExecuteDiagramUseCase"]("execute_diagram_use_case")
NODE_HANDLER_REGISTRY = ServiceKey["NodeHandlerRegistry"]("node_handler_registry")
```

### Phase 3: GraphQL Resolver Adaptation

**Use field aliases for GraphQL compatibility:**
```python
class DiagramType:
    @property
    def node_count(self) -> int:  # Python convention
        return len(self.nodes)
    
    # GraphQL field mapping
    nodeCount = node_count  # Alias for GraphQL
```

Or use Strawberry's field naming:
```python
@strawberry.type
class Diagram:
    node_count: int = strawberry.field(name="nodeCount")
```

### Phase 4: Backward Compatibility

**Provide aliases during transition:**
```python
@dataclass
class CodeJob:
    file_path: str
    function_name: str
    
    # Temporary compatibility
    @property
    def filePath(self) -> str:
        warnings.warn("Use file_path instead", DeprecationWarning)
        return self.file_path
    
    @property  
    def functionName(self) -> str:
        warnings.warn("Use function_name instead", DeprecationWarning)
        return self.function_name
```

## Implementation Plan

### Immediate Actions (Week 1)
1. Update code generation templates
2. Add naming convention linter rules
3. Document standards in CONTRIBUTING.md

### Short-term (Weeks 2-3)
1. Regenerate all code with proper naming
2. Update service registry keys
3. Fix GraphQL resolvers with aliases

### Medium-term (Weeks 4-5)
1. Update all manual code to follow conventions
2. Add deprecation warnings for old names
3. Update tests and documentation

### Long-term (Week 6+)
1. Remove compatibility aliases
2. Enforce conventions in CI/CD
3. Regular audits for consistency

## Tooling & Automation

### Linting Configuration

**Add to `.pre-commit-config.yaml`:**
```yaml
- repo: local
  hooks:
    - id: check-naming
      name: Check Python naming conventions
      entry: scripts/check_naming.py
      language: python
      files: \.py$
```

**Ruff configuration:**
```toml
[tool.ruff]
select = ["N"]  # pep8-naming

[tool.ruff.pep8-naming]
classmethod-decorators = ["classmethod", "strawberry.field"]
```

### Automated Conversion Script

```python
# scripts/fix_naming.py
import ast
import re

def convert_camel_to_snake(name: str) -> str:
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

def fix_dataclass_fields(source: str) -> str:
    # Parse and fix field names
    tree = ast.parse(source)
    # ... transformation logic
    return ast.unparse(tree)
```

## Expected Outcomes

### Quantitative Metrics
- 100% PEP8 compliance for naming
- 0 camelCase fields in Python code
- Consistent service registry keys
- All GraphQL resolvers properly mapped

### Qualitative Benefits
- Better IDE autocomplete
- Clearer code for Python developers
- Easier onboarding
- Reduced cognitive load
- Professional codebase appearance

## Migration Timeline

### v0.9.0 (Week 2)
- New code generation with proper naming
- Compatibility aliases added
- Deprecation warnings enabled

### v0.9.5 (Week 4)
- All manual code updated
- Documentation updated
- Linting enforced for new code

### v1.0.0 (Week 6)
- Compatibility aliases removed
- Full PEP8 compliance
- Strict linting in CI/CD

## Risk Mitigation

### Risk: Breaking API Changes
**Mitigation:** Provide compatibility aliases, deprecation period

### Risk: GraphQL Schema Incompatibility  
**Mitigation:** Use field aliases to maintain schema

### Risk: Large Diff Churn
**Mitigation:** Automated tools, incremental migration

### Risk: External Integration Issues
**Mitigation:** Document changes, provide migration guide

## Conclusion

Naming convention inconsistencies stem primarily from the code generation process. By fixing the generation templates and providing a clear migration path with compatibility aliases, we can achieve PEP8 compliance without breaking existing functionality. The key is automation and gradual transition with clear deprecation warnings.