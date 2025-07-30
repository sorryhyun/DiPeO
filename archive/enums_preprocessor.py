"""
Enums preprocessor - Uses services for heavy lifting.
This runs OUTSIDE of diagram execution to prepare data.
"""

from typing import Dict, Any, List, Tuple
from pathlib import Path
import json

# Import our new services
from files.codegen.code.services import (
    CoreTypeAlgebra, 
    ASTService,
    TemplateService,
    MacroDefinition
)


class EnumsPreprocessor:
    """Preprocessor that uses services to prepare enum generation data."""
    
    def __init__(self):
        self.type_algebra = CoreTypeAlgebra()
        self.ast_service = ASTService()
        self.template_service = TemplateService()
        self._register_enum_filters()
    
    def _register_enum_filters(self):
        """Register enum-specific template filters."""
        # Add custom filter for enum value formatting
        def format_enum_value(name: str, style: str = 'upper') -> str:
            if style == 'upper':
                return name.upper()
            elif style == 'lower':  
                return name.lower()
            elif style == 'pascal':
                return ''.join(word.capitalize() for word in name.split('_'))
            return name
        
        # Get a renderer with the custom filter
        self.enum_renderer = self.template_service.get_renderer(
            '',  # No specific template path
            extra_filters={'format_enum_value': format_enum_value}
        )
    
    def extract_enums_from_ast(self, file_path: str) -> Tuple[List[dict], dict]:
        """
        Extract enum definitions from TypeScript file using AST service.
        Returns (enums_data, metadata).
        """
        # Use AST service to get processed AST
        ast_data = self.ast_service.get_processed_ast(
            file_path,
            processors=['extract_exports', 'extract_types']
        )
        
        enums = []
        metadata = {
            'source_file': file_path,
            'extraction_time': ast_data.processing_time,
            'total_enums': 0
        }
        
        # Extract enum definitions
        for export in ast_data.exports:
            if export.get('type') == 'enum':
                enum_data = {
                    'name': export.get('name', ''),
                    'values': [],
                    'description': export.get('description', ''),
                    'metadata': {}
                }
                
                # Process enum members
                for member in export.get('members', []):
                    value = {
                        'name': member.get('name', ''),
                        'value': member.get('value'),
                        'description': member.get('description', '')
                    }
                    
                    # Type check the value if needed
                    if value['value'] and isinstance(value['value'], str):
                        try:
                            # Parse type expression
                            expr = self.type_algebra.parse(value['value'])
                            value['metadata'] = {
                                'type_kind': expr.kind.name,
                                'is_literal': expr.kind.name == 'LITERAL'
                            }
                        except:
                            pass
                    
                    enum_data['values'].append(value)
                
                enums.append(enum_data)
        
        metadata['total_enums'] = len(enums)
        return enums, metadata
    
    def prepare_template_data(self, enums: List[dict]) -> dict:
        """
        Prepare data for template rendering with additional computed fields.
        """
        # Enhance enum data with computed fields
        for enum in enums:
            enum['snake_case_name'] = self._to_snake_case(enum['name'])
            enum['has_descriptions'] = any(v.get('description') for v in enum['values'])
            enum['is_string_enum'] = all(
                isinstance(v.get('value'), str) for v in enum['values']
            )
        
        return {
            'enums': enums,
            'has_enums': len(enums) > 0,
            'enum_count': len(enums),
            'imports': self._calculate_imports(enums)
        }
    
    def render_preview(self, template_content: str, enums_data: List[dict]) -> str:
        """
        Render a preview using the template service with all filters.
        This is for testing/preview only - diagrams will use their own rendering.
        """
        data = self.prepare_template_data(enums_data)
        return self.enum_renderer.render_string(template_content, **data)
    
    def create_generation_package(self, 
                                 typescript_files: List[str],
                                 template_path: str) -> dict:
        """
        Create a complete data package for enum generation.
        This package can be serialized and passed to diagram nodes.
        """
        all_enums = []
        all_metadata = []
        
        # Process all TypeScript files
        for ts_file in typescript_files:
            enums, metadata = self.extract_enums_from_ast(ts_file)
            all_enums.extend(enums)
            all_metadata.append(metadata)
        
        # Read template
        template_content = Path(template_path).read_text()
        
        # Prepare final package
        package = {
            'template_content': template_content,
            'enums_data': all_enums,
            'metadata': {
                'source_files': typescript_files,
                'total_enums': len(all_enums),
                'processing_metadata': all_metadata
            }
        }
        
        return package
    
    def _to_snake_case(self, name: str) -> str:
        """Convert PascalCase to snake_case."""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _calculate_imports(self, enums: List[dict]) -> List[str]:
        """Calculate required imports based on enum data."""
        imports = set(['from enum import Enum'])
        
        # Add other imports based on enum characteristics
        if any(enum.get('has_descriptions') for enum in enums):
            imports.add('from typing import Dict')
        
        return sorted(list(imports))


# Example usage for testing
if __name__ == '__main__':
    # This shows how to use the preprocessor
    preprocessor = EnumsPreprocessor()
    
    # Example: prepare data for diagram
    package = preprocessor.create_generation_package(
        typescript_files=['dipeo/models/src/enums.ts'],
        template_path='files/codegen/templates/models/enums.py.jinja2'
    )
    
    # Save package for diagram consumption
    with open('enums_generation_data.json', 'w') as f:
        json.dump(package, f, indent=2)
    
    print(f"Prepared package with {len(package['enums_data'])} enums")