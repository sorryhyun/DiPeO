import { UnifiedStore } from '../types';
import { DomainNode, DomainArrow, DomainPerson } from '@/infrastructure/types';

// Memoization cache for computed arrays
interface ArrayCache {
  nodes: { version: number; array: DomainNode[] };
  arrows: { version: number; array: DomainArrow[] };
  persons: { version: number; array: DomainPerson[] };
}

// Use a simple cache object instead of WeakMap to avoid initialization issues
const cache: ArrayCache = {
  nodes: { version: -1, array: [] },
  arrows: { version: -1, array: [] },
  persons: { version: -1, array: [] },
};

// Memoized getter for nodes array
export const getNodesArray = (store: UnifiedStore): DomainNode[] => {
  // Check if store and nodes Map exist before trying to use them
  if (!store || !store.nodes || !(store.nodes instanceof Map)) {
    return [];
  }
  const version = store.dataVersion ?? 0;
  if (cache.nodes.version !== version) {
    cache.nodes.array = Array.from(store.nodes.values());
    cache.nodes.version = version;
  }
  return cache.nodes.array;
};

// Memoized getter for arrows array
export const getArrowsArray = (store: UnifiedStore): DomainArrow[] => {
  // Check if store and arrows Map exist before trying to use them
  if (!store || !store.arrows || !(store.arrows instanceof Map)) {
    return [];
  }
  const version = store.dataVersion ?? 0;
  if (cache.arrows.version !== version) {
    cache.arrows.array = Array.from(store.arrows.values());
    cache.arrows.version = version;
  }
  return cache.arrows.array;
};

// Memoized getter for persons array
export const getPersonsArray = (store: UnifiedStore): DomainPerson[] => {
  // Check if store and persons Map exist before trying to use them
  if (!store || !store.persons || !(store.persons instanceof Map)) {
    return [];
  }
  const version = store.dataVersion ?? 0;
  if (cache.persons.version !== version) {
    cache.persons.array = Array.from(store.persons.values());
    cache.persons.version = version;
  }
  return cache.persons.array;
};

// Computed getter creators for zustand store
export const createComputedGetters = (get: () => UnifiedStore) => ({
  get nodesArray() {
    try {
      const state = get();
      return getNodesArray(state);
    } catch (e) {
      console.error('[computedGetters] Error getting nodesArray:', e);
      return [];
    }
  },
  get arrowsArray() {
    try {
      const state = get();
      return getArrowsArray(state);
    } catch (e) {
      console.error('[computedGetters] Error getting arrowsArray:', e);
      return [];
    }
  },
  get personsArray() {
    try {
      const state = get();
      return getPersonsArray(state);
    } catch (e) {
      console.error('[computedGetters] Error getting personsArray:', e);
      return [];
    }
  },
});