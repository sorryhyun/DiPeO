/**
 * Automatic node registration functions for DiPeO code generation.
 * These functions update the necessary files to register new node types.
 */

import * as fs from 'fs';
import * as path from 'path';

interface RegistrationInputs {
  nodeType: string;
  displayName: string;
  category?: string;
}

interface RegistrationResult {
  success: boolean;
  message: string;
  filesUpdated: string[];
  errors?: string[];
}

/**
 * Main entry point for node registration
 */
export function main(inputs: { spec: RegistrationInputs }): RegistrationResult {
  const { nodeType, displayName, category = 'custom' } = inputs.spec;
  const filesUpdated: string[] = [];
  const errors: string[] = [];

  console.log(`Starting node registration for: ${nodeType}`);

  try {
    // 1. Update NODE_TYPE_MAP in conversions.ts
    const conversionsUpdated = updateNodeTypeMap(nodeType);
    if (conversionsUpdated) {
      filesUpdated.push('dipeo/models/src/conversions.ts');
    }

    // 2. Update generated_nodes.py imports
    const pythonNodesUpdated = updateGeneratedNodesPython(nodeType);
    if (pythonNodesUpdated) {
      filesUpdated.push('dipeo/core/static/generated_nodes.py');
    }

    // 3. Update frontend node registry
    const frontendRegistryUpdated = updateFrontendNodeRegistry(nodeType, displayName, category);
    if (frontendRegistryUpdated) {
      filesUpdated.push('apps/web/src/features/diagram/config/nodeRegistry.ts');
    }

    // 4. Update GraphQL schema unions
    const graphqlUpdated = updateGraphQLSchema(nodeType);
    if (graphqlUpdated) {
      filesUpdated.push('apps/server/src/dipeo_server/api/graphql/schema/nodes.graphql');
    }

    return {
      success: true,
      message: `Successfully registered ${nodeType} node type`,
      filesUpdated,
      errors
    };
  } catch (error) {
    return {
      success: false,
      message: `Failed to register ${nodeType}: ${error.message}`,
      filesUpdated,
      errors: [error.message]
    };
  }
}

/**
 * Update NODE_TYPE_MAP in conversions.ts
 */
function updateNodeTypeMap(nodeType: string): boolean {
  const filePath = path.join(process.cwd(), 'dipeo/models/src/conversions.ts');
  
  if (!fs.existsSync(filePath)) {
    console.error(`File not found: ${filePath}`);
    return false;
  }

  let content = fs.readFileSync(filePath, 'utf-8');
  
  // Check if already exists
  if (content.includes(`[NodeType.${nodeType}]`)) {
    console.log(`NODE_TYPE_MAP already contains ${nodeType}`);
    return false;
  }

  // Find the NODE_TYPE_MAP definition
  const mapStart = content.indexOf('export const NODE_TYPE_MAP');
  if (mapStart === -1) {
    throw new Error('NODE_TYPE_MAP not found in conversions.ts');
  }

  // Find the closing brace of NODE_TYPE_MAP
  const mapEnd = content.indexOf('};', mapStart);
  if (mapEnd === -1) {
    throw new Error('Could not find end of NODE_TYPE_MAP');
  }

  // Find the last entry before the closing brace
  const beforeEnd = content.lastIndexOf(',', mapEnd);
  
  // Create the new entry
  const pascalCase = nodeType.charAt(0).toUpperCase() + nodeType.slice(1);
  const newEntry = `\n  [NodeType.${nodeType}]: ${pascalCase}NodeData,`;
  
  // Insert the new entry
  content = content.slice(0, beforeEnd + 1) + newEntry + content.slice(beforeEnd + 1);
  
  fs.writeFileSync(filePath, content);
  console.log(`Updated NODE_TYPE_MAP with ${nodeType}`);
  return true;
}

/**
 * Update generated_nodes.py with the new node import
 */
