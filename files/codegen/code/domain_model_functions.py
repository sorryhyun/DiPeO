import glob
import os
import ast
import json
import subprocess
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any, List


def glob_typescript_files(inputs):
    """Get all TypeScript files from source directory."""
    # Get all TypeScript files from source directory
    source_dir = inputs.get('source_dir', 'dipeo/models/src')
    # Make it absolute if it's relative
    if not os.path.isabs(source_dir):
        source_dir = os.path.join(os.environ.get('DIPEO_BASE_DIR', '/home/soryhyun/DiPeO'), source_dir)
    
    pattern = os.path.join(source_dir, '**/*.ts')
    files = glob.glob(pattern, recursive=True)
    
    # Filter out test files and type definition files
    files = [f for f in files if not f.endswith('.test.ts') and not f.endswith('.d.ts')]
    
    print(f"Found {len(files)} TypeScript files to process")
    result = {'typescript_files': files, 'file_count': len(files)}
    # DiPeO expects a 'default' key for passing data between nodes
    result['default'] = result.copy()
    return result


def generate_pydantic_models(inputs):
    """Generate Pydantic models from parsed TypeScript data."""
    # Read model_data from saved file
    temp_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
    temp_base = os.path.join(temp_dir, '.temp', 'codegen')
    model_data_file = os.path.join(temp_base, 'model_data.json')
    
    print(f"[generate_pydantic_models] Loading model data from: {model_data_file}")
    
    if not os.path.exists(model_data_file):
        print(f"[generate_pydantic_models] ERROR: Model data file not found: {model_data_file}")
        return {'error': 'Model data file not found'}
    
    # Load the model data
    with open(model_data_file, 'r') as f:
        model_data = json.load(f)
    
    print(f"[generate_pydantic_models] Loaded model data with {len(model_data.get('models', []))} models")
    
    if not model_data or not model_data.get('models'):
        print("[generate_pydantic_models] No models to generate")
        return {'error': 'No models found in model data'}
    
    # Use Jinja2 with custom filters
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    import re
    
    # Define custom filters
    def snake_case(name):
        """Convert camelCase to snake_case."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def is_enum(type_name):
        """Check if a type is an enum."""
        enums = {enum['name'] for enum in model_data.get('enums', [])}
        return type_name in enums
    
    def ends_with(text, suffix):
        """Check if text ends with suffix."""
        return text.endswith(suffix)
    
    def to_node_type(name):
        """Convert NodeData name to node type."""
        if name.endswith('NodeData'):
            return snake_case(name[:-8])  # Remove 'NodeData' suffix
        return snake_case(name)
    
    # Setup Jinja2 environment
    template_dir = Path(temp_dir) / 'files' / 'codegen' / 'templates' / 'codegen'
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape()
    )
    
    # Register filters
    env.filters['snakeCase'] = snake_case
    env.filters['isEnum'] = is_enum
    env.filters['endsWith'] = ends_with
    env.filters['toNodeType'] = to_node_type
    
    # Load template directly (it's already in Jinja2 format)
    template = env.get_template('pydantic_models.j2')
    
    # Render template
    try:
        content = template.render(model_data=model_data)
    except Exception as e:
        print(f"[generate_pydantic_models] Template rendering error: {e}")
        return {'error': f'Template rendering error: {str(e)}'}
    
    # Write output file
    output_dir = Path(temp_dir) / 'dipeo' / 'models'
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / '__generated_models__.py'
    
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"[generate_pydantic_models] Generated Pydantic models: {output_path}")
    
    # Save result info to file for combine_results
    result_file = os.path.join(temp_base, 'pydantic_result.json')
    with open(result_file, 'w') as f:
        json.dump({'path': str(output_path), 'type': 'pydantic_models'}, f)
    
    return {'path': str(output_path), 'type': 'pydantic_models', 'success': True}


def generate_conversions(inputs):
    """Generate conversion functions between TypeScript and Python models."""
    # Read conversion_data from saved file
    temp_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
    temp_base = os.path.join(temp_dir, '.temp', 'codegen')
    conversion_data_file = os.path.join(temp_base, 'conversion_data.json')
    
    print(f"[generate_conversions] Loading conversion data from: {conversion_data_file}")
    
    if not os.path.exists(conversion_data_file):
        print(f"[generate_conversions] ERROR: Conversion data file not found: {conversion_data_file}")
        return {'error': 'Conversion data file not found'}
    
    # Load the conversion data
    with open(conversion_data_file, 'r') as f:
        conversion_data = json.load(f)
    
    print(f"[generate_conversions] Loaded conversion data")
    
    # Use Jinja2 with custom filters
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    import re
    
    # Define custom filters
    def snake_case(name):
        """Convert camelCase to snake_case."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def is_enum(type_name):
        """Check if a type is an enum."""
        enums = {enum['name'] for enum in conversion_data.get('enums', [])}
        return type_name in enums
    
    def ends_with(text, suffix):
        """Check if text ends with suffix."""
        return text.endswith(suffix)
    
    def to_node_type(name):
        """Convert NodeData name to node type."""
        if name.endswith('NodeData'):
            return snake_case(name[:-8])  # Remove 'NodeData' suffix
        return snake_case(name)
    
    # Setup Jinja2 environment
    template_dir = Path(temp_dir) / 'files' / 'codegen' / 'templates' / 'codegen'
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape()
    )
    
    # Register filters
    env.filters['snakeCase'] = snake_case
    env.filters['isEnum'] = is_enum
    env.filters['endsWith'] = ends_with
    env.filters['toNodeType'] = to_node_type
    
    # Load template directly (it's already in Jinja2 format)
    template = env.get_template('conversions.j2')
    
    # Render template
    try:
        content = template.render(conversion_data=conversion_data)
    except Exception as e:
        print(f"[generate_conversions] Template rendering error: {e}")
        return {'error': f'Template rendering error: {str(e)}'}
    
    # Write output file
    output_dir = Path(temp_dir) / 'dipeo' / 'models'
    output_path = output_dir / '__generated_conversions__.py'
    
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"[generate_conversions] Generated conversion functions: {output_path}")
    
    # Save result info to file for combine_results
    result_file = os.path.join(temp_base, 'conversion_result.json')
    with open(result_file, 'w') as f:
        json.dump({'path': str(output_path), 'type': 'conversions'}, f)
    
    return {'path': str(output_path), 'type': 'conversions', 'success': True}


