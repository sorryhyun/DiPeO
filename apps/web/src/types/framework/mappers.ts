import { Node as RFNode, Edge as RFEdge } from 'reactflow';
import { 
  DomainNode, 
  DomainArrow, 
  DomainHandle, 
  DomainDiagram,
  getNodeHandles 
} from '../domain';
import { NodeID, ArrowID, HandleID, handleId } from '../branded';
import { DiPeoNode, DiPeoEdge } from './react-flow';

/**
 * Convert domain node to React Flow node
 */
export function nodeToReactFlow(node: DomainNode, handles: DomainHandle[]): DiPeoNode {
  // Separate handles by direction
  const inputs = handles
    .filter(h => h.direction === 'input')
    .reduce((acc, h) => ({ ...acc, [h.name]: h }), {});
  
  const outputs = handles
    .filter(h => h.direction === 'output')
    .reduce((acc, h) => ({ ...acc, [h.name]: h }), {});

  return {
    id: node.id,
    type: node.type,
    position: node.position,
    data: {
      label: (node.data as any).label,
      properties: node.data,
      inputs,
      outputs
    }
  };
}

/**
 * Convert domain arrow to React Flow edge
 */
export function arrowToReactFlow(arrow: DomainArrow): DiPeoEdge {
  const [sourceNode, sourceHandle] = arrow.source.split(':');
  const [targetNode, targetHandle] = arrow.target.split(':');
  
  return {
    id: arrow.id,
    source: sourceNode,
    sourceHandle,
    target: targetNode,
    targetHandle,
    type: 'smoothstep',
    data: arrow.data
  };
}

/**
 * Convert React Flow node to domain node
 */
export function reactFlowToNode(rfNode: RFNode): DomainNode {
  const { inputs, outputs, properties, ...rest } = (rfNode.data || {}) as any;
  
  return {
    id: rfNode.id as NodeID,
    type: rfNode.type as any,
    position: rfNode.position,
    data: properties || rest
  };
}

/**
 * Convert React Flow edge to domain arrow
 */
export function reactFlowToArrow(rfEdge: RFEdge): DomainArrow {
  const sourceHandle = handleId(
    rfEdge.source as NodeID,
    rfEdge.sourceHandle || 'default'
  );
  const targetHandle = handleId(
    rfEdge.target as NodeID,
    rfEdge.targetHandle || 'default'
  );
  
  return {
    id: rfEdge.id as ArrowID,
    source: sourceHandle,
    target: targetHandle,
    data: rfEdge.data
  };
}

/**
 * Convert entire domain diagram to React Flow format
 */
export function domainToReactFlow(diagram: DomainDiagram): {
  nodes: DiPeoNode[];
  edges: DiPeoEdge[];
} {
  const nodes = Object.values(diagram.nodes).map(node => {
    const handles = getNodeHandles(diagram, node.id);
    return nodeToReactFlow(node, handles);
  });
  
  const edges = Object.values(diagram.arrows).map(arrowToReactFlow);
  
  return { nodes, edges };
}

/**
 * Convert React Flow elements back to domain diagram
 */
export function reactFlowToDomain(
  nodes: RFNode[],
  edges: RFEdge[],
  existingDiagram?: Partial<DomainDiagram>
): Partial<DomainDiagram> {
  const domainNodes: Record<NodeID, DomainNode> = {};
  const domainArrows: Record<ArrowID, DomainArrow> = {};
  
  // Convert nodes
  for (const node of nodes) {
    domainNodes[node.id as NodeID] = reactFlowToNode(node);
  }
  
  // Convert edges
  for (const edge of edges) {
    domainArrows[edge.id as ArrowID] = reactFlowToArrow(edge);
  }
  
  return {
    nodes: domainNodes,
    arrows: domainArrows,
    // Preserve existing handles and persons
    handles: existingDiagram?.handles,
    persons: existingDiagram?.persons
  };
}