function updateGeneratedNodesPython(nodeType: string): boolean {
  const filePath = path.join(process.cwd(), 'dipeo/core/static/generated_nodes.py');
  
  if (!fs.existsSync(filePath)) {
    console.error(`File not found: ${filePath}`);
    return false;
  }

  let content = fs.readFileSync(filePath, 'utf-8');
  
  // Check if already exists
  const pascalCase = nodeType.charAt(0).toUpperCase() + nodeType.slice(1);
  if (content.includes(`class ${pascalCase}Node`)) {
    console.log(`generated_nodes.py already contains ${pascalCase}Node`);
    return false;
  }

  // Find the last import
  const lastImportMatch = content.match(/from dipeo\.models import.*\n/g);
  if (!lastImportMatch) {
    throw new Error('Could not find imports in generated_nodes.py');
  }
  
  const lastImport = lastImportMatch[lastImportMatch.length - 1];
  const lastImportIndex = content.lastIndexOf(lastImport);
  
  // Add new import
  const newImport = `from dipeo.models import ${pascalCase}NodeData\n`;
  content = content.slice(0, lastImportIndex + lastImport.length) + 
            newImport + 
            content.slice(lastImportIndex + lastImport.length);

  // Find where to add the node class (before __all__)
  const allIndex = content.indexOf('__all__ = [');
  if (allIndex === -1) {
    throw new Error('Could not find __all__ in generated_nodes.py');
  }

  // Create the node class
  const nodeClass = `

@dataclass
class ${pascalCase}Node(BaseNode):
    """${pascalCase} node implementation."""
    
    # Core fields from BaseNode
    id: str
    type: NodeType
    label: str
    position: Position
    flipped: Optional[bool] = None
    
    # ${pascalCase}-specific fields
    # (Add fields from ${pascalCase}NodeData as needed)
    
    @classmethod
    def from_data(cls, data: ${pascalCase}NodeData) -> "${pascalCase}Node":
        """Create ${pascalCase}Node from ${pascalCase}NodeData."""
        return cls(
            id=data.id,
            type=data.type,
            label=data.label,
            position=data.position,
            flipped=data.flipped
        )
`;

  // Insert the node class before __all__
  content = content.slice(0, allIndex) + nodeClass + '\n' + content.slice(allIndex);

  // Update __all__
  const allEndIndex = content.indexOf(']', allIndex);
  const beforeEnd = content.lastIndexOf(',', allEndIndex);
  content = content.slice(0, beforeEnd + 1) + 
            `\n    "${pascalCase}Node",` + 
            content.slice(beforeEnd + 1);

  fs.writeFileSync(filePath, content);
  console.log(`Updated generated_nodes.py with ${pascalCase}Node`);
  return true;
}

/**
 * Update frontend node registry
 */
function updateFrontendNodeRegistry(nodeType: string, displayName: string, category: string): boolean {
  // For now, just log what needs to be done
  // In a real implementation, this would update the registry file
  console.log(`TODO: Update frontend node registry with ${nodeType}`);
  console.log(`  - Import ${nodeType}Config from './nodes/${nodeType}Config'`);
  console.log(`  - Add to nodeConfigs array`);
  return false;
}

/**
 * Update GraphQL schema unions
 */
function updateGraphQLSchema(nodeType: string): boolean {
  const filePath = path.join(process.cwd(), 'apps/server/src/dipeo_server/api/graphql/schema/nodes.graphql');
  
  if (!fs.existsSync(filePath)) {
    console.error(`File not found: ${filePath}`);
    return false;
  }

  let content = fs.readFileSync(filePath, 'utf-8');
  const pascalCase = nodeType.charAt(0).toUpperCase() + nodeType.slice(1);
  
  // Check if already exists
  if (content.includes(`${pascalCase}NodeData`)) {
    console.log(`GraphQL schema already contains ${pascalCase}NodeData`);
    return false;
  }

  // Update NodeData union
  const nodeDataUnion = content.match(/union NodeData = ([^]+?)(?=\n\n|union)/);
  if (nodeDataUnion) {
    const updatedUnion = nodeDataUnion[0] + ` | ${pascalCase}NodeData`;
    content = content.replace(nodeDataUnion[0], updatedUnion);
  }

  // Update NodeInput union  
  const nodeInputUnion = content.match(/union NodeInput = ([^]+?)(?=\n\n|type)/);
  if (nodeInputUnion) {
    const updatedUnion = nodeInputUnion[0] + ` | ${pascalCase}NodeInput`;
    content = content.replace(nodeInputUnion[0], updatedUnion);
  }

  fs.writeFileSync(filePath, content);
  console.log(`Updated GraphQL schema unions with ${pascalCase}NodeData and ${pascalCase}NodeInput`);
  return true;
}

