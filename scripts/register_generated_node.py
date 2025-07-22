#!/usr/bin/env python3
"""
Semi-automated registration script for newly generated DiPeO nodes.
This script reads the registry_updates.json and provides detailed instructions
and code snippets for completing the manual registration steps.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Get project root from environment or use current working directory
PROJECT_ROOT = Path(os.getenv('DIPEO_BASE_DIR', os.getcwd()))


def load_registry_updates() -> Dict[str, Any]:
    """Load the registry updates from the last codegen run."""
    registry_file = PROJECT_ROOT / 'output' / 'generated' / 'registry_updates.json'
    
    if not registry_file.exists():
        print("❌ No registry_updates.json found. Please run the codegen diagram first.")
        sys.exit(1)
    
    with open(registry_file, 'r') as f:
        return json.load(f)


def generate_registration_instructions(registry_data: Dict[str, Any]) -> None:
    """Generate detailed instructions with code snippets for registration."""
    node_type = registry_data['nodeType']
    pascal_case = node_type.capitalize() + 'Node'
    camel_case = node_type[0].lower() + node_type[1:] if len(node_type) > 1 else node_type.lower()
    
    print(f"\n📋 Registration Instructions for '{node_type}' Node")
    print("=" * 60)
    
    # Step 1: NODE_TYPE_MAP
    print("\n1️⃣  Add to NODE_TYPE_MAP in dipeo/models/src/conversions.ts")
    print("   File: dipeo/models/src/conversions.ts")
    print("   Add this line in the NODE_TYPE_MAP:")
    print(f"   [{node_type}]: '{pascal_case}',")
    
    # Step 2: Import in generated_nodes.py
    print(f"\n2️⃣  Import {pascal_case} in dipeo/core/static/generated_nodes.py")
    print("   File: dipeo/core/static/generated_nodes.py")
    print("   This should be auto-generated when you run 'make codegen-models'")
    print("   Verify the import exists after running the command")
    
    # Step 3: GraphQL union types
    print("\n3️⃣  Add to GraphQL schema union types")
    print("   File: apps/server/src/dipeo_server/api/graphql/schema/nodes.graphql")
    print("   Add to the Node union type:")
    print(f"   | {pascal_case}")
    print("   Add to the NodeData union type:")
    print(f"   | {pascal_case}Data")
    
    # Step 4: Frontend node registry
    print("\n4️⃣  Register in frontend node registry")
    print("   File: apps/web/src/features/diagram-editor/config/nodeRegistry.ts")
    print("   Add these imports:")
    print(f"   import {{ {camel_case}Config }} from './nodes/generated/{camel_case}Config';")
    print(f"   import {{ {camel_case}Fields }} from './nodes/generated/{camel_case}Fields';")
    print("\n   Add to NODE_CONFIGS_MAP:")
    print(f"   [NodeType.{node_type}]: {{")
    print(f"     ...{camel_case}Config,")
    print(f"     fields: {camel_case}Fields,")
    print("   },")
    
    # Step 5: Handler implementation
    print(f"\n5️⃣  Create handler in dipeo/application/execution/handlers/{node_type}.py")
    print(f"   File: dipeo/application/execution/handlers/{node_type}.py")
    print("   Create a new handler file with this template:")
    print(f"""
