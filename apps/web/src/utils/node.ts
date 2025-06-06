import { Node } from '@xyflow/react';
import type { Node as DiagramNode, DiagramNodeData, NodeType } from '@/types';
import { getNodeConfig, getNodeDefaults, validateNodeData as validateNodeConfig } from '@/config';

// NODE CREATION & DEFAULTS


export const createNodeId = (): string => {
  return `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

export function createDefaultNodeData(type: string, nodeId: string): DiagramNodeData {
  // Convert string type to NodeType
  const nodeType = type as NodeType;
  const config = getNodeConfig(nodeType);
  
  if (!config) {
    // Fallback for unknown types
    return {
      id: nodeId,
      type: 'start' as const,
      label: 'Unknown'
    };
  }
  
  // Get default data from unified configuration
  const defaults = getNodeDefaults(nodeType);
  
  // Base properties common to all nodes
  const baseData: Record<string, unknown> = {
    id: nodeId,
    type,
    label: config.label,
    ...defaults // Spread the default data from config
  };
  
  // Add any additional node-specific properties that might not be in config defaults
  // (for backward compatibility or special cases)
  switch (type) {
    case 'person_job':
      // Ensure backward compatibility fields
      baseData.detectedVariables = baseData.detectedVariables || [];
      break;
      
    case 'endpoint':
      // Map 'action' to legacy fields for backward compatibility
      if (baseData.action === 'save') {
        baseData.saveToFile = true;
        baseData.filePath = baseData.filename || '';
        baseData.fileFormat = 'json';
      }
      break;
  }
  
  return baseData as DiagramNodeData;
}


// NODE HELPERS

export const getNodeDisplayName = (node: Node): string => {
  const data = node.data as { label?: string; name?: string };
  return data?.label || data?.name || node.type || 'Unnamed Node';
};

export function createHandleId(nodeId: string, type: string, name?: string): string {
  return name ? `${nodeId}-${type}-${name}` : `${nodeId}-${type}`;
}

export const getNodeData = (node: DiagramNode, defaults: Record<string, any> = {}): Record<string, any> => {
  return { ...defaults, ...node.data };
};


// NODE VALIDATION

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

export const validateNode = (node: Node): ValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Basic validation
  if (!node.id) {
    errors.push('Node must have an ID');
  }

  if (!node.type) {
    errors.push('Node must have a type');
  }

  if (!node.data) {
    errors.push('Node must have data');
  }

  // Position validation
  if (!node.position) {
    warnings.push('Node position not set');
  }

  // Type-specific validation could be added here
  switch (node.type) {
    case 'person':
      if (!node.data?.name) {
        warnings.push('Person node should have a name');
      }
      break;
    case 'job':
      if (!node.data?.prompt) {
        warnings.push('Job node should have a prompt');
      }
      break;
    default:
      break;
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
  };
};

export const validateNodeData = (nodeType: string, data: unknown): ValidationResult => {
  const warnings: string[] = [];

  if (!data) {
    return { isValid: false, errors: ['Node data is required'], warnings };
  }

  // Use the new configuration-based validation
  const validationResult = validateNodeConfig(nodeType as NodeType, data as Record<string, any>);

  return {
    isValid: validationResult.valid,
    errors: validationResult.errors,
    warnings,
  };
};