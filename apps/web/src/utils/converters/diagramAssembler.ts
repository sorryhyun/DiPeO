import { 
  generateShortId,
  NodeKind,
  DomainNode, 
  DomainArrow, 
  DomainPerson, 
  DomainApiKey, 
  DomainHandle,
  DomainDiagram,
  createHandleId,
  nodeId,
  arrowId,
  personId,
  apiKeyId,
  NodeID,
  ArrowID,
  PersonID,
  ApiKeyID
} from '@/types';
import { generateNodeHandles, getDefaultHandles } from '@/utils/node';
import { getNodeConfig } from '@/config/helpers';
import { buildNode as buildNodeFromInfo, NodeInfo as NodeBuilderInfo } from './nodeBuilders';

// Converter diagram format with arrays and handles
export interface ConverterDiagram {
  id: string;
  name: string;
  description?: string;
  nodes: DomainNode[];
  arrows: DomainArrow[];
  persons: DomainPerson[];
  apiKeys: DomainApiKey[];
  handles: DomainHandle[]; // Store handles separately
}

// Temporary type for building nodes with handles
interface NodeWithHandles extends DomainNode {
  handles: DomainHandle[];
}

// Edge type for graph representation
export interface Edge {
  source: string;
  target: string;
  condition: string | null;
  variable: string | null;
}

// Node information for analysis
export interface NodeAnalysis {
  name: string;
  type: string;
  incoming: Edge[];
  outgoing: Edge[];
  [key: string]: any;
}

// Position calculation result
export interface NodePosition {
  x: number;
  y: number;
}

// Callbacks for format-specific logic
// Use NodeInfo from nodeBuilders
export type NodeInfo = NodeBuilderInfo;

export interface AssemblerCallbacks {
  // Parse edges from format-specific flow structure
  parseFlow: (flowData: any) => Edge[];
  
  // Infer node type from name and context
  inferNodeType: (name: string, context: any) => string;
  
  // Create node data from analysis
  createNodeInfo: (name: string, analysis: NodeAnalysis, context: any) => any;
  
  // Create arrow data from edge
  createArrowData: (edge: Edge, sourceId: string, targetId: string) => any;
  
  // Extract persons from context
  extractPersons: (nodeAnalysis: Record<string, NodeAnalysis>, context: any) => DomainPerson[];
  
  // Extract API keys from persons
  extractApiKeys: (persons: DomainPerson[]) => DomainApiKey[];
  
  // Link persons to nodes
  linkPersonsToNodes?: (nodes: DomainNode[], nodeAnalysis: Record<string, NodeAnalysis>, context: any) => void;
}

export interface AssemblerOptions {
  source: any;
  callbacks: AssemblerCallbacks;
}

/**
 * Common diagram assembler that unifies conversion logic
 */
export class DiagramAssembler {
  private nodeMap: Map<string, NodeID> = new Map();
  private personMap: Map<string, PersonID> = new Map();
  
