import { StoreDomainConverter } from './types';
import type { UnifiedStore } from '@/stores/unifiedStore.types';
import { 
  DomainDiagram, 
  DomainNode, 
  DomainArrow, 
  DomainHandle,
  DomainPerson,
  DomainApiKey,
  NodeID, 
  ArrowID, 
  HandleID,
  PersonID,
  ApiKeyID
} from '@/types';

export class StoreDomainConverterImpl implements StoreDomainConverter {
  /**
   * Convert store state to domain model
   * Maps → Records conversion
   */
  storeToDomain(store: Pick<UnifiedStore, 'nodes' | 'arrows' | 'handles' | 'persons' | 'apiKeys'>): DomainDiagram {
    // Convert Maps to Records
    const nodes: Record<NodeID, DomainNode> = {};
    const arrows: Record<ArrowID, DomainArrow> = {};
    const handles: Record<HandleID, DomainHandle> = {};
    const persons: Record<PersonID, DomainPerson> = {};
    const apiKeys: Record<ApiKeyID, DomainApiKey> = {};

    // Convert nodes
    store.nodes.forEach((node: DomainNode, id: NodeID) => {
      nodes[id] = { ...node };
    });

    // Convert arrows
    store.arrows.forEach((arrow: DomainArrow, id: ArrowID) => {
      arrows[id] = { ...arrow };
    });

    // Convert handles
    store.handles.forEach((handle: DomainHandle, id: HandleID) => {
      handles[id] = { ...handle };
    });

    // Convert persons
    store.persons.forEach((person: DomainPerson, id: PersonID) => {
      persons[id] = { ...person };
    });

    // Convert API keys
    store.apiKeys.forEach((apiKey: DomainApiKey, id: ApiKeyID) => {
      apiKeys[id] = { ...apiKey };
    });

    return {
      nodes,
      arrows,
      handles,
      persons,
      apiKeys
    };
  }

  /**
   * Convert domain model to store state
   * Records → Maps conversion
   */
  domainToStore(diagram: DomainDiagram): Pick<UnifiedStore, 'nodes' | 'arrows' | 'handles' | 'persons' | 'apiKeys'> {
    // Create new Maps from Records
    const nodes = new Map<NodeID, DomainNode>();
    const arrows = new Map<ArrowID, DomainArrow>();
    const handles = new Map<HandleID, DomainHandle>();
    const persons = new Map<PersonID, DomainPerson>();
    const apiKeys = new Map<ApiKeyID, DomainApiKey>();

    // Convert nodes
    if (diagram.nodes) {
      Object.entries(diagram.nodes).forEach(([id, node]) => {
        nodes.set(id as NodeID, node);
      });
    }

    // Convert arrows
    if (diagram.arrows) {
      Object.entries(diagram.arrows).forEach(([id, arrow]) => {
        arrows.set(id as ArrowID, arrow);
      });
    }

    // Convert handles
    if (diagram.handles) {
      Object.entries(diagram.handles).forEach(([id, handle]) => {
        handles.set(id as HandleID, handle);
      });
    }

    // Convert persons
    if (diagram.persons) {
      Object.entries(diagram.persons).forEach(([id, person]) => {
        persons.set(id as PersonID, person);
      });
    }

    // Convert API keys
    if (diagram.apiKeys) {
      Object.entries(diagram.apiKeys).forEach(([id, apiKey]) => {
        apiKeys.set(id as ApiKeyID, apiKey);
      });
    }

    return {
      nodes,
      arrows,
      handles,
      persons,
      apiKeys
    };
  }
}

// Export singleton instance
export const storeDomainConverter = new StoreDomainConverterImpl();