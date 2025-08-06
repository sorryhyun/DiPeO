import { DomainNode } from '@/core/types';
import { NodeType, Vec2 } from '@dipeo/models';
import { generateNodeId } from '@/core/types/utilities';
import { getNodeConfig, generateNodeLabel } from '@/domain/diagram/config/nodes';

// Helper to create a node
export function createNode(type: NodeType, position: Vec2, initialData?: Record<string, unknown>): DomainNode {
  const id = generateNodeId();
  const nodeConfig = getNodeConfig(type);
  const configDefaults = nodeConfig ? { ...nodeConfig.defaults } : {};
  
  const label = String(initialData?.label || configDefaults.label || generateNodeLabel(type, id));
  
  return {
    id,
    type,
    position: {
      x: position?.x ?? 0,
      y: position?.y ?? 0
    },
    data: {
      ...configDefaults,
      ...initialData,
      label,
    }
  };
}