  /**
   * Assemble a diagram from source data using provided callbacks
   */
  assemble(options: AssemblerOptions): ConverterDiagram {
    const { source, callbacks } = options;
    
    try {
      // Parse flow to build graph structure
      const edges = callbacks.parseFlow(source);
      
      // Analyze nodes from edges (single pass optimization)
      const nodeAnalysis = this.analyzeNodes(edges, source, callbacks);
      
      // Calculate positions using optimized BFS
      const positions = this.calculatePositions(nodeAnalysis);
      
      // Build diagram components
      const persons = callbacks.extractPersons(nodeAnalysis, source);
      const apiKeys = callbacks.extractApiKeys(persons);
      
      // Build nodes with positions
      const { nodes, handles } = this.buildNodes(nodeAnalysis, positions, source, callbacks);
      
      // Build arrows
      const arrows = this.buildArrows(edges);
      
      // Link persons to nodes if callback provided
      if (callbacks.linkPersonsToNodes) {
        callbacks.linkPersonsToNodes(nodes, nodeAnalysis, source);
      }
      
      return {
        id: `diagram-${generateShortId().slice(0, 4)}`,
        name: 'Imported Diagram',
        nodes,
        arrows,
        persons,
        apiKeys,
        handles
      };
    } catch (error) {
      // Return minimal valid diagram on error
      console.error('Diagram assembly error:', error);
      const errorNodeId = nodeId('error-node');
      const errorNodeConfig = getNodeConfig('start' as NodeKind);
      const errorHandles = errorNodeConfig 
        ? generateNodeHandles(errorNodeId, errorNodeConfig, 'start' as NodeKind) 
        : getDefaultHandles(errorNodeId, 'start' as NodeKind);
      
      return {
        id: `diagram-${generateShortId()}`,
        name: 'Import Error',
        nodes: [{
          id: errorNodeId,
          type: 'start' as NodeKind,
          position: { x: 0, y: 0 },
          data: {
            id: errorNodeId,
            label: `Import Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
            type: 'start'
          },
        }],
        arrows: [],
        persons: [],
        apiKeys: [],
        handles: errorHandles
      } as ConverterDiagram;
    }
  }
  
  /**
   * Analyze nodes from edges in a single pass
   */
  private analyzeNodes(
    edges: Edge[], 
    source: any, 
    callbacks: AssemblerCallbacks
  ): Record<string, NodeAnalysis> {
    const nodeAnalysis: Record<string, NodeAnalysis> = {};
    
    // Single pass to collect nodes and connections
    edges.forEach(edge => {
      // Process source node
      if (!nodeAnalysis[edge.source]) {
        nodeAnalysis[edge.source] = {
          name: edge.source,
          type: callbacks.inferNodeType(edge.source, source),
          incoming: [],
          outgoing: []
        };
      }
      
      // Process target node
      if (!nodeAnalysis[edge.target]) {
        nodeAnalysis[edge.target] = {
          name: edge.target,
          type: callbacks.inferNodeType(edge.target, source),
          incoming: [],
          outgoing: []
        };
      }
      
      // Track connections
      nodeAnalysis[edge.source]!.outgoing.push(edge);
      nodeAnalysis[edge.target]!.incoming.push(edge);
    });
    
    // Refine node types based on connections (integrated into first pass where possible)
    Object.entries(nodeAnalysis).forEach(([_name, analysis]) => {
      // Nodes with conditions become condition nodes
      if (analysis.outgoing.some(e => e.condition)) {
        analysis.type = 'condition';
      }
    });
    
    return nodeAnalysis;
  }
  
  /**
   * Calculate node positions using optimized BFS with proper queue
   */
  private calculatePositions(nodeAnalysis: Record<string, NodeAnalysis>): Record<string, NodePosition> {
    const positions: Record<string, NodePosition> = {};
    
    // Find start nodes
    const startNodes = Object.entries(nodeAnalysis)
      .filter(([_name, analysis]) => analysis.type === 'start' || analysis.incoming.length === 0)
      .map(([name]) => name);
    
    if (startNodes.length === 0 && Object.keys(nodeAnalysis).length > 0) {
      const firstNode = Object.keys(nodeAnalysis)[0];
      if (firstNode) startNodes.push(firstNode);
    }
    
    // Optimized BFS with array-based queue
    const visited = new Set<string>();
    const queue: Array<{ node: string; level: number; index: number }> = 
      startNodes.map((node, i) => ({ node, level: 0, index: i }));
    const levelCounts: Record<number, number> = {};
    
    // Use index-based queue to avoid array shifting
    let queueStart = 0;
    
    while (queueStart < queue.length) {
      const current = queue[queueStart++];
      if (!current) continue;
      const { node, level, index } = current;
      if (visited.has(node)) continue;
      
      visited.add(node);
      
      // Position calculation
      positions[node] = {
        x: level * 250,
        y: index * 150
      };
      
      // Queue children
      const analysis = nodeAnalysis[node];
      if (analysis) {
        const children = analysis.outgoing.map(e => e.target);
        children.forEach(child => {
          if (!visited.has(child)) {
            const nextLevel = level + 1;
            levelCounts[nextLevel] = (levelCounts[nextLevel] || 0) + 1;
            queue.push({
              node: child,
              level: nextLevel,
              index: levelCounts[nextLevel] - 1
            });
          }
        });
      }
    }
    
    return positions;
  }
  
  /**
   * Build nodes using callback-provided node info
   */
  private buildNodes(
    nodeAnalysis: Record<string, NodeAnalysis>,
    positions: Record<string, NodePosition>,
    source: any,
    callbacks: AssemblerCallbacks
  ): { nodes: DomainNode[], handles: DomainHandle[] } {
    const nodes: DomainNode[] = [];
    const allHandles: DomainHandle[] = [];
    
    Object.entries(nodeAnalysis).forEach(([name, analysis]) => {
      const nodeInfo = callbacks.createNodeInfo(name, analysis, source);
      const nodeIdValue = nodeId(nodeInfo.id);
      
      // Store mapping
      this.nodeMap.set(name, nodeIdValue);
      
      // Generate handles for the node
      const nodeConfig = getNodeConfig(nodeInfo.type);
      const handles = nodeConfig 
        ? generateNodeHandles(nodeIdValue, nodeConfig, nodeInfo.type) 
        : getDefaultHandles(nodeIdValue, nodeInfo.type);
      
      // Create node (pure domain node)
      const node: DomainNode = {
        id: nodeIdValue,
        type: nodeInfo.type,
        position: positions[name] || { x: 0, y: 0 },
        data: nodeInfo.data
      };
      
      nodes.push(node);
      allHandles.push(...handles);
    });
    
    return { nodes, handles: allHandles };
  }
  
  /**
   * Build arrows from edges
   */
  private buildArrows(edges: Edge[]): DomainArrow[] {
    const arrows: DomainArrow[] = [];
    
    edges.forEach(edge => {
      const sourceId = this.nodeMap.get(edge.source);
      const targetId = this.nodeMap.get(edge.target);
      
      if (!sourceId || !targetId) return;
      
      const id = arrowId(`arrow-${generateShortId().slice(0, 4)}`);
      
      // Determine handle names based on edge properties
      const sourceHandleName = edge.condition ? 
        (edge.condition.includes('not') || edge.condition.startsWith('!') ? 'false' : 'true')
        : 'output';
      const targetHandleName = 'input';
      
      // Create handle IDs
      const sourceHandleId = createHandleId(sourceId, sourceHandleName);
      const targetHandleId = createHandleId(targetId, targetHandleName);
      
      const arrow: DomainArrow = {
        id,
        source: sourceHandleId,
        target: targetHandleId,
        data: {
          label: edge.variable || 'flow',
          contentType: edge.variable ? 'variable_in_object' : 'raw_text',
          branch: edge.condition ? 
            (edge.condition.includes('not') || edge.condition.startsWith('!') ? 'false' : 'true') 
            : undefined
        }
      };
      
      arrows.push(arrow);
    });
    
    return arrows;
  }
  
  /**
   * Get node map for external use
   */
  getNodeMap(): Map<string, NodeID> {
    return this.nodeMap;
  }
  
  /**
   * Get person map for external use
   */
  getPersonMap(): Map<string, PersonID> {
    return this.personMap;
  }
  
  /**
   * Set person map for external use
   */
  setPersonMap(map: Map<string, PersonID>): void {
    this.personMap = map;
  }
  
  /**
   * Build a node using the unified builder system
   * @deprecated Use buildNodeFromInfo directly from nodeBuilders
   */
  static buildNode(info: NodeInfo): DomainNode {
    // This is now deprecated - use buildNodeFromInfo directly
    const nodeWithHandles = buildNodeFromInfo(info) as NodeWithHandles;
    // Extract just the domain node part
    const { handles: _handles, ...domainNode } = nodeWithHandles;
    return domainNode;
  }
  
  /**
   * Build multiple nodes from a record of node infos
   * @deprecated Use buildNodes directly from nodeBuilders
   */
  static buildNodes(nodeInfos: Record<string, NodeInfo>): DomainNode[] {
    return Object.values(nodeInfos).map(info => DiagramAssembler.buildNode(info));
  }
  
}