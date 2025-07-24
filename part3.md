# Part 3: Data-Driven Codegen Architecture

## Overview

Transform the codegen system from a file-based approach to a pure data-driven approach where:
- Diagrams orchestrate the entire process using DB nodes for I/O
- Functions are pure transformations (data in → data out) 
- No file I/O or path resolution inside generator functions
- All templates and specs are loaded/saved by DB nodes
- Code lives in proper Python files, not inline in diagrams

## Current Problems

1. **Mixed Concerns**: Generators handle both logic AND file I/O
2. **Path Resolution**: Complex path resolution scattered throughout code
3. **Template Loading**: Templates loaded inside functions
4. **Hard to Test**: Can't test generators without file system
5. **Inline Code**: Complex logic embedded in YAML diagrams

## Proposed Architecture

### 1. Pure Generator Functions

```python
# files/codegen/code/generators/pure_generators.py
from jinja2 import Environment
from typing import Dict, Any
from ..utils.filters import create_template_env

def generate_typescript_model(spec_data: Dict[str, Any], template_content: str) -> str:
    """Pure function: Generate TypeScript model from spec and template."""
    env = create_template_env()
    template = env.from_string(template_content)
    return template.render(spec_data)

def generate_pydantic_model(spec_data: Dict[str, Any], template_content: str) -> str:
    """Pure function: Generate Pydantic model from spec and template."""
    env = create_template_env()
    template = env.from_string(template_content)
    return template.render(spec_data)

def generate_graphql_schema(spec_data: Dict[str, Any], template_content: str) -> str:
    """Pure function: Generate GraphQL schema from spec and template."""
    env = create_template_env()
    template = env.from_string(template_content)
    return template.render(spec_data)

def generate_node_config(spec_data: Dict[str, Any], template_content: str) -> str:
    """Pure function: Generate frontend node config from spec and template."""
    env = create_template_env()
    template = env.from_string(template_content)
    return template.render(spec_data)
```

### 2. Separated Frontend and Backend Orchestration

#### Frontend Generation Diagram

```yaml
# files/diagrams/codegen/frontend/generate_frontend_single.light.yaml
nodes:
  # Load node specification
  - label: Load Node Spec
    type: db
    position: {x: 100, y: 200}
    props:
      operation: read
      sub_type: file
      source_details: files/codegen/specifications/nodes/{node_spec_path}.json
    id: load_spec
  
  # Load frontend templates
  - label: Load TypeScript Template
    type: db
    position: {x: 100, y: 300}
    props:
      operation: read
      sub_type: file
      source_details: files/codegen/templates/frontend/typescript_model.j2
    id: load_ts_template
  
  - label: Load Node Config Template
    type: db
    position: {x: 100, y: 400}
    props:
      operation: read
      sub_type: file
      source_details: files/codegen/templates/frontend/node_config.j2
    id: load_config_template

  - label: Load Field Config Template
    type: db
    position: {x: 100, y: 500}
    props:
      operation: read
      sub_type: file
      source_details: files/codegen/templates/frontend/field_config.j2
    id: load_field_template

  # Generate frontend code
  - label: Generate TypeScript Model
    type: code_job
    position: {x: 400, y: 300}
    props:
      code_type: file
      source_details: files/codegen/code/frontend/generators/typescript_model.py
    id: gen_typescript
  
  - label: Generate Node Config
    type: code_job
    position: {x: 400, y: 400}
    props:
      code_type: file
      source_details: files/codegen/code/frontend/generators/node_config.py
    id: gen_config

  - label: Generate Field Config
    type: code_job
    position: {x: 400, y: 500}
    props:
      code_type: file
      source_details: files/codegen/code/frontend/generators/field_config.py
    id: gen_field

  # Write frontend outputs
  - label: Write TypeScript Model
    type: db
    position: {x: 700, y: 300}
    props:
      operation: write
      sub_type: file
      source_details: dipeo/models/src/nodes/{node_name}Node.ts
    id: write_ts
  
  - label: Write Node Config
    type: db
    position: {x: 700, y: 400}
    props:
      operation: write
      sub_type: file
      source_details: apps/web/src/features/diagram-editor/config/nodes/{node_name}Config.ts
    id: write_config

  - label: Write Field Config
    type: db
    position: {x: 700, y: 500}
    props:
      operation: write
      sub_type: file
      source_details: apps/web/src/core/config/fields/{node_name}Fields.ts
    id: write_field

connections:
  # Connect spec and templates to generators
  - source: Load Node Spec.out
    target: Generate TypeScript Model.spec_data
  - source: Load TypeScript Template.out
    target: Generate TypeScript Model.template_content
  
  - source: Load Node Spec.out
    target: Generate Node Config.spec_data
  - source: Load Node Config Template.out
    target: Generate Node Config.template_content

  - source: Load Node Spec.out
    target: Generate Field Config.spec_data
  - source: Load Field Config Template.out
    target: Generate Field Config.template_content
  
  # Connect generators to writers
  - source: Generate TypeScript Model.out
    target: Write TypeScript Model.in
  - source: Generate Node Config.out
    target: Write Node Config.in
  - source: Generate Field Config.out
    target: Write Field Config.in
```

