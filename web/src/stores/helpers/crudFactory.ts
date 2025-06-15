import { Draft } from 'immer';
import { UnifiedStore } from '../unifiedStore.types';
import { recordHistory, updateMap, updateEntity } from './entityHelpers';
import { 
  NodeID, ArrowID, PersonID, ApiKeyID, HandleID,
  DomainNode, DomainArrow, DomainPerson, DomainApiKey, DomainHandle,
  NodeKind
} from '@/types';
import { generateNodeHandles } from '@/utils/node/handle-builder';
import { getNodeConfig } from '@/config';

// Helper function to check if an arrow connects to a specific node
function connectsToNode(arrow: DomainArrow, nodeId: NodeID): boolean {
  const sourceNodeId = arrow.source.split(':')[0];
  const targetNodeId = arrow.target.split(':')[0];
  return sourceNodeId === nodeId || targetNodeId === nodeId;
}

type EntityType = 'nodes' | 'arrows' | 'persons' | 'apiKeys';
type EntityId = NodeID | ArrowID | PersonID | ApiKeyID;
type Entity = DomainNode | DomainArrow | DomainPerson | DomainApiKey;

interface CrudActions<T extends Entity, ID extends EntityId> {
  add: (state: Draft<UnifiedStore>, entity: T) => ID;
  update: (state: Draft<UnifiedStore>, id: ID, updates: Partial<T>) => void;
  delete: (state: Draft<UnifiedStore>, id: ID) => void;
}

// Generic CRUD factory
export function createCrudActions<T extends Entity, ID extends EntityId>(
  entityType: EntityType,
  options?: {
    onAdd?: (state: Draft<UnifiedStore>, entity: T) => void;
    onUpdate?: (state: Draft<UnifiedStore>, id: ID, entity: T) => void;
    onDelete?: (state: Draft<UnifiedStore>, id: ID) => void;
  }
): CrudActions<T, ID> {
  return {
    add: (state, entity) => {
      const map = state[entityType] as Map<ID, T>;
      const newMap = updateMap(map, entity.id as ID, entity);
      state[entityType] = newMap as any;
      state.dataVersion += 1;
      
      options?.onAdd?.(state, entity);
      recordHistory(state);
      
      return entity.id as ID;
    },
    
    update: (state, id, updates) => {
      const map = state[entityType] as Map<ID, T>;
      const newMap = updateEntity(map as Map<string, T>, id as string, updates);
      
      if (newMap) {
        state[entityType] = newMap as any;
        state.dataVersion += 1;
        
        const entity = newMap.get(id as string);
        if (entity) {
          options?.onUpdate?.(state, id, entity as T);
        }
        
        recordHistory(state);
      }
    },
    
    delete: (state, id) => {
      options?.onDelete?.(state, id);
      
      const map = state[entityType] as Map<ID, T>;
      const newMap = updateMap(map, id, null, 'delete');
      state[entityType] = newMap as any;
      state.dataVersion += 1;
      
      // Clear selection if deleted
      if (state.selectedId === id) {
        state.selectedId = null;
        state.selectedType = null;
      }
      
      recordHistory(state);
    }
  };
}

// Node-specific CRUD with handle generation
export const nodeCrud = createCrudActions<DomainNode, NodeID>('nodes', {
  onAdd: (state, node) => {
    // Auto-generate handles
    const nodeConfig = getNodeConfig(node.type as NodeKind);
    if (nodeConfig) {
      const handles = generateNodeHandles(node.id, nodeConfig, node.type);
      handles.forEach((handle: DomainHandle) => {
        const newHandles = updateMap(state.handles, handle.id as HandleID, handle);
        state.handles = newHandles;
      });
    }
  },
  
  onDelete: (state, nodeId) => {
    // Delete associated handles
    const newHandles = new Map(state.handles);
    Array.from(state.handles.values()).forEach(handle => {
      if (handle.nodeId === nodeId) {
        newHandles.delete(handle.id as HandleID);
      }
    });
    state.handles = newHandles;
    
    // Delete connected arrows
    const newArrows = new Map(state.arrows);
    Array.from(state.arrows.values()).forEach(arrow => {
      if (connectsToNode(arrow, nodeId)) {
        newArrows.delete(arrow.id as ArrowID);
      }
    });
    state.arrows = newArrows;
  }
});

// Person-specific CRUD with node updates
export const personCrud = createCrudActions<DomainPerson, PersonID>('persons', {
  onDelete: (state, personId) => {
    // Update nodes that reference this person
    const updatedNodes = new Map(state.nodes);
    updatedNodes.forEach(node => {
      if (
        (node.type === 'person_job' || node.type === 'person_batch_job') &&
        node.data.personId === personId
      ) {
        const updatedNode = { ...node, data: { ...node.data, personId: null } };
        updatedNodes.set(node.id as NodeID, updatedNode);
      }
    });
    state.nodes = updatedNodes;
    state.dataVersion += 1;
  }
});

// Standard CRUD for arrows and API keys
export const arrowCrud = createCrudActions<DomainArrow, ArrowID>('arrows');
export const apiKeyCrud = createCrudActions<DomainApiKey, ApiKeyID>('apiKeys');