import { recordHistory, updateMap, updateEntity } from './entityHelpers';
import { DomainArrow, DomainNode, DomainPerson } from '@/infrastructure/types';
import {ArrowID, NodeID, PersonID} from '@dipeo/models';
import type { UnifiedStore } from '../types';
import { Draft } from 'immer';

type EntityType = 'nodes' | 'arrows' | 'persons';
type EntityId = NodeID | ArrowID | PersonID;
type Entity = DomainNode | DomainArrow | DomainPerson;

interface CrudActions<T extends Entity, ID extends EntityId> {
  add: (state: UnifiedStore, entity: T) => ID;
  update: (state: UnifiedStore, id: ID, updates: Partial<T>) => void;
  delete: (state: UnifiedStore, id: ID) => void;
}

function getEntityMap<T extends Entity, ID extends EntityId>(
  state: UnifiedStore,
  entityType: EntityType
): Map<ID, T> {
  return state[entityType] as Map<ID, T>;
}

function setEntityMap<T extends Entity, ID extends EntityId>(
  state: UnifiedStore,
  entityType: EntityType,
  map: Map<ID, T>
): void {
  (state[entityType] as Map<ID, T>) = map;
}

export function createCrudActions<T extends Entity, ID extends EntityId>(
  entityType: EntityType,
  options?: {
    onAdd?: (state: UnifiedStore, entity: T) => void;
    onUpdate?: (state: UnifiedStore, id: ID, entity: T) => void;
    onDelete?: (state: UnifiedStore, id: ID) => void;
  }
): CrudActions<T, ID> {
  return {
    add: (state, entity) => {
      const map = getEntityMap<T, ID>(state, entityType);
      const newMap = updateMap(map, entity.id as ID, entity);
      setEntityMap(state, entityType, newMap);
      state.dataVersion += 1;

      options?.onAdd?.(state, entity);
      // Use Draft type for immer state
      recordHistory(state as Draft<UnifiedStore>);

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

        // Use Draft type for immer state
        recordHistory(state as Draft<UnifiedStore>);
      }
    },

    delete: (state, id) => {
      options?.onDelete?.(state, id);

      const map = getEntityMap<T, ID>(state, entityType);
      const newMap = updateMap(map, id, null, 'delete');
      setEntityMap(state, entityType, newMap);
      state.dataVersion += 1;

      if (state.selectedId === id) {
        state.selectedId = null;
        state.selectedType = null;
      }

      // Use Draft type for immer state
      recordHistory(state as Draft<UnifiedStore>);
    }
  };
}