#### Backend Generation Diagram

```yaml
# files/diagrams/codegen/backend/generate_backend_single.light.yaml
nodes:
  # Load node specification
  - label: Load Node Spec
    type: db
    position: {x: 100, y: 200}
    props:
      operation: read
      sub_type: file
      source_details: files/codegen/specifications/nodes/{node_spec_path}.json
    id: load_spec
  
  # Load backend templates
  - label: Load Pydantic Template
    type: db
    position: {x: 100, y: 300}
    props:
      operation: read
      sub_type: file  
      source_details: files/codegen/templates/backend/pydantic_model.j2
    id: load_py_template

  - label: Load GraphQL Template
    type: db
    position: {x: 100, y: 400}
    props:
      operation: read
      sub_type: file
      source_details: files/codegen/templates/backend/graphql_schema.j2
    id: load_gql_template

  - label: Load Static Node Template
    type: db
    position: {x: 100, y: 500}
    props:
      operation: read
      sub_type: file
      source_details: files/codegen/templates/backend/static_nodes.j2
    id: load_static_template

  # Generate backend code
  - label: Generate Pydantic Model
    type: code_job
    position: {x: 400, y: 300}
    props:
      code_type: file
      source_details: files/codegen/code/backend/generators/pydantic_model.py
    id: gen_pydantic

  - label: Generate GraphQL Schema
    type: code_job
    position: {x: 400, y: 400}
    props:
      code_type: file
      source_details: files/codegen/code/backend/generators/graphql_schema.py
    id: gen_graphql

  - label: Generate Static Node
    type: code_job
    position: {x: 400, y: 500}
    props:
      code_type: file
      source_details: files/codegen/code/backend/generators/static_nodes.py
    id: gen_static

  # Write backend outputs
  - label: Write Pydantic Model
    type: db
    position: {x: 700, y: 300}
    props:
      operation: write
      sub_type: file
      source_details: dipeo/diagram_generated/models/{node_name}_model.py
    id: write_py

  - label: Write GraphQL Schema
    type: db
    position: {x: 700, y: 400}
    props:
      operation: write
      sub_type: file
      source_details: apps/server/src/graphql/schemas/{node_name}.graphql
    id: write_gql

  - label: Write Static Node
    type: db
    position: {x: 700, y: 500}
    props:
      operation: write
      sub_type: file
      source_details: dipeo/core/static/generated/{node_name}_node.py
    id: write_static

connections:
  # Connect spec and templates to generators
  - source: Load Node Spec.out
    target: Generate Pydantic Model.spec_data
  - source: Load Pydantic Template.out
    target: Generate Pydantic Model.template_content
  
  - source: Load Node Spec.out
    target: Generate GraphQL Schema.spec_data
  - source: Load GraphQL Template.out
    target: Generate GraphQL Schema.template_content

  - source: Load Node Spec.out
    target: Generate Static Node.spec_data
  - source: Load Static Node Template.out
    target: Generate Static Node.template_content
  
  # Connect generators to writers
  - source: Generate Pydantic Model.out
    target: Write Pydantic Model.in
  - source: Generate GraphQL Schema.out
    target: Write GraphQL Schema.in
  - source: Generate Static Node.out
    target: Write Static Node.in
```

