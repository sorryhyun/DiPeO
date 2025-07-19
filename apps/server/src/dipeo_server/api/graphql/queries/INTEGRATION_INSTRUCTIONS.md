# Entity Code Generation - Integration Instructions

## Generated Files

The following files have been generated:

### Mutations
- mutations/person_mutation.py
- mutations/node_mutation.py
- mutations/handle_mutation.py
- mutations/execution_mutation.py
- mutations/diagram_mutation.py
- mutations/arrow_mutation.py
- mutations/apikey_mutation.py

### Query Methods  
- queries/execution_queries.py
- queries/apikey_queries.py

### Types
- generated_types_additions.py (merge into generated_types.py)

## Integration Steps

### 1. Update mutations/__init__.py

Add imports:
```python
from .person_mutation import PersonMutations
from .node_mutation import NodeMutations
from .handle_mutation import HandleMutations
from .execution_mutation import ExecutionMutations
from .diagram_mutation import DiagramMutations
from .arrow_mutation import ArrowMutations
from .apikey_mutation import ApiKeyMutations
```

Update the Mutation class inheritance:
```python
@strawberry.type
class Mutation(
    ApiKeyMutations,
    DiagramMutations,
    ExecutionMutations,
    NodeMutations,
    PersonMutations,
    UploadMutations,
    PersonMutations,
    NodeMutations,
    HandleMutations,
    ExecutionMutations,
    DiagramMutations,
    ArrowMutations,
    ApiKeyMutations,
):
    """Combined GraphQL mutation type."""
    pass
```

### 2. Update queries.py

Add the query methods from the generated query files to the main Query class:
    - execution(id) -> ExecutionType
    - Executions(filter, limit, offset) -> list[ExecutionType]
    - apikey(id) -> ApiKeyType
    - ApiKeys(filter, limit, offset) -> list[ApiKeyType]

### 3. Update generated_types.py

1. Add the types from generated_types_additions.py
2. Update the __all__ export to include the new types

### 4. Create Services

Ensure these services exist in the service registry:
- diagram_service
- diagram_service
- diagram_service
- execution_service
- integrated_diagram_service
- diagram_service
- api_key_service

## Notes

- The generated code assumes services follow the pattern `{entity}_service`
- Custom logic in mutations may reference additional services (notification_service, email_service, etc.)
- Review and adjust the generated code as needed for your specific requirements
