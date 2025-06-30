import { Draft } from 'immer';
import { UnifiedStore } from '../unifiedStore.types';
import { recordHistory, updateMap, updateEntity } from './entityHelpers';
import { DomainArrow, DomainNode, DomainPerson } from '@/core/types';
import {ArrowID, NodeID, PersonID} from '@dipeo/domain-models';

type EntityType = 'nodes' | 'arrows' | 'persons';
type EntityId = NodeID | ArrowID | PersonID;
type Entity = DomainNode | DomainArrow | DomainPerson;

interface CrudActions<T extends Entity, ID extends EntityId> {
  add: (state: Draft<UnifiedStore>, entity: T) => ID;
  update: (state: Draft<UnifiedStore>, id: ID, updates: Partial<T>) => void;
  delete: (state: Draft<UnifiedStore>, id: ID) => void;
}

// Type-safe entity map getter
function getEntityMap<T extends Entity, ID extends EntityId>(
  state: Draft<UnifiedStore>,
  entityType: EntityType
): Map<ID, T> {
  return state[entityType] as Map<ID, T>;
}

// Type-safe entity map setter
function setEntityMap<T extends Entity, ID extends EntityId>(
  state: Draft<UnifiedStore>,
  entityType: EntityType,
  map: Map<ID, T>
): void {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (state as any)[entityType] = map;
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
      const map = getEntityMap<T, ID>(state, entityType);
      const newMap = updateMap(map, entity.id as ID, entity);
      setEntityMap(state, entityType, newMap);
      state.dataVersion += 1;
      
      options?.onAdd?.(state, entity);
      recordHistory(state);
      
      return entity.id as ID;
    },
    
    update: (state, id, updates) => {
      const map = getEntityMap<T, ID>(state, entityType);
      const newMap = updateEntity(map as Map<string, T>, id as string, updates);
      
      if (newMap) {
        setEntityMap(state, entityType, newMap as Map<ID, T>);
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
      
      const map = getEntityMap<T, ID>(state, entityType);
      const newMap = updateMap(map, id, null, 'delete');
      setEntityMap(state, entityType, newMap);
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

