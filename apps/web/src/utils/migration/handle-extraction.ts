import { Node, Arrow, Person } from '@/types';
import { NodeV2, HandleV2, ArrowV2, PersonV2, DiagramV2 } from '@/types/diagram';
import { nodeId, handleId, arrowId, personId, HandleID, NodeID } from '@/types/branded';
import { normalizeDirection } from '@/types/direction';

// V1 diagram structure (current)
interface DiagramV1 {
  nodes: Record<string, Node>;
  arrows: Record<string, Arrow>;
  persons: Record<string, Person>;
  apiKeys: Record<string, any>;
}

/**
 * Extract handles from nodes into a separate collection
 * This is the main migration function from V1 to V2
 */
export function extractHandles(diagram: DiagramV1): DiagramV2 {
  const handles: Record<HandleID, HandleV2> = {};
  const nodeMap: Record<NodeID, NodeV2> = {};
  
  // Process nodes and extract handles
  for (const [id, node] of Object.entries(diagram.nodes)) {
    const nodeIdBranded = nodeId(id);
    
    // Extract handles from node
    if (node.handles && Array.isArray(node.handles)) {
      for (const handle of node.handles) {
        const handleIdBranded = handleId(nodeIdBranded, handle.id);
        
        handles[handleIdBranded] = {
          id: handleIdBranded,
          nodeId: nodeIdBranded,
          direction: normalizeDirection(handle.kind),
          name: handle.id,
          dataType: handle.dataType,
          position: handle.position || 'right',
          offset: handle.offset,
          label: handle.label,
          color: handle.color,
          required: handle.required,
          multiple: handle.multiple
        };
      }
    }
    
    // Create node without handles
    const { handles: _, ...nodeWithoutHandles } = node;
    nodeMap[nodeIdBranded] = {
      ...nodeWithoutHandles,
      id: nodeIdBranded
    } as NodeV2;
  }
  
  // Convert arrows to use handle IDs directly
  const arrowMap: Record<string, ArrowV2> = {};
  for (const [id, arrow] of Object.entries(diagram.arrows)) {
    arrowMap[arrowId(id)] = {
      id: arrowId(id),
      source: arrow.source as HandleID, // Already in handle ID format
      target: arrow.target as HandleID, // Already in handle ID format
      data: arrow.data
    };
  }
  
  // Convert persons
  const personMap: Record<string, PersonV2> = {};
  for (const [id, person] of Object.entries(diagram.persons)) {
    personMap[personId(id)] = {
      ...person,
      id: personId(id)
    } as PersonV2;
  }
  
  return {
    nodes: nodeMap,
    handles,
    arrows: arrowMap,
    persons: personMap,
    apiKeys: diagram.apiKeys || {}
  };
}

/**
 * Convert V2 diagram back to V1 format for backward compatibility
 */
export function injectHandles(diagram: DiagramV2): DiagramV1 {
  const nodes: Record<string, Node> = {};
  
  // Process nodes and inject handles back
  for (const [nodeIdStr, node] of Object.entries(diagram.nodes)) {
    const nodeHandles = Object.values(diagram.handles)
      .filter(h => h.nodeId === nodeIdStr)
      .map(h => ({
        id: h.name,
        kind: h.direction === 'output' ? 'source' : 'target',
        dataType: h.dataType,
        position: h.position,
        offset: h.offset,
        label: h.label,
        color: h.color,
        required: h.required,
        multiple: h.multiple
      }));
    
    nodes[nodeIdStr] = {
      ...node,
      id: nodeIdStr,
      handles: nodeHandles
    } as Node;
  }
  
  // Convert arrows back to string IDs
  const arrows: Record<string, Arrow> = {};
  for (const [id, arrow] of Object.entries(diagram.arrows)) {
    arrows[id] = {
      ...arrow,
      id,
      source: arrow.source as string,
      target: arrow.target as string
    } as Arrow;
  }
  
  // Convert persons back to string IDs
  const persons: Record<string, Person> = {};
  for (const [id, person] of Object.entries(diagram.persons)) {
    persons[id] = {
      ...person,
      id
    } as Person;
  }
  
  return {
    nodes,
    arrows,
    persons,
    apiKeys: diagram.apiKeys
  };
}

/**
 * Helper to get handles for a node in V1 format
 */
export function getNodeHandlesV1(diagram: DiagramV1, nodeId: string): any[] {
  const node = diagram.nodes[nodeId];
  return node?.handles || [];
}

/**
 * Check if a diagram is in V2 format
 */
export function isDiagramV2(diagram: any): diagram is DiagramV2 {
  return diagram && 
    typeof diagram === 'object' && 
    'handles' in diagram &&
    typeof diagram.handles === 'object';
}

/**
 * Migrate a single node from V1 to V2
 */
export function migrateNode(node: Node): { node: NodeV2; handles: HandleV2[] } {
  const nodeIdBranded = nodeId(node.id);
  const handles: HandleV2[] = [];
  
  if (node.handles && Array.isArray(node.handles)) {
    for (const handle of node.handles) {
      const handleIdBranded = handleId(nodeIdBranded, handle.id);
      
      handles.push({
        id: handleIdBranded,
        nodeId: nodeIdBranded,
        direction: normalizeDirection(handle.kind),
        name: handle.id,
        dataType: handle.dataType,
        position: handle.position || 'right',
        offset: handle.offset,
        label: handle.label,
        color: handle.color,
        required: handle.required,
        multiple: handle.multiple
      });
    }
  }
  
  const { handles: _, ...nodeWithoutHandles } = node;
  
  return {
    node: {
      ...nodeWithoutHandles,
      id: nodeIdBranded
    } as NodeV2,
    handles
  };
}