### 3. New Module Structure

```
files/codegen/
├── code/
│   ├── frontend/                    # Frontend-specific generators
│   │   ├── __init__.py
│   │   ├── generators/
│   │   │   ├── typescript_model.py
│   │   │   ├── node_config.py
│   │   │   ├── node_registry.py
│   │   │   └── field_config.py
│   │   └── utils/
│   │       ├── typescript_mapper.py
│   │       └── react_helpers.py
│   ├── backend/                     # Backend-specific generators
│   │   ├── __init__.py
│   │   ├── generators/
│   │   │   ├── pydantic_model.py
│   │   │   ├── graphql_schema.py
│   │   │   ├── static_nodes.py
│   │   │   └── conversions.py
│   │   └── utils/
│   │       ├── python_mapper.py
│   │       └── pydantic_helpers.py
│   └── shared/                      # Shared utilities
│       ├── __init__.py
│       ├── spec_loader.py
│       ├── template_env.py
│       └── filters.py              # Common Jinja2 filters
├── templates/
│   ├── backend/
│   │   ├── pydantic_model.j2
│   │   ├── graphql_schema.j2
│   │   ├── static_nodes.j2
│   │   └── conversions.j2
│   └── frontend/
│       ├── typescript_model.j2
│       ├── node_config.j2
│       ├── node_registry.j2
│       └── field_config.j2
├── specifications/nodes/           # Node specifications
├── manifests/                      # Generation manifests
│   ├── frontend.json              # Frontend generation config
│   ├── backend.json               # Backend generation config
│   └── all.json                   # Complete generation config
└── diagrams/                       # Orchestration diagrams
    ├── frontend/
    │   ├── generate_frontend_single.light.yaml
    │   └── generate_frontend_all.light.yaml
    ├── backend/
    │   ├── generate_backend_single.light.yaml
    │   └── generate_backend_all.light.yaml
    └── master/
        ├── generate_all.light.yaml
        └── validate_specs.light.yaml
```

### 4. Frontend and Backend Separation

#### Frontend Generators

##### TypeScript Model Generator
```python
# files/codegen/code/frontend/generators/typescript_model.py
from jinja2 import Environment
from ..utils.typescript_mapper import map_to_typescript_type
from ...shared.template_env import create_template_env

def generate_typescript_model(spec_data: dict, template_content: str) -> str:
    """Pure function: Generate TypeScript model from spec."""
    env = create_template_env()
    
    # Transform spec for TypeScript
    ts_spec = {
        **spec_data,
        'imports': _calculate_imports(spec_data),
        'type_mappings': {
            field['name']: map_to_typescript_type(field['type'])
            for field in spec_data.get('fields', [])
        }
    }
    
    template = env.from_string(template_content)
    return template.render(ts_spec)

def main(inputs):
    """Entry point for code_job node."""
    return {
        'generated_code': generate_typescript_model(
            inputs['spec_data'], 
            inputs['template_content']
        ),
        'filename': f"{inputs['spec_data']['type']}Node.ts"
    }
```

