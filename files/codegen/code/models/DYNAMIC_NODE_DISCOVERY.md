# Dynamic Node Discovery Approaches

## Approach 1: Using Code Job Nodes

In your diagram, add a code_job node before the existing nodes:

```yaml
nodes:
  - id: discover_files
    type: code_job
    position: {x: 100, y: 100}
    data:
      name: "Discover Node Files"
      code: |
        import os
        from pathlib import Path
        
        base_dir = Path(os.getenv('DIPEO_BASE_DIR', os.getcwd()))
        
        # Discover data files
        cache_dir = base_dir / '.temp'
        node_data_files = []
        if cache_dir.exists():
            node_data_files = sorted([f.name for f in cache_dir.glob('*_data_ast.json')])
        
        # Discover spec files
        temp_dir = base_dir / 'temp'
        spec_files = []
        if temp_dir.exists():
            spec_files = sorted([f.name for f in temp_dir.glob('*.spec.ts.json')])
        
        return {
            'node_data_files': node_data_files,
            'spec_files': spec_files
        }
  
  - id: combine_node_data
    type: code_job
    position: {x: 300, y: 100}
    data:
      name: "Combine Node Data"
      module_path: "/files/codegen/code/models/generate_graphql_schema/graphql_schema_generator.py"
      function_name: "combine_node_data_ast"

connections:
  - source: discover_files
    target: combine_node_data
    source_output: node_data_files
    target_input: node_data_files
```

## Approach 2: Using DB Node with Glob Pattern (RECOMMENDED)

Use DB node to read multiple files with glob patterns:

```yaml
nodes:
  - id: read_node_data_files
    type: db
    position: {x: 100, y: 200}
    data:
      name: "Read Node Data Files"
      operation: read
      source_type: file
      serialize_json: true
      glob: true  # Enable glob pattern expansion
      source_details:
        - ".temp/*_data_ast.json"  # Matches all node data files
  
  - id: read_spec_files
    type: db
    position: {x: 100, y: 300}
    data:
      name: "Read Spec Files"
      operation: read
      source_type: file
      serialize_json: true
      glob: true  # Enable glob pattern expansion
      source_details:
        - "temp/*.spec.ts.json"  # Matches all spec files
```

**Note**: The `glob: true` flag must be set to enable pattern expansion. Without it, patterns are treated as literal filenames.

## Approach 3: Hybrid - Use Discovery Function in Diagram

```yaml
nodes:
  - id: discover_and_process
    type: code_job
    position: {x: 100, y: 400}
    data:
      name: "Discover and Process"
      module_path: "/files/codegen/code/models/discover_node_files.py"
      function_name: "discover_all_node_files"
  
  - id: process_graphql
    type: code_job
    position: {x: 300, y: 400}
    data:
      name: "Process GraphQL"
      module_path: "/files/codegen/code/models/generate_graphql_schema/graphql_schema_generator.py"
      function_name: "combine_node_data_ast"

connections:
  - source: discover_and_process
    target: process_graphql
    source_output: node_data_files
    target_input: node_data_files
```

## Benefits

1. **No Manual Updates**: New node types are automatically discovered
2. **Cleaner Code**: No hardcoded lists to maintain
3. **Flexible**: Can filter or process specific patterns
4. **Diagram-Driven**: Logic is visible in the diagram

## Migration Steps

1. Update your existing diagrams to use one of the approaches above
2. The modified functions will accept discovered files as input
3. If no files are provided, they fall back to dynamic discovery
4. Gradually phase out hardcoded lists

## Example for Complete GraphQL Generation

```yaml
name: "GraphQL Schema Generation with Dynamic Discovery"
nodes:
  # Step 1: Discover all node files
  - id: discover_files
    type: code_job
    data:
      module_path: "/files/codegen/code/models/discover_node_files.py"
      function_name: "discover_all_node_files"
  
  # Step 2: Combine node data AST
  - id: combine_node_data
    type: code_job
    data:
      module_path: "/files/codegen/code/models/generate_graphql_schema/graphql_schema_generator.py"
      function_name: "combine_node_data_ast"
  
  # Step 3: Extract GraphQL types
  - id: extract_types
    type: code_job
    data:
      module_path: "/files/codegen/code/models/generate_graphql_schema/graphql_schema_generator.py"
      function_name: "extract_graphql_types"
  
  # ... rest of the diagram

connections:
  - source: discover_files
    target: combine_node_data
    source_output: node_data_files
    target_input: node_data_files
  
  - source: combine_node_data
    target: extract_types
    target_input: node_data_ast
```