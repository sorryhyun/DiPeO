import { Node, DiagramNodeData, getNodeConfig, getNodeDefaults } from '@/common/types';

// Factory function to create default node data based on node config
export function createDefaultNodeData(type: string, nodeId: string): DiagramNodeData {
  // Convert string type to Node type
  const nodeType = type as Node['type'];
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