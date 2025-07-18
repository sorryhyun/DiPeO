#!/usr/bin/env python3
"""
Automates the integration of generated entity code into the existing GraphQL structure.

This script performs the following tasks:
1. Updates mutations/__init__.py with new mutation classes
2. Integrates query methods into the main Query class
3. Merges generated types into generated_types.py
4. Creates service stubs if they don't exist
"""

import ast
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import argparse
import sys


class ASTModifier:
    """Utility class for AST-based file modifications."""
    
    @staticmethod
    def add_import(tree: ast.Module, module: str, names: List[str]) -> bool:
        """Add an import statement if it doesn't exist."""
        # Check if import already exists
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == module:
                existing_names = {alias.name for alias in node.names}
                if all(name in existing_names for name in names):
                    return False  # Import already exists
        
        # Add import at the appropriate position
        import_node = ast.ImportFrom(
            module=module,
            names=[ast.alias(name=name, asname=None) for name in names],
            level=0
        )
        
        # Find the last import statement
        last_import_idx = 0
        for i, node in enumerate(tree.body):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                last_import_idx = i
        
        tree.body.insert(last_import_idx + 1, import_node)
        return True
    
    @staticmethod
    def add_to_inheritance_list(tree: ast.Module, class_name: str, base: str) -> bool:
        """Add a base class to a class's inheritance list."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                # Check if base already exists
                for base_node in node.bases:
                    if isinstance(base_node, ast.Name) and base_node.id == base:
                        return False  # Already inherits
                
                # Add to inheritance list
                node.bases.append(ast.Name(id=base, ctx=ast.Load()))
                return True
        return False


class EntityIntegrator:
    def __init__(self, server_path: Path, dry_run: bool = False):
        self.server_path = server_path
        self.dry_run = dry_run
        self.graphql_path = server_path / "src" / "dipeo_server" / "api" / "graphql"
        self.mutations_path = self.graphql_path / "mutations"
        self.queries_path = self.graphql_path / "queries"
        self.types_path = self.graphql_path / "types"
        
    def find_generated_files(self) -> Dict[str, List[Path]]:
        """Find all generated entity files."""
        generated = {
            'mutations': [],
            'queries': [],
            'types': []
        }
        
        # Find mutation files
        mutations_gen = self.mutations_path / "generated"
        if mutations_gen.exists():
            generated['mutations'] = list(mutations_gen.glob("*_mutations.py"))
        
        # Find query files
        queries_gen = self.queries_path / "generated"
        if queries_gen.exists():
            generated['queries'] = list(queries_gen.glob("*_queries.py"))
        
        # Find type additions
        types_gen = self.types_path / "generated"
        if types_gen.exists():
            generated['types'] = list(types_gen.glob("*_types.py"))
        
        return generated
    
    def integrate_mutations(self, mutation_files: List[Path]) -> List[str]:
        """Integrate mutation classes into mutations/__init__.py."""
        messages = []
        init_file = self.mutations_path / "__init__.py"
        
        if not init_file.exists():
            messages.append(f"ERROR: {init_file} not found")
            return messages
        
        # Read and parse the init file
        content = init_file.read_text()
        tree = ast.parse(content)
        
        modified = False
        for mutation_file in mutation_files:
            # Extract entity name from filename (e.g., task_mutations.py -> Task)
            entity_name = mutation_file.stem.replace('_mutations', '')
            entity_class = f"{entity_name.title()}Mutations"
            
            # Parse the mutation file to get the class name
            mutation_content = mutation_file.read_text()
            mutation_tree = ast.parse(mutation_content)
            
            # Find the actual class name
            actual_class_name = None
            for node in ast.walk(mutation_tree):
                if isinstance(node, ast.ClassDef) and 'Mutations' in node.name:
                    actual_class_name = node.name
                    break
            
            if not actual_class_name:
                messages.append(f"WARNING: No mutation class found in {mutation_file}")
                continue
            
            # Add import
            module_path = f".generated.{mutation_file.stem}"
            if ASTModifier.add_import(tree, module_path, [actual_class_name]):
                modified = True
                messages.append(f"Added import for {actual_class_name}")
            
            # Add to Mutation class inheritance
            if ASTModifier.add_to_inheritance_list(tree, "Mutation", actual_class_name):
                modified = True
                messages.append(f"Added {actual_class_name} to Mutation inheritance")
        
        # Write back if modified
        if modified and not self.dry_run:
            code = ast.unparse(tree)
            init_file.write_text(code)
            messages.append("Updated mutations/__init__.py")
        elif modified:
            messages.append("Would update mutations/__init__.py (dry-run)")
        
        return messages
    
    def integrate_queries(self, query_files: List[Path]) -> List[str]:
        """Integrate query methods into the main Query class."""
        messages = []
        queries_file = self.graphql_path / "queries.py"
        
        if not queries_file.exists():
            messages.append(f"ERROR: {queries_file} not found")
            return messages
        
        content = queries_file.read_text()
        tree = ast.parse(content)
        
        # Find the Query class
        query_class = None
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == "Query":
                query_class = node
                break
        
        if not query_class:
            messages.append("ERROR: Query class not found")
            return messages
        
        modified = False
        for query_file in query_files:
            # Parse the query file
            query_content = query_file.read_text()
            query_tree = ast.parse(query_content)
            
            # Find all query methods
            for node in query_tree.body:
                if isinstance(node, ast.ClassDef):
                    for method in node.body:
                        if isinstance(method, ast.FunctionDef) and not method.name.startswith('_'):
                            # Check if method already exists
                            method_exists = False
                            for existing in query_class.body:
                                if isinstance(existing, ast.FunctionDef) and existing.name == method.name:
                                    method_exists = True
                                    break
                            
                            if not method_exists:
                                query_class.body.append(method)
                                modified = True
                                messages.append(f"Added query method: {method.name}")
            
            # Add necessary imports
            entity_name = query_file.stem.replace('_queries', '')
            service_name = f"{entity_name}_service"
            
            # Check if we need to add service import
            if ASTModifier.add_import(tree, "dipeo_server.container", [service_name]):
                modified = True
                messages.append(f"Added import for {service_name}")
        
        # Write back if modified
        if modified and not self.dry_run:
            code = ast.unparse(tree)
            queries_file.write_text(code)
            messages.append("Updated queries.py")
        elif modified:
            messages.append("Would update queries.py (dry-run)")
        
        return messages
    
    def integrate_types(self, type_files: List[Path]) -> List[str]:
        """Merge generated types into generated_types.py."""
        messages = []
        generated_types_file = self.types_path / "generated_types.py"
        
        if not generated_types_file.exists():
            messages.append(f"ERROR: {generated_types_file} not found")
            return messages
        
        content = generated_types_file.read_text()
        
        # Find the __all__ list
        all_match = re.search(r'__all__\s*=\s*\[(.*?)\]', content, re.DOTALL)
        if not all_match:
            messages.append("ERROR: __all__ list not found in generated_types.py")
            return messages
        
        existing_exports = set(re.findall(r'"(\w+)"', all_match.group(1)))
        new_types = []
        new_exports = []
        
        for type_file in type_files:
            type_content = type_file.read_text()
            
            # Extract type definitions
            tree = ast.parse(type_content)
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    if node.name not in existing_exports:
                        # Get the source code for this class
                        start_line = node.lineno - 1
                        end_line = node.end_lineno
                        lines = type_content.split('\n')
                        class_code = '\n'.join(lines[start_line:end_line])
                        
                        new_types.append(class_code)
                        new_exports.append(node.name)
                        messages.append(f"Found new type: {node.name}")
        
        if new_types and not self.dry_run:
            # Add new types before __all__
            all_start = content.find('__all__')
            new_content = content[:all_start] + '\n\n' + '\n\n'.join(new_types) + '\n\n' + content[all_start:]
            
            # Update __all__ list
            updated_exports = sorted(list(existing_exports) + new_exports)
            all_list = '[\n    ' + ',\n    '.join(f'"{e}"' for e in updated_exports) + '\n]'
            new_content = re.sub(r'__all__\s*=\s*\[.*?\]', f'__all__ = {all_list}', new_content, flags=re.DOTALL)
            
            generated_types_file.write_text(new_content)
            messages.append("Updated generated_types.py")
        elif new_types:
            messages.append("Would update generated_types.py (dry-run)")
        
        return messages
    
    def check_services(self, entity_names: List[str]) -> List[str]:
        """Check if required services exist and create stubs if needed."""
        messages = []
        services_path = self.server_path / "src" / "dipeo_server" / "services"
        
        for entity_name in entity_names:
            service_name = f"{entity_name}_service"
            service_file = services_path / f"{service_name}.py"
            
            if not service_file.exists():
                messages.append(f"WARNING: Service {service_name} does not exist")
                
                if not self.dry_run:
                    # Create a basic service stub
                    stub_content = f'''"""
{entity_name.title()} service implementation.
Auto-generated stub - implement actual business logic.
"""

from typing import List, Optional, Dict, Any
from dipeo.core.models import {entity_name.title()}ID, {entity_name.title()}


class {entity_name.title()}Service:
    """Service for managing {entity_name} entities."""
    
    async def get(self, id: {entity_name.title()}ID) -> Optional[{entity_name.title()}]:
        """Get a {entity_name} by ID."""
        # TODO: Implement actual data retrieval
        raise NotImplementedError("Service method not implemented")
    
    async def list(self, filters: Dict[str, Any]) -> List[{entity_name.title()}]:
        """List {entity_name}s with optional filters."""
        # TODO: Implement actual data retrieval
        raise NotImplementedError("Service method not implemented")
    
    async def create(self, data: Dict[str, Any]) -> {entity_name.title()}:
        """Create a new {entity_name}."""
        # TODO: Implement actual creation logic
        raise NotImplementedError("Service method not implemented")
    
    async def update(self, id: {entity_name.title()}ID, data: Dict[str, Any]) -> {entity_name.title()}:
        """Update an existing {entity_name}."""
        # TODO: Implement actual update logic
        raise NotImplementedError("Service method not implemented")
    
    async def delete(self, id: {entity_name.title()}ID) -> bool:
        """Delete a {entity_name}."""
        # TODO: Implement actual deletion logic
        raise NotImplementedError("Service method not implemented")
'''
                    service_file.write_text(stub_content)
                    messages.append(f"Created service stub: {service_file}")
                else:
                    messages.append(f"Would create service stub: {service_file} (dry-run)")
        
        return messages
    
    def integrate_all(self) -> List[str]:
        """Run all integration steps."""
        messages = []
        
        # Find generated files
        generated = self.find_generated_files()
        
        if not any(generated.values()):
            messages.append("No generated files found to integrate")
            return messages
        
        # Extract entity names
        entity_names = set()
        for mutation_file in generated['mutations']:
            entity_name = mutation_file.stem.replace('_mutations', '')
            entity_names.add(entity_name)
        
        # Run integration steps
        messages.extend(self.integrate_mutations(generated['mutations']))
        messages.extend(self.integrate_queries(generated['queries']))
        messages.extend(self.integrate_types(generated['types']))
        messages.extend(self.check_services(list(entity_names)))
        
        return messages


def main():
    parser = argparse.ArgumentParser(
        description="Integrate generated entity code into the GraphQL structure"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--server-path",
        type=Path,
        default=Path(__file__).parent.parent.parent.parent / "apps" / "server",
        help="Path to the server directory"
    )
    
    args = parser.parse_args()
    
    if not args.server_path.exists():
        print(f"ERROR: Server path not found: {args.server_path}")
        sys.exit(1)
    
    integrator = EntityIntegrator(args.server_path, args.dry_run)
    messages = integrator.integrate_all()
    
    for message in messages:
        print(message)
    
    if args.dry_run:
        print("\nDry-run complete. No files were modified.")
    else:
        print("\nIntegration complete.")


if __name__ == "__main__":
    main()