def generate_zod_schemas(inputs):
    """Generate Zod schemas for TypeScript runtime validation."""
    # Read zod_data from saved file
    temp_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
    temp_base = os.path.join(temp_dir, '.temp', 'codegen')
    zod_data_file = os.path.join(temp_base, 'zod_data.json')
    
    print(f"[generate_zod_schemas] Loading zod data from: {zod_data_file}")
    
    if not os.path.exists(zod_data_file):
        print(f"[generate_zod_schemas] ERROR: Zod data file not found: {zod_data_file}")
        return {'error': 'Zod data file not found'}
    
    # Load the zod data
    with open(zod_data_file, 'r') as f:
        zod_data = json.load(f)
    
    print(f"[generate_zod_schemas] Loaded zod data")
    
    # Use Jinja2 with custom filters
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    import re
    
    # Define custom filters
    def snake_case(name):
        """Convert camelCase to snake_case."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\\1_\\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\\1_\\2', s1).lower()
    
    def is_enum(type_name):
        """Check if a type is an enum."""
        enums = {enum['name'] for enum in zod_data.get('enums', [])}
        return type_name in enums
    
    def ends_with(text, suffix):
        """Check if text ends with suffix."""
        return text.endswith(suffix)
    
    def to_node_type(name):
        """Convert NodeData name to node type."""
        if name.endswith('NodeData'):
            return snake_case(name[:-8])  # Remove 'NodeData' suffix
        return snake_case(name)
    
    # Setup Jinja2 environment
    template_dir = Path(temp_dir) / 'files' / 'codegen' / 'templates' / 'codegen'
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape()
    )
    
    def to_zod_schema(definition):
        """Convert type definition to Zod schema."""
        # Simple implementation - can be enhanced
        if definition in ['string', 'number', 'boolean']:
            return f'z.{definition}()'
        return f'z.any()  // TODO: implement {definition}'
    
    def to_zod_type(field):
        """Convert field to Zod type."""
        type_name = field.get('type', 'any')
        required = field.get('required', True)
        
        # Map basic types
        type_map = {
            'str': 'z.string()',
            'string': 'z.string()',
            'float': 'z.number()',
            'int': 'z.number().int()',
            'bool': 'z.boolean()',
            'boolean': 'z.boolean()',
            'Any': 'z.any()',
            'None': 'z.null()',
        }
        
        # Check if it's a basic type
        if type_name in type_map:
            zod_type = type_map[type_name]
        elif type_name.startswith('List['):
            inner_type = type_name[5:-1]  # Extract inner type
            zod_type = f'z.array({to_zod_type({"type": inner_type})})'
        elif type_name.startswith('Optional['):
            inner_type = type_name[9:-1]  # Extract inner type
            return f'{to_zod_type({"type": inner_type})}.optional()'
        elif is_enum(type_name):
            zod_type = f'{type_name}Schema'
        else:
            # Assume it's a model schema
            zod_type = f'{type_name}Schema'
        
        if not required and not type_name.startswith('Optional['):
            zod_type += '.optional()'
        
        return zod_type
    
    # Register filters
    env.filters['snakeCase'] = snake_case
    env.filters['isEnum'] = is_enum
    env.filters['endsWith'] = ends_with
    env.filters['toNodeType'] = to_node_type
    env.filters['toZodSchema'] = to_zod_schema
    env.filters['toZodType'] = to_zod_type
    
    # Load template directly (it's already in Jinja2 format)
    template = env.get_template('zod_schemas.j2')
    
    # Render template
    try:
        content = template.render(zod_data=zod_data)
    except Exception as e:
        print(f"[generate_zod_schemas] Template rendering error: {e}")
        return {'error': f'Template rendering error: {str(e)}'}
    
    # Write output file
    output_dir = Path(temp_dir) / 'dipeo' / 'models' / 'src' / 'generated'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'zod_schemas.ts'
    
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"[generate_zod_schemas] Generated Zod schemas: {output_path}")
    
    # Save result info to file for combine_results
    result_file = os.path.join(temp_base, 'zod_result.json')
    with open(result_file, 'w') as f:
        json.dump({'path': str(output_path), 'type': 'zod_schemas'}, f)
    
    return {'path': str(output_path), 'type': 'zod_schemas', 'success': True}


def verify_generated_code(inputs):
    """Verify syntax and run basic checks on generated code."""
    temp_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
    temp_base = os.path.join(temp_dir, '.temp', 'codegen')
    
    results = {"errors": [], "warnings": []}
    
    # Load combined results
    combined_file = os.path.join(temp_base, 'combined_results.json')
    if not os.path.exists(combined_file):
        print(f"[verify_generated_code] ERROR: Combined results file not found: {combined_file}")
        return {'error': 'Combined results file not found'}
    
    with open(combined_file, 'r') as f:
        combined_results = json.load(f)
    
    # Check Python syntax
    for file_info in combined_results.get('generated_files', []):
        if isinstance(file_info, dict) and 'path' in file_info:
            file_path = file_info['path']
            if file_path.endswith('.py') and os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        ast.parse(f.read())
                    print(f"✓ Valid Python syntax: {file_path}")
                except SyntaxError as e:
                    results['errors'].append(f"Syntax error in {file_path}: {e}")
                except Exception as e:
                    results['warnings'].append(f"Could not parse {file_path}: {e}")
    
    # Run mypy type checking if available (optional)
    output_dir = os.path.join(temp_dir, 'dipeo', 'models')
    if os.path.exists(output_dir):
        try:
            result = subprocess.run(
                ['mypy', '--ignore-missing-imports', output_dir], 
                capture_output=True, 
                text=True
            )
            if result.returncode != 0:
                results['warnings'].append(f"MyPy warnings:\n{result.stdout}")
        except FileNotFoundError:
            results['warnings'].append("MyPy not installed, skipping type checks")
    
    # Save verification results
    verification_file = os.path.join(temp_base, 'verification_results.json')
    with open(verification_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results


def read_typescript_files(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Read content of TypeScript files and combine them for parsing."""
    print(f"read_typescript_files received inputs: {list(inputs.keys())}")
    
    # DiPeO may pass data under different keys
    files = []
    if 'file_list' in inputs and isinstance(inputs['file_list'], dict):
        # From labeled connection
        files = inputs['file_list'].get('typescript_files', [])
    elif 'typescript_files' in inputs:
        files = inputs['typescript_files']
    elif 'default' in inputs:
        files = inputs['default'].get('typescript_files', [])
    
    print(f"Processing {len(files)} TypeScript files")
    file_contents = []
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                file_contents.append({
                    'path': file_path,
                    'content': content,
                    'filename': os.path.basename(file_path)
                })
                print(f"Read {file_path}: {len(content)} characters")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
    
    # Combine all content for parsing
    combined_source = '\n\n// --- File Separator ---\n\n'.join(
        [f"// File: {fc['filename']}\n{fc['content']}" for fc in file_contents]
    )
    
    result = {
        'source': combined_source,
        'files': file_contents,
        'file_count': len(file_contents)
    }
    
    print(f"Returning combined source of length: {len(combined_source)}")
    print(f"Result keys: {list(result.keys())}")
    
    # For DiPeO handle-based data passing, return with both direct keys and default
    result['default'] = result.copy()
    
    return result


