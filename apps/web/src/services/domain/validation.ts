/**
 * Validation domain service - centralized business validation rules
 * Leverages @dipeo/models specifications for type-safe validation
 */

import type {
  DomainNode,
  DomainArrow,
  DomainDiagram,
  DomainPerson,
  NodeID,
  HandleID,
  LLMService,
} from '@dipeo/models';
import { NodeType } from '@dipeo/models';
import { 
  isValidLLMService,
  isValidAPIServiceType,
} from '@dipeo/models';
import { z } from 'zod';
import { NODE_DATA_SCHEMAS, getNodeDataSchema } from '@/__generated__/schemas';

/**
 * Validation result type
 */
export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  nodeErrors?: Map<NodeID, ValidationError[]>;
  connectionErrors?: ValidationError[];
  generalErrors?: ValidationError[];
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

export interface ValidationWarning {
  field: string;
  message: string;
}

/**
 * Validation service for business rules
 */
export class ValidationService {
  /**
   * Get node validation schema from generated schemas
   */
  private static getNodeSchema(nodeType: NodeType): z.ZodSchema | undefined {
    // Map NodeType enum to string key for schema lookup
    const schemaKey = nodeType.toLowerCase().replace(/_/g, '_');
    return getNodeDataSchema(schemaKey);
  }
  
  /**
   * Validate a node
   */
  static validateNode(node: DomainNode): ValidationResult {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];
    
    // Get schema for node type from generated schemas
    const schema = this.getNodeSchema(node.type);
    if (!schema) {
      // Node type might not need validation (e.g., START node)
      // Only error if it's truly unknown
      const knownTypes = Object.values(NodeType);
      if (!knownTypes.includes(node.type)) {
        errors.push({
          field: 'type',
          message: `Unknown node type: ${node.type}`,
          code: 'UNKNOWN_NODE_TYPE',
        });
        return { valid: false, errors, warnings };
      }
    }
    
    // Validate node data if schema exists
    if (schema) {
      try {
        schema.parse(node.data);
      } catch (error) {
        if (error instanceof z.ZodError) {
          error.errors.forEach(err => {
            errors.push({
              field: err.path.join('.'),
              message: err.message,
              code: 'VALIDATION_ERROR',
            });
          });
        }
      }
    }
    
    // Additional business rule validations
    this.validateNodeBusinessRules(node, errors, warnings);
    
