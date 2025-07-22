import glob
import os
import ast
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
    # Get model_data from inputs (may be under 'default' key)
    model_data = inputs.get('model_data')
    if not model_data and 'default' in inputs:
        model_data = inputs['default'].get('model_data')
    
    if not model_data:
        print("ERROR: No model_data found in inputs")
        print(f"Available keys: {list(inputs.keys())}")
        return {'error': 'No model_data provided'}
    
    # Setup Jinja2 environment
    template_dir = Path('files/codegen/templates/codegen')
    env = Environment(loader=FileSystemLoader(template_dir))
    
    # Add custom filters
    def snake_case(name):
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def starts_with(text, prefix):
        return text.startswith(prefix)
    
    def ends_with(text, suffix):
        return text.endswith(suffix)
    
    def to_node_type(class_name):
        if class_name.endswith('Node'):
            node_type = class_name[:-4]
            return snake_case(node_type)
        return snake_case(class_name)
    
    env.filters['snakeCase'] = snake_case
    env.filters['startsWith'] = starts_with
    env.filters['endsWith'] = ends_with
    env.filters['toNodeType'] = to_node_type
    env.globals['eq'] = lambda x, y: x == y
    env.globals['or'] = lambda *args: any(args)
    
    # Load template and render
    template = env.get_template('pydantic_models.j2')
    content = template.render(model_data=model_data)
    
    # Write output file
    output_path = os.path.join(inputs.get('output_dir', 'dipeo/models'), '__generated_models__.py')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"Generated Pydantic models: {output_path}")
    return {'path': output_path, 'type': 'pydantic_models'}


def generate_conversions(inputs):
    """Generate conversion functions between TypeScript and Python models."""
    # Get conversion_data from inputs (may be under 'default' key)
    conversion_data = inputs.get('conversion_data')
    if not conversion_data and 'default' in inputs:
        conversion_data = inputs['default'].get('conversion_data')
    
    if not conversion_data:
        print("ERROR: No conversion_data found in inputs")
        return {'error': 'No conversion_data provided'}
    
    # Setup Jinja2 environment
    template_dir = Path('files/codegen/templates/codegen')
    env = Environment(loader=FileSystemLoader(template_dir))
    
    # Add custom filters
    def snake_case(name):
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def is_enum(type_name):
        # Check if type is an enum (simplified check)
        return type_name in ['NodeType', 'ExecutionStatus', 'DiagramFormat']
    
    def to_node_type(class_name):
        if class_name.endswith('Node'):
            node_type = class_name[:-4]
            return snake_case(node_type)
        return snake_case(class_name)
    
    env.filters['snakeCase'] = snake_case
    env.filters['isEnum'] = is_enum
    env.filters['toNodeType'] = to_node_type
    env.filters['endsWith'] = lambda text, suffix: text.endswith(suffix)
    
    # Load template and render
    template = env.get_template('conversions.j2')
    content = template.render(conversion_data=conversion_data)
    
    # Write output file
    output_path = os.path.join(inputs.get('output_dir', 'dipeo/models'), '__generated_conversions__.py')
    
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"Generated conversion functions: {output_path}")
    return {'path': output_path, 'type': 'conversions'}


def generate_zod_schemas(inputs):
    """Generate Zod schemas for TypeScript runtime validation."""
    # Get zod_data from inputs (may be under 'default' key)
    zod_data = inputs.get('zod_data')
    if not zod_data and 'default' in inputs:
        zod_data = inputs['default'].get('zod_data')
    
    if not zod_data:
        print("ERROR: No zod_data found in inputs")
        return {'error': 'No zod_data provided'}
    
    # Setup Jinja2 environment
    template_dir = Path('files/codegen/templates/codegen')
    env = Environment(loader=FileSystemLoader(template_dir))
    
    # Add custom filters
    def to_zod_type(python_type, required=True):
        type_map = {
            'str': 'z.string()',
            'int': 'z.number().int()',
            'float': 'z.number()',
            'bool': 'z.boolean()',
            'Any': 'z.any()',
            'datetime': 'z.string().datetime()',
            'Dict[str, Any]': 'z.record(z.any())',
        }
        
        zod_type = type_map.get(python_type, f'z.unknown() /* {python_type} */')
        
        if not required:
            zod_type = f'{zod_type}.optional()'
        
        return zod_type
    
    def to_zod_schema(definition):
        # Convert type definition to Zod schema
        return 'z.unknown() /* TODO: implement */'
    
    env.filters['toZodType'] = to_zod_type
    env.filters['toZodSchema'] = to_zod_schema
    env.filters['endsWith'] = lambda text, suffix: text.endswith(suffix)
    env.globals['eq'] = lambda x, y: x == y
    
    # Load template and render
    template = env.get_template('zod_schemas.j2')
    content = template.render(zod_data=zod_data)
    
    # Write output file
    output_dir = os.path.join(inputs.get('source_dir', 'dipeo/models/src'), 'generated')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'zod_schemas.ts')
    
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"Generated Zod schemas: {output_path}")
    return {'path': output_path, 'type': 'zod_schemas'}


def verify_generated_code(inputs):
    """Verify syntax and run basic checks on generated code."""
    results = {"errors": [], "warnings": []}
    
    # Check Python syntax
    for file_info in inputs.get('generated_files', []):
        if file_info['path'].endswith('.py'):
            try:
                with open(file_info['path'], 'r') as f:
                    ast.parse(f.read())
                print(f"✓ Valid Python syntax: {file_info['path']}")
            except SyntaxError as e:
                results['errors'].append(f"Syntax error in {file_info['path']}: {e}")
    
    # Run mypy type checking if available
    try:
        result = subprocess.run(
            ['mypy', '--ignore-missing-imports', inputs['output_dir']], 
            capture_output=True, 
            text=True
        )
        if result.returncode != 0:
            results['warnings'].append(f"MyPy warnings:\n{result.stdout}")
    except FileNotFoundError:
        results['warnings'].append("MyPy not installed, skipping type checks")
    
    return results


def read_typescript_files(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Read content of TypeScript files and combine them for parsing."""
    print(f"read_typescript_files received inputs: {list(inputs.keys())}")
    
    # DiPeO may pass data under 'default' key
    files = inputs.get('typescript_files', [])
    if not files and 'default' in inputs:
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
    results = {
        'generated_files': [],
        'file_count': inputs.get('file_info', {}).get('file_count', 0)
    }
    
    # Add results from each generator
    if 'pydantic_result' in inputs and inputs['pydantic_result']:
        results['generated_files'].append(inputs['pydantic_result'])
    
    if 'conversion_result' in inputs and inputs['conversion_result']:
        results['generated_files'].append(inputs['conversion_result'])
    
    if 'zod_result' in inputs and inputs['zod_result']:
        results['generated_files'].append(inputs['zod_result'])
    
    if 'schema_result' in inputs and inputs['schema_result']:
        # Schema generator returns multiple files
        results['generated_files'].extend(inputs['schema_result'].get('generated_files', []))
    
    print(f"Combined {len(results['generated_files'])} generated files")
    return results