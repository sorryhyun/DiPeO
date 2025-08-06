import { Draft } from 'immer';
import { UnifiedStore, Snapshot } from '../types';

export const MAX_HISTORY_SIZE = 50;

export function createFullSnapshot(state: Partial<UnifiedStore>): Snapshot {
  return {
    nodes: new Map(state.nodes || new Map()),
    arrows: new Map(state.arrows || new Map()),
    persons: new Map(state.persons || new Map()),
    handles: new Map(state.handles || new Map()),
    timestamp: Date.now(),
  };
}

export function recordHistory(state: Draft<UnifiedStore>) {
  if (!state.history.currentTransaction) {
    state.history.undoStack.push(createFullSnapshot(state));
    state.history.redoStack = [];
    if (state.history.undoStack.length > MAX_HISTORY_SIZE) {
      state.history.undoStack.shift();
    }
  }
}

export function updateMap<K, V>(
  map: Map<K, V>,
  key: K,
  value: V | null,
  operation: 'set' | 'delete' = 'set'
): Map<K, V> {
  const newMap = new Map(map);
  if (operation === 'delete' || value === null) {
    newMap.delete(key);
  } else {
    newMap.set(key, value);
  }
  return newMap;
}

export function updateEntity<T extends { id: string; data?: Record<string, unknown> | null }>(
  map: Map<string, T>,
  id: string,
  updates: Partial<T>
): Map<string, T> | null {
  const entity = map.get(id);
  if (!entity) return null;
  
  const updatedEntity = { ...entity };
  if ('data' in updates && 'data' in entity && entity.data && updates.data && updates.data !== null) {
    updatedEntity.data = { ...entity.data, ...updates.data };
    const { data: _data, ...otherUpdates } = updates;
    Object.assign(updatedEntity, otherUpdates);
  } else {
    Object.assign(updatedEntity, updates);
  }
  
  return updateMap(map, id, updatedEntity);
}