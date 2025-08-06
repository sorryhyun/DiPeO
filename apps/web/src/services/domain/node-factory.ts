/**
 * Node Factory service - creates and configures nodes using @dipeo/models specifications
 * Leverages TypeScript specifications for type-safe node creation
 */

import {
  type DomainNode,
  type NodeID,
  type NodeType,
  type DomainHandle,
  type HandleID,
  HandleDirection,
  DataType,
  type Vec2,
  type HandleLabel,
  nodeSpecificationRegistry,
  getNodeSpecification,
  createHandleId,
} from '@dipeo/models';
import { ValidationService } from './validation-service';

/**
 * Node creation options
 */
interface CreateNodeOptions {
  position: { x: number; y: number };
  data?: Record<string, any>;
  id?: NodeID;
  width?: number;
  height?: number;
}

/**
 * Validation error interface
 */
export interface ValidationError {
  field?: string;
  message: string;
}

/**
 * Result type for operations that can fail
 */
export type Result<T, E> = 
  | { success: true; data: T }
  | { success: false; error: E };

/**
 * Node Factory service
 */
export class NodeFactory {
  /**
   * Create a new node with proper initialization from specifications
   * Supports both signatures for backward compatibility
   */
  static createNode(type: NodeType, position: { x: number; y: number }, data?: Partial<Record<string, any>>): DomainNode;
  static createNode(type: NodeType, options: CreateNodeOptions): DomainNode;
  static createNode(
    type: NodeType, 
    positionOrOptions: { x: number; y: number } | CreateNodeOptions, 
    data?: Partial<Record<string, any>>
  ): DomainNode {
    // Normalize arguments to options format
    const options: CreateNodeOptions = 
      'position' in positionOrOptions 
        ? positionOrOptions 
        : { position: positionOrOptions, data };
    const nodeSpec = getNodeSpecification(type);
    if (!nodeSpec) {
      throw new Error(`Unknown node type: ${type}`);
    }
    
    const nodeId = options.id || this.generateNodeId();
    const defaultData = this.getDefaultDataFromSpec(nodeSpec);
    
    return {
      id: nodeId,
      type,
      position: options.position,
      data: {
        ...defaultData,
        ...options.data,
      },
    };
  }
  
  /**
   * Create handles for a node based on its specification
   */
  static createNodeHandles(nodeId: NodeID, type: NodeType): DomainHandle[] {
    const nodeSpec = getNodeSpecification(type);
    if (!nodeSpec) {
      return [];
    }
    
    const handles: DomainHandle[] = [];
    
    // Create input handles
    if (nodeSpec.inputs) {
      nodeSpec.inputs.forEach((input: any) => {
        const handleId = createHandleId(nodeId, input.name, HandleDirection.INPUT);
        handles.push({
          id: handleId,
          node_id: nodeId,
          label: (input.label || input.name) as HandleLabel,
          direction: HandleDirection.INPUT,
          data_type: this.mapToDataType(input.type),
          position: null,
        });
      });
    }
    
    // Create output handles
    if (nodeSpec.outputs) {
      nodeSpec.outputs.forEach((output: any) => {
        const handleId = createHandleId(nodeId, output.name, HandleDirection.OUTPUT);
        handles.push({
          id: handleId,
          node_id: nodeId,
          label: (output.label || output.name) as HandleLabel,
          direction: HandleDirection.OUTPUT,
          data_type: this.mapToDataType(output.type),
          position: null,
        });
      });
    }
    
    return handles;
  }
  
  /**
   * Get default data from specification
   */
  private static getDefaultDataFromSpec(spec: any): Record<string, any> {
    const defaultData: Record<string, any> = {};
    
    if (spec.fields) {
      spec.fields.forEach((field: any) => {
        if (field.defaultValue !== undefined) {
          defaultData[field.name] = field.defaultValue;
        } else if (field.required) {
          // Set default values for required fields
          defaultData[field.name] = this.getDefaultValueForType(field.type);
        }
      });
    }
    
    return defaultData;
  }
  
  /**
   * Get default value for a field type
   */
  private static getDefaultValueForType(type: string): any {
    switch (type) {
      case 'string':
        return '';
      case 'number':
        return 0;
      case 'boolean':
        return false;
      case 'array':
        return [];
      case 'object':
        return {};
      default:
        return null;
    }
  }
  
  /**
   * Map specification type to handle type
   */
  private static mapToDataType(type: string): DataType {
    switch (type) {
      case 'string':
        return DataType.STRING;
      case 'number':
        return DataType.NUMBER;
      case 'boolean':
        return DataType.BOOLEAN;
      case 'object':
        return DataType.OBJECT;
      case 'array':
        return DataType.ARRAY;
      case 'any':
      default:
        return DataType.ANY;
    }
  }
  
  /**
   * Generate a unique node ID
   */
  private static generateNodeId(): NodeID {
    return `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}` as NodeID;
  }
  
  /**
   * Clone a node with a new ID
   */
  static cloneNode(node: DomainNode, position?: { x: number; y: number }): DomainNode {
    return {
      ...node,
      id: this.generateNodeId(),
      position: position || {
        x: node.position.x + 50,
        y: node.position.y + 50,
      },
      data: { ...node.data },
    };
  }
  
  /**
   * Get node display information from specification
   */
  static getNodeDisplayInfo(type: NodeType): {
    name: string;
    icon: string;
    color: string;
    category: string;
    description: string;
  } {
    const spec = getNodeSpecification(type);
    if (!spec) {
      return {
        name: type,
        icon: '📦',
        color: '#666',
        category: 'unknown',
        description: 'Unknown node type',
      };
    }
    
    return {
      name: spec.displayName,
      icon: spec.icon || '📦',
      color: spec.color || '#666',
      category: spec.category,
      description: spec.description,
    };
  }
  