def extract_source(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Extract source code from inputs for TypeScript AST parser."""
    # Debug: print the structure of inputs
    print(f"extract_source received inputs structure: {list(inputs.keys())}")
    
    # DiPeO passes the entire output from previous node
    # When content_type is 'object', the data is directly in inputs
    source = inputs.get('source', '')
    files = inputs.get('files', [])
    file_count = inputs.get('file_count', 0)
    
    if not source and 'value' in inputs and isinstance(inputs['value'], dict):
        # Sometimes DiPeO wraps the output in a 'value' key
        source = inputs['value'].get('source', '')
        files = inputs['value'].get('files', files)
        file_count = inputs['value'].get('file_count', file_count)
    
    print(f"Extracted source code, length: {len(source)}")
    print(f"File count: {file_count}")
    
    # The TypeScript AST parser expects just 'source' as input
    # Return only what the parser needs
    return {'source': source}


def combine_generation_results(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Combine all generation results into a single structure."""
    temp_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
    temp_base = os.path.join(temp_dir, '.temp', 'codegen')
    
    print(f"[combine_generation_results] Reading results from: {temp_base}")
    
    results = {
        'generated_files': [],
        'file_count': 0
    }
    
    # Read file info
    file_info_file = os.path.join(temp_base, 'file_info.json')
    if os.path.exists(file_info_file):
        with open(file_info_file, 'r') as f:
            file_info = json.load(f)
            results['file_count'] = file_info.get('file_count', 0)
    
    # Read results from each generator
    result_files = {
        'pydantic_result.json': 'pydantic',
        'conversion_result.json': 'conversion',
        'zod_result.json': 'zod',
        'schema_result.json': 'schema'
    }
    
    for filename, result_type in result_files.items():
        result_file = os.path.join(temp_base, filename)
        if os.path.exists(result_file):
            with open(result_file, 'r') as f:
                result_data = json.load(f)
                
                if result_type == 'schema':
                    # Schema generator returns multiple files
                    results['generated_files'].extend(result_data.get('generated_files', []))
                else:
                    # Other generators return single file info
                    results['generated_files'].append(result_data)
            print(f"[combine_generation_results] Loaded {result_type} results")
        else:
            print(f"[combine_generation_results] Warning: {filename} not found")
    
    print(f"[combine_generation_results] Combined {len(results['generated_files'])} generated files")
    
    # Save combined results to file
    combined_file = os.path.join(temp_base, 'combined_results.json')
    with open(combined_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results


def generate_graphql_schema(inputs):
    """Generate GraphQL schema from Python models."""
    # Read model data from saved file
    temp_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
    temp_base = os.path.join(temp_dir, '.temp', 'codegen')
    model_data_file = os.path.join(temp_base, 'model_data.json')
    
    print(f"[generate_graphql_schema] Loading model data from: {model_data_file}")
    
    if not os.path.exists(model_data_file):
        print(f"[generate_graphql_schema] ERROR: Model data file not found: {model_data_file}")
        return {'error': 'Model data file not found'}
    
    # Load the model data
    with open(model_data_file, 'r') as f:
        model_data = json.load(f)
    
    # Prepare GraphQL data structure
    graphql_data = {
        'enums': [],
        'models': [],
        'unions': {}
    }
    
    # Type mapping from Python to GraphQL
    type_map = {
        'str': 'String',
        'string': 'String',
        'float': 'Float',
        'int': 'Int',
        'bool': 'Boolean',
        'boolean': 'Boolean',
        'Any': 'JSON',
        'None': 'JSON',
        'datetime': 'DateTime',
        'Dict[str, Any]': 'JSON',
    }
    
    def python_to_graphql_type(python_type):
        """Convert Python type to GraphQL type."""
        # Handle Optional types
        if python_type.startswith('Optional['):
            inner_type = python_type[9:-1]
            return python_to_graphql_type(inner_type)
        
        # Handle List types
        if python_type.startswith('List['):
            inner_type = python_type[5:-1]
            return f'[{python_to_graphql_type(inner_type)}]'
        
        # Check if it's an enum
        enum_names = {enum['name'] for enum in model_data.get('models', []) if enum.get('type') == 'enum'}
        if python_type in enum_names:
            return python_type
        
        # Basic type mapping
        return type_map.get(python_type, python_type)
    
    # Process enums
    for model in model_data.get('models', []):
        if model.get('type') == 'enum':
            graphql_data['enums'].append({
                'name': model['name'],
                'values': [v[0] for v in model.get('enum_values', [])]
            })
    
    # Process models
    for model in model_data.get('models', []):
        if model.get('type') == 'class':
            fields = []
            for field_name, field_info in model.get('fields', {}).items():
                fields.append({
                    'name': field_name,
                    'graphql_type': python_to_graphql_type(field_info['type']),
                    'required': field_info.get('required', True),
                    'description': field_info.get('description', '')
                })
            
            graphql_data['models'].append({
                'name': model['name'],
                'fields': fields
            })
    
    # Setup Jinja2 environment
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    template_dir = Path(temp_dir) / 'files' / 'codegen' / 'templates' / 'codegen'
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape()
    )
    
    # Load and render template
    template = env.get_template('graphql_from_python.j2')
    content = template.render(graphql_data=graphql_data)
    
    # Write output file
    output_dir = Path(temp_dir) / 'apps' / 'server' / 'src' / 'dipeo_server' / 'api' / 'graphql' / 'schema'
    output_dir.mkdir(exist_ok=True, parents=True)
    output_path = output_dir / 'generated_models.graphql'
    
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"[generate_graphql_schema] Generated GraphQL schema: {output_path}")
    
    # Save result info to file for combine_results
    result_file = os.path.join(temp_base, 'graphql_result.json')
    with open(result_file, 'w') as f:
        json.dump({'path': str(output_path), 'type': 'graphql_schema'}, f)
    
    return {'path': str(output_path), 'type': 'graphql_schema', 'success': True}
