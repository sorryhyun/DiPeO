import { Node, Edge } from '@xyflow/react';
import { DiagramState } from '@/shared/types';

/**
 * General diagram utility functions
 */

export const validateDiagram = (diagram: DiagramState) => {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Check for orphaned nodes (no connections)
  const connectedNodeIds = new Set<string>();
  diagram.arrows?.forEach(arrow => {
    if (arrow.source) connectedNodeIds.add(arrow.source);
    if (arrow.target) connectedNodeIds.add(arrow.target);
  });

  diagram.nodes?.forEach(node => {
    if (!connectedNodeIds.has(node.id)) {
      warnings.push(`Node "${node.id}" is not connected to any other nodes`);
    }
  });

  // Check for missing start nodes
  const hasStartNode = diagram.nodes?.some(node => node.type === 'start');
  if (!hasStartNode) {
    warnings.push('Diagram should have at least one start node');
  }

  return { isValid: errors.length === 0, errors, warnings };
};

export const findPathsFromNode = (nodeId: string, nodes: Node[], arrows: Edge[]): string[] => {
  const paths: string[] = [];
  const visited = new Set<string>();

  const traverse = (currentId: string, path: string[]) => {
    if (visited.has(currentId)) return; // Prevent infinite loops
    
    visited.add(currentId);
    path.push(currentId);

    const outgoingArrows = arrows.filter(arrow => arrow.source === currentId);
    
    if (outgoingArrows.length === 0) {
      // End of path
      paths.push(path.join(' -> '));
    } else {
      outgoingArrows.forEach(arrow => {
        if (arrow.target) {
          traverse(arrow.target, [...path]);
        }
      });
    }
  };

  traverse(nodeId, []);
  return paths;
};

export const getNodeDependencies = (nodeId: string, arrows: Edge[]) => {
  const dependencies = arrows
    .filter(arrow => arrow.target === nodeId)
    .map(arrow => arrow.source)
    .filter(Boolean);

  return dependencies;
};

export const getDiagramStatistics = (diagram: DiagramState) => {
  return {
    totalNodes: diagram.nodes?.length || 0,
    totalArrows: diagram.arrows?.length || 0,
    totalPersons: diagram.persons?.length || 0,
    nodeTypes: [...new Set(diagram.nodes?.map(n => n.type) || [])],
    hasApiKeys: (diagram.apiKeys?.length || 0) > 0,
  };
};

export const duplicateNode = (node: Node, offset = { x: 50, y: 50 }): Node => {
  return {
    ...node,
    id: `${node.id}_copy_${Date.now()}`,
    position: {
      x: (node.position?.x || 0) + offset.x,
      y: (node.position?.y || 0) + offset.y,
    },
    selected: false,
  };
};