import { Draft } from 'immer';
import { UnifiedStore, Snapshot } from '../unifiedStore.types';

export const MAX_HISTORY_SIZE = 50;

// Helper to create a full snapshot
export function createFullSnapshot(state: Partial<UnifiedStore>): Snapshot {
  return {
    nodes: new Map(state.nodes || new Map()),
    arrows: new Map(state.arrows || new Map()),
    persons: new Map(state.persons || new Map()),
    handles: new Map(state.handles || new Map()),
    timestamp: Date.now(),
  };
}

// Helper to record history
export function recordHistory(state: Draft<UnifiedStore>) {
  if (!state.history.currentTransaction) {
    state.history.undoStack.push(createFullSnapshot(state));
    state.history.redoStack = [];
    
    // Limit history size
    if (state.history.undoStack.length > MAX_HISTORY_SIZE) {
      state.history.undoStack.shift();
    }
  }
}

// Generic Map update helper
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

// Generic entity update helper
export function updateEntity<T extends { id: string; data?: Record<string, unknown> | null }>(
  map: Map<string, T>,
  id: string,
  updates: Partial<T>
): Map<string, T> | null {
  const entity = map.get(id);
  if (!entity) return null;
  
  const updatedEntity = { ...entity };
  
  // Handle nested data updates
  if ('data' in updates && 'data' in entity && entity.data && updates.data && updates.data !== null) {
    updatedEntity.data = { ...entity.data, ...updates.data };
    const { data: _data, ...otherUpdates } = updates;
    Object.assign(updatedEntity, otherUpdates);
  } else {
    Object.assign(updatedEntity, updates);
  }
  
  return updateMap(map, id, updatedEntity);
}