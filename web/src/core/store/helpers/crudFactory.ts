import { Draft } from 'immer';
import { UnifiedStore } from '../unifiedStore.types';
import { recordHistory, updateMap, updateEntity } from './entityHelpers';
import { ApiKeyID, ArrowID, DomainApiKey, DomainArrow, DomainHandle, DomainNode, DomainPerson, HandleID, NodeID, PersonID } from '@/core/types';
import { NodeKind } from '@/features/diagram-editor/types/node-kinds';
import { generateNodeId, generateArrowId, generatePersonId, entityIdGenerators } from '@/core/types/utilities';
import { nodeKindToGraphQLType } from '@/graphql/types';

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

// Standard CRUD for API keys
export const apiKeyCrud = createCrudActions<DomainApiKey, ApiKeyID>('apiKeys');