    return {
      valid: errors.length === 0,
      errors,
      warnings,
    };
  }
  
  /**
   * Validate node business rules
   */
  private static validateNodeBusinessRules(
    node: DomainNode,
    errors: ValidationError[],
    warnings: ValidationWarning[],
  ): void {
    switch (node.type) {
      case NodeType.PERSON_JOB:
      case NodeType.PERSON_BATCH_JOB:
        // Warn if no person is selected
        if (!node.data.person) {
          warnings.push({
            field: 'person',
            message: 'No person selected, will use default settings',
          });
        }
        break;
        
      case NodeType.SUB_DIAGRAM:
        // Check if diagram exists
        if (node.data.diagram_name && !this.diagramExists(node.data.diagram_name)) {
          errors.push({
            field: 'diagram_name',
            message: 'Referenced diagram does not exist',
            code: 'DIAGRAM_NOT_FOUND',
          });
        }
        break;
        
      case NodeType.ENDPOINT:
        // Warn about insecure URLs
        if (node.data.url?.startsWith('http://')) {
          warnings.push({
            field: 'url',
            message: 'Using insecure HTTP connection',
          });
        }
        break;
    }
  }
  
  /**
   * Validate a person configuration
   */
  static validatePerson(person: DomainPerson): ValidationResult {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];
    
    const schema = z.object({
      name: z.string().min(1).max(100),
      role: z.string().min(1).max(200),
      model: z.string().refine(isValidLLMService, 'Invalid LLM service'),
      system_prompt: z.string().max(10000).optional(),
      tools_enabled: z.boolean().optional(),
      max_tokens: z.number().min(1).max(100000).optional(),
    });
    
    try {
      schema.parse(person);
    } catch (error) {
      if (error instanceof z.ZodError) {
        error.errors.forEach(err => {
          errors.push({
            field: err.path.join('.'),
            message: err.message,
            code: 'VALIDATION_ERROR',
          });
        });
      }
    }
    
    // Additional person-specific validations can be added here
    
    return {
      valid: errors.length === 0,
      errors,
      warnings,
    };
  }
  
  /**
   * Validate a diagram
   */
  static validateDiagram(diagram: DomainDiagram): ValidationResult {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];
    
    // Must have at least one node
    if (diagram.nodes.length === 0) {
      errors.push({
        field: 'nodes',
        message: 'Diagram must have at least one node',
        code: 'EMPTY_DIAGRAM',
      });
    }
    
    // Must have a START node
    const hasStart = diagram.nodes.some(n => n.type === NodeType.START);
    if (!hasStart && diagram.nodes.length > 0) {
      errors.push({
        field: 'nodes',
        message: 'Diagram must have a START node',
        code: 'NO_START_NODE',
      });
    }
    
    // Validate all nodes
    diagram.nodes.forEach(node => {
      const nodeValidation = this.validateNode(node);
      errors.push(...nodeValidation.errors.map(e => ({
        ...e,
        field: `nodes.${node.id}.${e.field}`,
      })));
      warnings.push(...nodeValidation.warnings.map(w => ({
        ...w,
        field: `nodes.${node.id}.${w.field}`,
      })));
    });
    
    // Validate arrow connections
    diagram.arrows.forEach(arrow => {
      // Arrow source/target are HandleIDs, extract node IDs
      const sourceNodeId = arrow.source.split('_')[0] as NodeID;
      const targetNodeId = arrow.target.split('_')[0] as NodeID;
      
      const sourceExists = diagram.nodes.some(n => n.id === sourceNodeId);
      const targetExists = diagram.nodes.some(n => n.id === targetNodeId);
      
      if (!sourceExists) {
        errors.push({
          field: `arrows.${arrow.id}`,
          message: `Source node ${sourceNodeId} does not exist`,
          code: 'INVALID_SOURCE',
        });
      }
      
      if (!targetExists) {
        errors.push({
          field: `arrows.${arrow.id}`,
          message: `Target node ${targetNodeId} does not exist`,
          code: 'INVALID_TARGET',
        });
      }
    });
    
    // Check for disconnected nodes
    const connectedNodes = new Set<NodeID>();
    diagram.arrows.forEach(arrow => {
      // Extract node IDs from handle IDs
      const sourceNodeId = arrow.source.split('_')[0] as NodeID;
      const targetNodeId = arrow.target.split('_')[0] as NodeID;
      connectedNodes.add(sourceNodeId);
      connectedNodes.add(targetNodeId);
    });
    
    diagram.nodes.forEach(node => {
      if (node.type !== NodeType.START && !connectedNodes.has(node.id)) {
        warnings.push({
          field: `nodes.${node.id}`,
          message: 'Node is not connected to any other nodes',
        });
      }
    });
    
    return {
      valid: errors.length === 0,
      errors,
      warnings,
    };
  }
  
  /**
   * Helper to check if diagram exists (would query backend)
   */
  private static diagramExists(name: string): boolean {
    // This would actually query the backend
    return true;
  }
  
  /**
   * Validate form data against a schema
   */
  static validateFormData<T>(
    data: unknown,
    schema: z.ZodSchema<T>,
  ): { valid: boolean; data?: T; errors?: z.ZodError } {
    try {
      const validated = schema.parse(data);
      return { valid: true, data: validated };
    } catch (error) {
      if (error instanceof z.ZodError) {
        return { valid: false, errors: error };
      }
      throw error;
    }
  }
  
  /**
   * Get field validation messages for a specific node type and field
   */
  static getFieldValidationMessages(
    nodeType: NodeType | string,
    fieldName: string,
    value: unknown,
  ): string[] {
    const messages: string[] = [];
    
    // Get the schema for this node type
    const nodeTypeEnum = typeof nodeType === 'string' 
      ? nodeType.toUpperCase().replace(/-/g, '_') as NodeType
      : nodeType;
    const schema = this.getNodeSchema(nodeTypeEnum);
    
    if (!schema) {
      return messages;
    }
    
    // Try to parse just this field
    try {
      const fieldData = { [fieldName]: value };
      schema.partial().parse(fieldData);
    } catch (error) {
      if (error instanceof z.ZodError) {
        error.errors.forEach(err => {
          if (err.path[0] === fieldName) {
            messages.push(err.message);
          }
        });
      }
    }
    
    return messages;
  }
  
  /**
   * Get field errors for a node
   */
  static getFieldErrors(
    nodeType: NodeType | string,
    data: Record<string, unknown>,
  ): Record<string, string[]> {
    const fieldErrors: Record<string, string[]> = {};
    
    // Get the schema for this node type
    const nodeTypeEnum = typeof nodeType === 'string'
      ? nodeType.toUpperCase().replace(/-/g, '_') as NodeType
      : nodeType;
    const schema = this.getNodeSchema(nodeTypeEnum);
    
    if (!schema) {
      return fieldErrors;
    }
    
    try {
      schema.parse(data);
    } catch (error) {
      if (error instanceof z.ZodError) {
        error.errors.forEach(err => {
          const field = err.path.join('.');
          if (!fieldErrors[field]) {
            fieldErrors[field] = [];
          }
          fieldErrors[field].push(err.message);
        });
      }
    }
    
    return fieldErrors;
  }
  
  /**
   * Validate a connection between two handles
   */
  static validateConnection(
    sourceHandle: HandleID,
    targetHandle: HandleID,
    nodes: Map<NodeID, DomainNode>,
  ): ValidationResult {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];
    
    // Extract node IDs from handle IDs (format: nodeId_handleLabel_direction)
    const sourceNodeId = sourceHandle.split('_')[0] as NodeID;
    const targetNodeId = targetHandle.split('_')[0] as NodeID;
    
    const sourceNode = nodes.get(sourceNodeId);
    const targetNode = nodes.get(targetNodeId);
    
    if (!sourceNode) {
      errors.push({
        field: 'source',
        message: `Source node ${sourceNodeId} not found`,
        code: 'SOURCE_NOT_FOUND',
      });
    }
    
    if (!targetNode) {
      errors.push({
        field: 'target',
        message: `Target node ${targetNodeId} not found`,
        code: 'TARGET_NOT_FOUND',
      });
    }
    
    // Additional connection validation logic
    // (e.g., checking if connection types are compatible)
    
    return {
      valid: errors.length === 0,
      errors,
      warnings,
    };
  }
}