##### Node Config Generator
```python
# files/codegen/code/frontend/generators/node_config.py
from ...shared.template_env import create_template_env

def generate_node_config(spec_data: dict, template_content: str) -> str:
    """Pure function: Generate frontend node configuration."""
    env = create_template_env()
    
    # Add UI-specific transformations
    config_spec = {
        **spec_data,
        'field_groups': _group_fields_by_category(spec_data),
        'default_values': _calculate_default_values(spec_data)
    }
    
    template = env.from_string(template_content)
    return template.render(config_spec)
```

#### Backend Generators

##### Pydantic Model Generator
```python
# files/codegen/code/backend/generators/pydantic_model.py
from ...shared.template_env import create_template_env
from ..utils.python_mapper import map_to_python_type

def generate_pydantic_model(spec_data: dict, template_content: str) -> str:
    """Pure function: Generate Pydantic model from spec."""
    env = create_template_env()
    
    # Transform spec for Python/Pydantic
    py_spec = {
        **spec_data,
        'imports': _calculate_python_imports(spec_data),
        'type_mappings': {
            field['name']: map_to_python_type(field['type'])
            for field in spec_data.get('fields', [])
        },
        'validators': _build_validators(spec_data)
    }
    
    template = env.from_string(template_content)
    return template.render(py_spec)

def main(inputs):
    """Entry point for code_job node."""
    return {
        'generated_code': generate_pydantic_model(
            inputs['spec_data'],
            inputs['template_content']
        ),
        'filename': f"{inputs['spec_data']['type']}_model.py"
    }
```

##### Static Nodes Generator
```python
# files/codegen/code/backend/generators/static_nodes.py
from ...shared.template_env import create_template_env

def generate_static_node(spec_data: dict, template_content: str) -> str:
    """Pure function: Generate static node implementation."""
    env = create_template_env()
    
    # Add execution-specific data
    node_spec = {
        **spec_data,
        'handler_class': f"{spec_data['type'].title()}NodeHandler",
        'execution_logic': _build_execution_logic(spec_data)
    }
    
    template = env.from_string(template_content)
    return template.render(node_spec)
```

### 5. Master Orchestrator with Separated Frontend/Backend

```yaml
# files/diagrams/codegen/master/generate_all.light.yaml
nodes:
  - label: Load Generation Manifest
    type: db
    position: {x: 100, y: 300}
    props:
      operation: read
      sub_type: file
      source_details: files/codegen/manifests/all.json
    id: load_manifest

  - label: Process Manifest
    type: code_job
    position: {x: 300, y: 300}
    props:
      code_type: file
      source_details: files/codegen/code/shared/manifest_processor.py
    id: process_manifest

  # Frontend and Backend sub-diagrams
  - label: Generate All Frontend
    type: sub_diagram
    position: {x: 500, y: 200}
    props:
      diagram_path: codegen/frontend/generate_frontend_all
    id: gen_frontend

  - label: Generate All Backend
    type: sub_diagram
    position: {x: 500, y: 400}
    props:
      diagram_path: codegen/backend/generate_backend_all
    id: gen_backend

  # Registry generation (combines frontend and backend info)
  - label: Generate Node Registry
    type: code_job
    position: {x: 700, y: 300}
    props:
      code_type: file
      source_details: files/codegen/code/frontend/generators/node_registry.py
    id: gen_registry

  - label: Write Node Registry
    type: db
    position: {x: 900, y: 300}
    props:
      operation: write
      sub_type: file
      source_details: apps/web/src/features/diagram-editor/config/nodeRegistry.ts
    id: write_registry

connections:
  - source: Load Generation Manifest.out
    target: Process Manifest.in
  
  # Send node specs to frontend and backend
  - source: Process Manifest.frontend_specs
    target: Generate All Frontend.in
  - source: Process Manifest.backend_specs
    target: Generate All Backend.in
  
  # Registry needs results from both
  - source: Generate All Frontend.node_configs
    target: Generate Node Registry.frontend_configs
  - source: Generate All Backend.node_metadata
    target: Generate Node Registry.backend_metadata
  
  - source: Generate Node Registry.out
    target: Write Node Registry.in
```