```python
from typing import TYPE_CHECKING, Optional
from pydantic import BaseModel

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.core.static.generated_nodes import {pascal_case}
from dipeo.core.execution.node_output import DataOutput, ErrorOutput, NodeOutputProtocol
from dipeo.models import {pascal_case}Data, NodeType

if TYPE_CHECKING:
    from dipeo.application.execution.execution_runtime import ExecutionRuntime
    from dipeo.core.dynamic.execution_context import ExecutionContext


@register_handler
class {pascal_case}Handler(TypedNodeHandler[{pascal_case}]):
    
    @property
    def node_class(self) -> type[{pascal_case}]:
        return {pascal_case}
    
    @property
    def node_type(self) -> str:
        return NodeType.{node_type}.value
    
    @property
    def schema(self) -> type[BaseModel]:
        return {pascal_case}Data
    
    @property
    def requires_services(self) -> list[str]:
        return []
    
    @property
    def description(self) -> str:
        return "Handler for {node_type} node operations"
    
    def validate(self, request: ExecutionRequest[{pascal_case}]) -> Optional[str]:
        \"\"\"Validate the {node_type} configuration.\"\"\"
        # Add validation logic here
        return None
    
    async def execute_request(self, request: ExecutionRequest[{pascal_case}]) -> NodeOutputProtocol:
        \"\"\"Execute the {node_type} operation.\"\"\"
        node = request.node
        inputs = request.inputs
        
        try:
            # TODO: Implement your node logic here
            result = {{"message": "TODO: Implement {node_type} handler"}}
            
            return DataOutput(
                value={{"default": result}},
                node_id=node.id,
                metadata={{"success": True}}
            )
        
        except Exception as e:
            return ErrorOutput(
                value=str(e),
                node_id=node.id,
                error_type=type(e).__name__
            )
```""")
    
    # Step 6: Run make codegen
    print("\n6️⃣  Run 'make codegen' to regenerate all derived files")
    print("   This will:")
    print("   - Generate Python models from TypeScript")
    print("   - Update GraphQL resolvers")
    print("   - Generate TypeScript types")
    
    # Summary
    print(f"\n✅ Summary for '{node_type}' node:")
    print(f"   - {len(registry_data['files_generated'])} files successfully generated")
    if registry_data['files_missing']:
        print(f"   - ⚠️  {len(registry_data['files_missing'])} files missing")
    print(f"   - Success rate: {registry_data['generation_summary']['success_rate']}")
    
    # Generated files
    print("\n📁 Generated Files:")
    for file in registry_data['files_generated']:
        print(f"   ✓ {file}")
    
    print("\n🎯 Next Steps:")
    print("   1. Follow the manual registration steps above")
    print("   2. Run 'make codegen' to regenerate derived files")
    print("   3. Implement the handler logic")
    print("   4. Test the new node in the diagram editor")
    print("\n" + "=" * 60)


def main():
    """Main entry point."""
    print("🔧 DiPeO Node Registration Helper")
    
    # Load registry data
    registry_data = load_registry_updates()
    
    # Generate instructions
    generate_registration_instructions(registry_data)
    
    # Offer to create handler file
    node_type = registry_data['nodeType']
    handler_path = PROJECT_ROOT / 'dipeo' / 'application' / 'execution' / 'handlers' / f'{node_type}.py'
    
    if not handler_path.exists():
        response = input(f"\n💡 Would you like to create the handler file at {handler_path}? (y/n): ")
        if response.lower() == 'y':
            # Create the handler file content
            pascal_case = node_type.capitalize() + 'Node'
            handler_content = f'''"""Handler for {node_type} node operations."""
from typing import TYPE_CHECKING, Optional
from pydantic import BaseModel

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.core.static.generated_nodes import {pascal_case}
from dipeo.core.execution.node_output import DataOutput, ErrorOutput, NodeOutputProtocol
from dipeo.models import {pascal_case}Data, NodeType

if TYPE_CHECKING:
    from dipeo.application.execution.execution_runtime import ExecutionRuntime
    from dipeo.core.dynamic.execution_context import ExecutionContext


@register_handler
class {pascal_case}Handler(TypedNodeHandler[{pascal_case}]):
    """Handler for {node_type} node type."""
    
    @property
    def node_class(self) -> type[{pascal_case}]:
        return {pascal_case}
    
    @property
    def node_type(self) -> str:
        return NodeType.{node_type}.value
    
    @property
    def schema(self) -> type[BaseModel]:
        return {pascal_case}Data
    
    @property
    def requires_services(self) -> list[str]:
        return []
    
    @property
    def description(self) -> str:
        return "{registry_data.get('description', 'Handler for ' + node_type + ' node operations')}"
    
    def validate(self, request: ExecutionRequest[{pascal_case}]) -> Optional[str]:
        """Validate the {node_type} configuration."""
        node = request.node
        
        # TODO: Add validation logic based on node requirements
        # Example: Check required fields, validate URLs, etc.
        
        return None
    
    async def execute_request(self, request: ExecutionRequest[{pascal_case}]) -> NodeOutputProtocol:
        """Execute the {node_type} operation."""
        node = request.node
        inputs = request.inputs
        
        try:
            # TODO: Implement your node logic here
            # Access node properties: node.field_name
            # Access inputs: inputs.get('input_name')
            
            result = {{
                "message": f"TODO: Implement {node_type} handler",
                "node_id": str(node.id),
                "inputs_received": list(inputs.keys()) if inputs else []
            }}
            
            return DataOutput(
                value={{"default": result}},
                node_id=node.id,
                metadata={{"success": True}}
            )
        
        except Exception as e:
            return ErrorOutput(
                value=str(e),
                node_id=node.id,
                error_type=type(e).__name__,
                metadata={{"error_details": str(e)}}
            )
'''
            
            # Create the handler file
            handler_path.parent.mkdir(parents=True, exist_ok=True)
            with open(handler_path, 'w') as f:
                f.write(handler_content)
            
            print(f"\n✅ Handler file created at: {handler_path}")
            print("   Don't forget to implement the execute_request method!")
    
    print("\n🚀 Happy coding!")


if __name__ == '__main__':
    main()