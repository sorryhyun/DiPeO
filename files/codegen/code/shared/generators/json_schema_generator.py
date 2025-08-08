"""Generate JSON Schema from TypeScript interfaces using typescript-json-schema."""
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Set
import os


def find_referenced_definitions(schema: Dict[str, Any], all_definitions: Dict[str, Any], visited: Set[str]) -> Set[str]:
    """
    Recursively find all definitions referenced by a schema.
    
    Args:
        schema: The schema to analyze
        all_definitions: All available definitions
        visited: Set of already visited definitions to avoid cycles
        
    Returns:
        Set of all referenced definition names
    """
    references = visited.copy()
    
    def traverse(obj: Any) -> None:
        if isinstance(obj, dict):
            # Check for $ref
            if '$ref' in obj:
                ref = obj['$ref']
                if ref.startswith('#/definitions/'):
                    ref_name = ref.replace('#/definitions/', '')
                    if ref_name not in references and ref_name in all_definitions:
                        references.add(ref_name)
                        # Recursively find references in the referenced definition
                        sub_refs = find_referenced_definitions(
                            all_definitions[ref_name], 
                            all_definitions, 
                            references
                        )
                        references.update(sub_refs)
            
            # Traverse all values in the dict
            for value in obj.values():
                traverse(value)
        elif isinstance(obj, list):
            # Traverse all items in the list
            for item in obj:
                traverse(item)
    
    traverse(schema)
    return references


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate JSON Schema from TypeScript node data interfaces.
    
    Args:
        inputs: Dictionary containing file paths or parsed data
        
    Returns:
        Dictionary containing generated JSON schemas
    """
    base_dir = Path(os.getenv('DIPEO_BASE_DIR', os.getcwd()))
    models_dir = base_dir / 'dipeo' / 'models'
    
    # Create a temporary tsconfig.json that includes all necessary files
    tsconfig = {
        "compilerOptions": {
            "target": "ES2020",
            "module": "commonjs",
            "lib": ["ES2020"],
            "strict": True,
            "esModuleInterop": True,
            "skipLibCheck": True,
            "forceConsistentCasingInFileNames": True,
            "resolveJsonModule": True,
            "moduleResolution": "node",
            "baseUrl": ".",
            "paths": {
                "*": ["*", "node_modules/*"]
            }
        },
        "include": [
            "src/**/*"
        ]
    }
    
    # Write temporary tsconfig
    tsconfig_path = models_dir / 'tsconfig.schema.json'
    with open(tsconfig_path, 'w') as f:
        json.dump(tsconfig, f, indent=2)
    
    # List of interfaces to generate schemas for
    interfaces = [
        ('StartNodeData', 'src/core/nodes/start.data.ts'),
        ('ConditionNodeData', 'src/core/nodes/condition.data.ts'),
        ('PersonJobNodeData', 'src/core/nodes/person-job.data.ts'),
        ('CodeJobNodeData', 'src/core/nodes/code-job.data.ts'),
        ('ApiJobNodeData', 'src/core/nodes/api-job.data.ts'),
        ('EndpointNodeData', 'src/core/nodes/endpoint.data.ts'),
        ('DBNodeData', 'src/core/nodes/db.data.ts'),
        ('UserResponseNodeData', 'src/core/nodes/user-response.data.ts'),
        ('PersonBatchJobNodeData', 'src/core/nodes/person-batch-job.data.ts'),
        ('HookNodeData', 'src/core/nodes/hook.data.ts'),
        ('TemplateJobNodeData', 'src/core/nodes/template-job.data.ts'),
        ('JsonSchemaValidatorNodeData', 'src/core/nodes/json-schema-validator.data.ts'),
        ('TypescriptAstNodeData', 'src/core/nodes/typescript-ast.data.ts'),
        ('SubDiagramNodeData', 'src/core/nodes/sub-diagram.data.ts')
    ]
    
    schemas = {}
    
    try:
        # Generate all schemas in one command for better performance
        print("Generating JSON Schemas for all node data interfaces...")
        
        # Build the command with all interfaces
        interface_names = [name for name, _ in interfaces]
        cmd = [
            'pnpm', 'typescript-json-schema',
            'tsconfig.schema.json',
            '*',  # Generate for all exported types
            '--required',
            '--strictNullChecks',
            '--noExtraProps',
            '--out', 'all-schemas.json'
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        print(f"Working directory: {models_dir}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(models_dir),
            timeout=60
        )
        
        if result.returncode != 0:
            print(f"Error generating schemas:")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            print(f"Return code: {result.returncode}")
            # Try individual generation as fallback
            for interface_name, file_path in interfaces:
                print(f"Trying individual generation for {interface_name}")
                cmd = [
                    'pnpm', 'typescript-json-schema',
                    'tsconfig.schema.json',
                    interface_name,
                    '--required',
                    '--strictNullChecks',
                    '--noExtraProps'
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=str(models_dir),
                    timeout=30
                )
                
                if result.returncode == 0:
                    try:
                        schema = json.loads(result.stdout)
                        key = interface_name.replace('NodeData', '').lower()
                        
                        # Ensure all referenced definitions are included
                        if 'definitions' in schema and interface_name in schema['definitions']:
                            # Find all referenced definitions
                            referenced_defs = find_referenced_definitions(
                                schema['definitions'][interface_name],
                                schema.get('definitions', {}),
                                {interface_name}
                            )
                            
                            # Filter definitions to only include referenced ones
                            filtered_definitions = {}
                            for ref_name in referenced_defs:
                                if ref_name in schema['definitions']:
                                    filtered_definitions[ref_name] = schema['definitions'][ref_name]
                            
                            schema['definitions'] = filtered_definitions
                        
                        schemas[key] = schema
                        print(f"✓ Generated schema for {interface_name}")
                    except json.JSONDecodeError:
                        print(f"✗ Failed to parse schema for {interface_name}")
                else:
                    print(f"✗ Failed to generate schema for {interface_name}: {result.stderr}")
        else:
            # Parse the combined output
            all_schemas_path = models_dir / 'all-schemas.json'
            if all_schemas_path.exists():
                with open(all_schemas_path, 'r') as f:
                    all_schemas = json.load(f)
                
                # Extract individual schemas
                definitions = all_schemas.get('definitions', {})
                for interface_name, _ in interfaces:
                    if interface_name in definitions:
                        key = interface_name.replace('NodeData', '').lower()
                        
                        # Find all referenced definitions
                        referenced_defs = find_referenced_definitions(
                            definitions[interface_name], 
                            definitions,
                            {interface_name}
                        )
                        
                        # Include all referenced definitions
                        schema_definitions = {}
                        for ref_name in referenced_defs:
                            if ref_name in definitions:
                                schema_definitions[ref_name] = definitions[ref_name]
                        
                        schemas[key] = {
                            "$schema": "http://json-schema.org/draft-07/schema#",
                            "$ref": f"#/definitions/{interface_name}",
                            "definitions": schema_definitions
                        }
                        print(f"✓ Extracted schema for {interface_name}")
                
                # Clean up combined file
                os.unlink(all_schemas_path)
    
    finally:
        # Clean up temporary tsconfig
        if tsconfig_path.exists():
            os.unlink(tsconfig_path)
    
    # Save individual schema files
    output_dir = base_dir / 'dipeo' / 'diagram_generated_staged' / 'schemas' / 'nodes'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    saved_count = 0
    for key, schema in schemas.items():
        schema_file = output_dir / f"{key}.schema.json"
        with open(schema_file, 'w') as f:
            json.dump(schema, f, indent=2)
        print(f"Saved {key} schema to {schema_file}")
        saved_count += 1
    
    print(f"\n✓ Generated and saved {saved_count} JSON schemas")
    
    return {
        'schemas': schemas,
        'schema_count': len(schemas),
        'output_dir': str(output_dir)
    }