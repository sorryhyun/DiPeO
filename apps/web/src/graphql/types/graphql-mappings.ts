import type {
  DomainNode as Node,
  DomainArrow as Arrow,
  DomainHandle as Handle,
  DomainPerson as Person,
  DomainApiKey as ApiKey,
  DomainDiagramType,
  Vec2Input
} from '@/__generated__/graphql';
import { 
  NodeType, HandleDirection, DataType, Vec2,
  NodeID, ArrowID, HandleID, PersonID, ApiKeyID, DiagramID,
  DomainNode as DomainNodeModel,
  DomainArrow as DomainArrowModel,
  DomainHandle as DomainHandleModel,
  DomainPerson as DomainPersonModel,
  DomainApiKey as DomainApiKeyModel,
  DomainDiagram as DomainDiagramModel
} from '@dipeo/domain-models';

// Type aliases for semantic clarity - these help distinguish between
// different contexts where the same types are used

// Domain types represent the server's data model
export type DomainNode = Node;
export type DomainArrow = Arrow;
export type DomainHandle = Handle;
export type DomainPerson = Person;
export type DomainApiKey = ApiKey;
export type DomainDiagram = DomainDiagramType;

export type ReactDiagram = DomainDiagramType;

// Store format uses Maps for efficient lookups
export interface StoreDiagram {
  nodes: Map<NodeID, Node>;
  handles: Map<HandleID, Handle>;
  arrows: Map<ArrowID, Arrow>;
  persons: Map<PersonID, Person>;
  apiKeys: Map<ApiKeyID, ApiKey>;
  metadata?: {
    id?: DiagramID;
    name?: string;
    description?: string;
    version: string;
    created: string;
    modified: string;
    author?: string;
    tags?: string[];
  };
}

// Convert from Domain/React format (arrays) to Store format (Maps)
export function diagramToStoreMaps(diagram: Partial<DomainDiagramType>): {
  nodes: Map<NodeID, Node>;
  handles: Map<HandleID, Handle>;
  arrows: Map<ArrowID, Arrow>;
  persons: Map<PersonID, Person>;
  apiKeys: Map<ApiKeyID, ApiKey>;
} {
  const nodes = new Map<NodeID, Node>();
  const handles = new Map<HandleID, Handle>();
  const arrows = new Map<ArrowID, Arrow>();
  const persons = new Map<PersonID, Person>();
  const apiKeys = new Map<ApiKeyID, ApiKey>();

  // Convert arrays to maps with branded IDs as keys
  diagram.nodes?.forEach((node: Node) => {
    nodes.set(node.id as NodeID, node);
  });

  diagram.handles?.forEach((handle: Handle) => {
    handles.set(handle.id as HandleID, handle);
  });

  diagram.arrows?.forEach((arrow: Arrow) => {
    arrows.set(arrow.id as ArrowID, arrow);
  });

  diagram.persons?.forEach((person: Person) => {
    persons.set(person.id as PersonID, person);
  });

  diagram.apiKeys?.forEach((apiKey: ApiKey) => {
    apiKeys.set(apiKey.id as ApiKeyID, apiKey);
  });

  return { nodes, handles, arrows, persons, apiKeys };
}

// Convert from Store format (Maps) back to Domain/React format (arrays)
export function storeMapsToArrays(store: {
  nodes: Map<NodeID, Node>;
  handles: Map<HandleID, Handle>;
  arrows: Map<ArrowID, Arrow>;
  persons: Map<PersonID, Person>;
  apiKeys: Map<ApiKeyID, ApiKey>;
}): Partial<DomainDiagramType> {
  return {
    nodes: Array.from(store.nodes.values()),
    handles: Array.from(store.handles.values()),
    arrows: Array.from(store.arrows.values()),
    persons: Array.from(store.persons.values()),
    apiKeys: Array.from(store.apiKeys.values())
  };
}

// Convert from React format to Domain/GraphQL format for server communication
export function reactDiagramToDomain(diagram: ReactDiagram): Partial<DomainDiagramType> {
  return {
    nodes: diagram.nodes || [],
    handles: diagram.handles || [],
    arrows: diagram.arrows || [],
    persons: diagram.persons || [],
    apiKeys: diagram.apiKeys || [],
    metadata: diagram.metadata ? {
      __typename: 'DiagramMetadataType' as const,
      id: diagram.metadata.id || null,
      name: diagram.metadata.name || null,
      description: diagram.metadata.description || null,
      version: diagram.metadata.version,
      created: diagram.metadata.created,
      modified: diagram.metadata.modified,
      author: diagram.metadata.author || null,
      tags: diagram.metadata.tags || null
    } : undefined
  };
}