/**
 * Register a node handler in the handler factory
 */
export function registerNodeHandler(inputs: { nodeType: string }): RegistrationResult {
  const { nodeType } = inputs;
  const pascalCase = nodeType.charAt(0).toUpperCase() + nodeType.slice(1);
  
  // Create handler file path
  const handlerPath = path.join(process.cwd(), `dipeo/application/execution/handlers/${nodeType}.py`);
  
  // Check if handler already exists
  if (fs.existsSync(handlerPath)) {
    return {
      success: false,
      message: `Handler already exists for ${nodeType}`,
      filesUpdated: []
    };
  }

  // Create handler template
  const handlerTemplate = `"""
Handler for ${nodeType} node type.
"""
from typing import TYPE_CHECKING, Optional
from pydantic import BaseModel

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.core.static.generated_nodes import ${pascalCase}Node
from dipeo.core.execution.node_output import TextOutput, ErrorOutput, NodeOutputProtocol
from dipeo.models import ${pascalCase}NodeData, NodeType

if TYPE_CHECKING:
    from dipeo.application.execution.execution_runtime import ExecutionRuntime
    from dipeo.core.dynamic.execution_context import ExecutionContext


@register_handler
class ${pascalCase}NodeHandler(TypedNodeHandler[${pascalCase}Node]):
    """Handler for ${nodeType} nodes."""
    
    @property
    def node_class(self) -> type[${pascalCase}Node]:
        return ${pascalCase}Node
    
    @property
    def node_type(self) -> str:
        return NodeType.${nodeType}.value
    
    @property
    def schema(self) -> type[BaseModel]:
        return ${pascalCase}NodeData
    
    @property
    def requires_services(self) -> list[str]:
        return []
    
    @property
    def description(self) -> str:
        return "Handler for ${nodeType} node operations"
    
    def validate(self, request: ExecutionRequest[${pascalCase}Node]) -> Optional[str]:
        """Validate the ${nodeType} node configuration."""
        # Add validation logic here
        return None
    
    async def execute_request(self, request: ExecutionRequest[${pascalCase}Node]) -> NodeOutputProtocol:
        """Execute the ${nodeType} node."""
        node = request.node
        inputs = request.inputs
        
        try:
            # TODO: Implement ${nodeType} logic here
            result = f"${pascalCase} node executed with label: {node.label}"
            
            return TextOutput(
                value=result,
                node_id=node.id,
                metadata={"success": True}
            )
        
        except Exception as e:
            return ErrorOutput(
                value=str(e),
                node_id=node.id,
                error_type=type(e).__name__
            )
`;

  fs.writeFileSync(handlerPath, handlerTemplate);
  
  // Update __init__.py
  const initPath = path.join(process.cwd(), 'dipeo/application/execution/handlers/__init__.py');
  if (fs.existsSync(initPath)) {
    let initContent = fs.readFileSync(initPath, 'utf-8');
    initContent += `\nfrom .${nodeType} import ${pascalCase}NodeHandler`;
    fs.writeFileSync(initPath, initContent);
  }

  return {
    success: true,
    message: `Created handler for ${nodeType}`,
    filesUpdated: [handlerPath, initPath]
  };
}