  /**
   * Get all available node types grouped by category
   */
  static getNodeTypesByCategory(): Map<string, NodeType[]> {
    const categories = new Map<string, NodeType[]>();
    
    Object.entries(nodeSpecificationRegistry).forEach(([key, spec]) => {
      const category = spec.category;
      if (!categories.has(category)) {
        categories.set(category, []);
      }
      categories.get(category)!.push(spec.nodeType);
    });
    
    return categories;
  }
  
  /**
   * Validate node data against specification
   */
  static validateNodeData(type: NodeType, data: any): {
    valid: boolean;
    errors: string[];
  } {
    const spec = getNodeSpecification(type);
    if (!spec) {
      return {
        valid: false,
        errors: [`Unknown node type: ${type}`],
      };
    }
    
    const errors: string[] = [];
    
    // Validate required fields
    if (spec.fields) {
      spec.fields.forEach((field: any) => {
        if (field.required && (data[field.name] === undefined || data[field.name] === null)) {
          errors.push(`Required field '${field.name}' is missing`);
        }
        
        // Type validation
        if (data[field.name] !== undefined) {
          const actualType = typeof data[field.name];
          const expectedType = field.type;
          
          if (expectedType === 'number' && actualType !== 'number') {
            errors.push(`Field '${field.name}' must be a number`);
          } else if (expectedType === 'string' && actualType !== 'string') {
            errors.push(`Field '${field.name}' must be a string`);
          } else if (expectedType === 'boolean' && actualType !== 'boolean') {
            errors.push(`Field '${field.name}' must be a boolean`);
          }
        }
        
        // Enum validation
        if (field.validation?.allowedValues && data[field.name] !== undefined) {
          if (!field.validation.allowedValues.includes(data[field.name])) {
            errors.push(`Field '${field.name}' must be one of: ${field.validation.allowedValues.join(', ')}`);
          }
        }
      });
    }
    
    return {
      valid: errors.length === 0,
      errors,
    };
  }
  
  /**
   * Get field metadata for a node type
   */
  static getNodeFields(type: NodeType): any[] {
    const spec = getNodeSpecification(type);
    return spec?.fields || [];
  }
  
  /**
   * Check if nodes can be connected
   */
  static canConnect(
    sourceType: NodeType,
    sourceOutput: string,
    targetType: NodeType,
    targetInput: string,
  ): boolean {
    const sourceSpec = getNodeSpecification(sourceType);
    const targetSpec = getNodeSpecification(targetType);
    
    if (!sourceSpec || !targetSpec) {
      return false;
    }
    
    // Find output in source
    const output = sourceSpec.outputs?.find((o: any) => o.name === sourceOutput);
    if (!output) {
      return false;
    }
    
    // Find input in target
    const input = targetSpec.inputs?.find((i: any) => i.name === targetInput);
    if (!input) {
      return false;
    }
    
    // Check type compatibility
    if (output.type === 'any' || input.type === 'any') {
      return true;
    }
    
    return output.type === input.type;
  }

  /**
   * Create a node with validation
   * @param type - Node type enum
   * @param position - Node position
   * @param data - Optional partial node data
   * @returns Result with created node or validation error
   */
  static createNodeWithValidation<T extends NodeType>(
    type: T,
    position: { x: number; y: number },
    data?: Partial<Record<string, any>>
  ): Result<DomainNode, ValidationError[]> {
    try {
      // Create the node
      const node = this.createNode(type, { position, data });

      // Validate the node data
      const validationResult = ValidationService.validateNodeData(type, node.data);
      
      if (!validationResult.success) {
        const errors: ValidationError[] = [];
        
        if ('error' in validationResult && validationResult.error) {
          const zodError = validationResult.error as any;
          if (zodError.issues) {
            for (const issue of zodError.issues) {
              errors.push({
                field: issue.path.join('.'),
                message: issue.message,
              });
            }
          }
        }

        return { success: false, error: errors };
      }

      return { success: true, data: node };
    } catch (error) {
      return {
        success: false,
        error: [{
          message: error instanceof Error ? error.message : 'Unknown error creating node',
        }],
      };
    }
  }

  /**
   * Create a batch of nodes efficiently
   * @param specs - Array of node creation specs
   * @returns Array of created nodes
   */
  static createBatch(
    specs: Array<{
      type: NodeType;
      position: { x: number; y: number };
      data?: Partial<Record<string, any>>;
    }>
  ): DomainNode[] {
    return specs.map(spec => this.createNode(spec.type, { position: spec.position, data: spec.data }));
  }

  /**
   * Create a batch of nodes with validation
   * @param specs - Array of node creation specs
   * @returns Result with created nodes or validation errors
   */
  static createBatchWithValidation(
    specs: Array<{
      type: NodeType;
      position: { x: number; y: number };
      data?: Partial<Record<string, any>>;
    }>
  ): Result<DomainNode[], Map<number, ValidationError[]>> {
    const nodes: DomainNode[] = [];
    const errors = new Map<number, ValidationError[]>();
    
    for (let i = 0; i < specs.length; i++) {
      const spec = specs[i];
      const result = spec ? this.createNodeWithValidation(spec.type, spec.position, spec.data) : { success: false, error: [{ message: 'Invalid spec' }] };
      
      if ('data' in result && result.success) {
        nodes.push(result.data);
      } else {
        errors.set(i, result.error);
      }
    }

    if (errors.size > 0) {
      return { success: false, error: errors };
    }

    return { success: true, data: nodes };
  }
}