// Convert from Domain/GraphQL format to React format for component usage
export function domainToReactDiagram(diagram: Partial<DomainDiagramType>): ReactDiagram {
  return diagram as ReactDiagram;
}

// Node type mappings
export function nodeKindToGraphQLType(kind: string): NodeType {
  const mapping: Record<string, NodeType> = {
    'start': NodeType.START,
    'condition': NodeType.CONDITION,
    'person_job': NodeType.PERSON_JOB,
    'person_batch_job': NodeType.PERSON_BATCH_JOB,
    'endpoint': NodeType.ENDPOINT,
    'db': NodeType.DB,
    'job': NodeType.JOB,
    'user_response': NodeType.USER_RESPONSE,
    'notion': NodeType.NOTION
  };
  return mapping[kind] || NodeType.START;
}

export function graphQLTypeToNodeKind(type: NodeType): string {
  const mapping: Record<NodeType, string> = {
    [NodeType.START]: 'start',
    [NodeType.CONDITION]: 'condition',
    [NodeType.PERSON_JOB]: 'person_job',
    [NodeType.PERSON_BATCH_JOB]: 'person_batch_job',
    [NodeType.ENDPOINT]: 'endpoint',
    [NodeType.DB]: 'db',
    [NodeType.JOB]: 'job',
    [NodeType.USER_RESPONSE]: 'user_response',
    [NodeType.NOTION]: 'notion'
  };
  return mapping[type];
}

// Vec2 conversion helpers
export function vec2ToInput(vec: Vec2): Vec2Input {
  return { x: vec.x, y: vec.y };
}

export function vec2FromGraphQL(vec: { x: number; y: number }): Vec2 {
  return { x: vec.x, y: vec.y };
}

// Type guards (matching old domain type guards)
export function isDomainNode(obj: unknown): obj is Node {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'id' in obj &&
    'type' in obj &&
    'position' in obj &&
    'data' in obj
  );
}

export function isReactDiagram(obj: unknown): obj is ReactDiagram {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'nodes' in obj &&
    'handles' in obj &&
    'arrows' in obj &&
    'persons' in obj &&
    'apiKeys' in obj
  );
}

// Utility functions matching old domain helpers
export function createEmptyDiagram(): ReactDiagram {
  return {
    nodes: [],
    handles: [],
    arrows: [],
    persons: [],
    apiKeys: [],
    nodeCount: 0,
    arrowCount: 0,
    personCount: 0,
    metadata: {
      version: '2.0.0',
      created: new Date().toISOString(),
      modified: new Date().toISOString()
    }
  };
}

export function getNodeHandles(
  diagram: ReactDiagram,
  nodeId: NodeID
): Handle[] {
  return (diagram.handles || []).filter(
    (handle: Handle) => handle.nodeId === nodeId
  );
}

export function getHandleById(diagram: ReactDiagram, handleId: HandleID): Handle | undefined {
  return (diagram.handles || []).find((handle: Handle) => handle.id === handleId);
}

export function parseHandleId(handleId: HandleID): { nodeId: NodeID; handleName: string } {
  const [nodeId, ...handleNameParts] = handleId.split(':');
  return {
    nodeId: nodeId as NodeID,
    handleName: handleNameParts.join(':')
  };
}

// Check if two handles are compatible for connection
export function areHandlesCompatible(source: Handle, target: Handle): boolean {
  // Basic compatibility: output can connect to input
  if (source.direction !== HandleDirection.OUTPUT || target.direction !== HandleDirection.INPUT) {
    return false;
  }
  
  // Type compatibility
  if (source.dataType === DataType.ANY || target.dataType === DataType.ANY) {
    return true;
  }
  
  return source.dataType === target.dataType;
}

// Arrow data interface
export interface ArrowData {
  label?: string;
  style?: React.CSSProperties;
  controlPointOffsetX?: number;
  controlPointOffsetY?: number;
  loopRadius?: number;
  branch?: 'true' | 'false';
  contentType?: 'raw_text' | 'variable_in_object' | 'conversation_state' | 'empty' | 'generic';
  [key: string]: unknown;
}