#### Frontend Batch Generation

```yaml
# files/diagrams/codegen/frontend/generate_frontend_all.light.yaml
nodes:
  - label: Load Frontend Manifest
    type: db
    position: {x: 100, y: 100}
    props:
      operation: read
      sub_type: file
      source_details: files/codegen/manifests/frontend.json
    id: load_manifest

  - label: Batch Process Frontend
    type: code_job
    position: {x: 300, y: 100}
    props:
      code_type: file
      source_details: files/codegen/code/frontend/batch_processor.py
    id: batch_processor

  # Parallel generation for each artifact type
  - label: Generate All TypeScript Models
    type: sub_diagram
    position: {x: 500, y: 200}
    props:
      diagram_path: codegen/frontend/batch_typescript
    id: gen_ts_batch

  - label: Generate All Node Configs
    type: sub_diagram
    position: {x: 500, y: 300}
    props:
      diagram_path: codegen/frontend/batch_node_configs
    id: gen_config_batch

  - label: Generate All Field Configs
    type: sub_diagram
    position: {x: 500, y: 400}
    props:
      diagram_path: codegen/frontend/batch_field_configs
    id: gen_field_batch

connections:
  - source: Load Frontend Manifest.out
    target: Batch Process Frontend.in
  
  - source: Batch Process Frontend.typescript_tasks
    target: Generate All TypeScript Models.in
  - source: Batch Process Frontend.config_tasks
    target: Generate All Node Configs.in
  - source: Batch Process Frontend.field_tasks
    target: Generate All Field Configs.in
```

#### Backend Batch Generation

```yaml
# files/diagrams/codegen/backend/generate_backend_all.light.yaml
nodes:
  - label: Load Backend Manifest
    type: db
    position: {x: 100, y: 100}
    props:
      operation: read
      sub_type: file
      source_details: files/codegen/manifests/backend.json
    id: load_manifest

  - label: Batch Process Backend
    type: code_job
    position: {x: 300, y: 100}
    props:
      code_type: file
      source_details: files/codegen/code/backend/batch_processor.py
    id: batch_processor

  # Parallel generation for each artifact type
  - label: Generate All Pydantic Models
    type: sub_diagram
    position: {x: 500, y: 200}
    props:
      diagram_path: codegen/backend/batch_pydantic
    id: gen_pydantic_batch

  - label: Generate All GraphQL Schemas
    type: sub_diagram
    position: {x: 500, y: 300}
    props:
      diagram_path: codegen/backend/batch_graphql
    id: gen_graphql_batch

  - label: Generate All Static Nodes
    type: sub_diagram
    position: {x: 500, y: 400}
    props:
      diagram_path: codegen/backend/batch_static_nodes
    id: gen_static_batch

  - label: Generate Conversions
    type: code_job
    position: {x: 700, y: 300}
    props:
      code_type: file
      source_details: files/codegen/code/backend/generators/conversions.py
    id: gen_conversions

  - label: Write Conversions
    type: db
    position: {x: 900, y: 300}
    props:
      operation: write
      sub_type: file
      source_details: dipeo/diagram_generated/__generated_conversions__.py
    id: write_conversions

connections:
  - source: Load Backend Manifest.out
    target: Batch Process Backend.in
  
  - source: Batch Process Backend.pydantic_tasks
    target: Generate All Pydantic Models.in
  - source: Batch Process Backend.graphql_tasks
    target: Generate All GraphQL Schemas.in
  - source: Batch Process Backend.static_tasks
    target: Generate All Static Nodes.in
  
  # Conversions need all models generated first
  - source: Generate All Pydantic Models.results
    target: Generate Conversions.pydantic_models
  - source: Generate Conversions.out
    target: Write Conversions.in
```

### 6. Benefits of Revised Architecture

