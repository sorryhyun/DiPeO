import glob
import os
import ast
import subprocess
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


def glob_typescript_files(inputs):
    """Get all TypeScript files from source directory."""
    # Get all TypeScript files from source directory
    pattern = os.path.join(inputs.get('source_dir', 'dipeo/models/src'), '**/*.ts')
    files = glob.glob(pattern, recursive=True)
    
    # Filter out test files and type definition files
    files = [f for f in files if not f.endswith('.test.ts') and not f.endswith('.d.ts')]
    
    print(f"Found {len(files)} TypeScript files to process")
    return {'typescript_files': files, 'file_count': len(files)}


def generate_pydantic_models(inputs):
    """Generate Pydantic models from parsed TypeScript data."""
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
    content = template.render(model_data=inputs['model_data'])
    
    # Write output file
    output_path = os.path.join(inputs.get('output_dir', 'dipeo/models'), '__generated_models__.py')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"Generated Pydantic models: {output_path}")
    return {'path': output_path, 'type': 'pydantic_models'}


def generate_conversions(inputs):
    """Generate conversion functions between TypeScript and Python models."""
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
    content = template.render(conversion_data=inputs['conversion_data'])
    
    # Write output file
    output_path = os.path.join(inputs.get('output_dir', 'dipeo/models'), '__generated_conversions__.py')
    
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"Generated conversion functions: {output_path}")
    return {'path': output_path, 'type': 'conversions'}


def generate_zod_schemas(inputs):
    """Generate Zod schemas for TypeScript runtime validation."""
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
    content = template.render(zod_data=inputs['zod_data'])
    
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