1. **DiPeO-Native**: Uses DB nodes for all I/O operations
2. **No Inline Code**: All logic in proper Python files
3. **Pure Functions**: Complete separation of I/O and logic
4. **Testability**: Each generator can be unit tested
5. **Scalability**: Easy to add new generators and templates
6. **Visibility**: Visual diagram shows entire data flow
7. **Debugging**: Can inspect data at each node
8. **Caching**: DB nodes can leverage DiPeO's caching

### 7. Migration Steps

1. **Create Generator Files**:
   ```bash
   # Create pure generator functions
   mkdir -p files/codegen/code/generators
   # Move logic from inline code to Python files
   ```

2. **Update Diagrams to Use DB Nodes**:
   - Replace file I/O code_job nodes with DB nodes
   - Use `code_type: file` for all code execution

3. **Implement Batch Processing**:
   ```python
   # files/codegen/code/batch_processor.py
   def process_batch(inputs):
       """Process multiple nodes in parallel."""
       specs = inputs['specs']
       template = inputs['template']
       
       results = []
       for spec in specs:
           result = generate_code(spec, template)
           results.append({
               'node_type': spec['type'],
               'code': result,
               'path': calculate_output_path(spec)
           })
       
       return {'batch_results': results}
   ```

4. **Add Validation Layer**:
   ```yaml
   # Validation diagram using DB nodes
   - label: Validate Spec
     type: code_job
     props:
       code_type: file
       source_details: files/codegen/code/validators/spec_validator.py
   ```

## Example Usage

```bash
# Generate frontend code for a single node
dipeo run codegen/frontend/generate_frontend_single --light --input-data '{"node_spec_path": "person_job"}'

# Generate backend code for a single node  
dipeo run codegen/backend/generate_backend_single --light --input-data '{"node_spec_path": "person_job"}'

# Generate all frontend code
dipeo run codegen/frontend/generate_frontend_all --light --debug

# Generate all backend code
dipeo run codegen/backend/generate_backend_all --light --debug

# Generate everything (frontend + backend + registry)
dipeo run codegen/master/generate_all --light --debug

# Validate all specifications
dipeo run codegen/master/validate_specs --light
```

### Manifest Examples

#### Frontend Manifest (`frontend.json`)
```json
{
  "nodes": ["person_job", "condition", "api_job", "code_job"],
  "generators": {
    "typescript_model": {
      "template": "frontend/typescript_model.j2",
      "output_pattern": "dipeo/models/src/nodes/{node_name}Node.ts"
    },
    "node_config": {
      "template": "frontend/node_config.j2",
      "output_pattern": "apps/web/src/features/diagram-editor/config/nodes/{node_name}Config.ts"
    },
    "field_config": {
      "template": "frontend/field_config.j2",
      "output_pattern": "apps/web/src/core/config/fields/{node_name}Fields.ts"
    }
  }
}
```

#### Backend Manifest (`backend.json`)
```json
{
  "nodes": ["person_job", "condition", "api_job", "code_job"],
  "generators": {
    "pydantic_model": {
      "template": "backend/pydantic_model.j2",
      "output_pattern": "dipeo/diagram_generated/models/{node_name}_model.py"
    },
    "graphql_schema": {
      "template": "backend/graphql_schema.j2",
      "output_pattern": "apps/server/src/graphql/schemas/{node_name}.graphql"
    },
    "static_node": {
      "template": "backend/static_nodes.j2",
      "output_pattern": "dipeo/core/static/generated/{node_name}_node.py"
    }
  }
}
```

## Key Improvements

1. **DB Nodes for I/O**: All file operations use native DiPeO DB nodes
2. **File-Based Code**: No complex inline code in YAML
3. **Pure Functions**: Complete separation of concerns
4. **Visual Debugging**: Can see data flow in diagram
5. **Native Integration**: Leverages DiPeO's strengths

This approach fully embraces DiPeO's visual programming paradigm while maintaining clean, testable code architecture.