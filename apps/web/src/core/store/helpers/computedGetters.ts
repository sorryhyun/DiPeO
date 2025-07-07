import { UnifiedStore } from '../unifiedStore.types';
import { DomainNode, DomainArrow, DomainPerson } from '@/core/types';

// Memoization cache for computed arrays
interface ArrayCache {
  nodes: { version: number; array: DomainNode[] };
  arrows: { version: number; array: DomainArrow[] };
  persons: { version: number; array: DomainPerson[] };
}

// Create a weakmap to store cache per store instance
const cacheMap = new WeakMap<UnifiedStore, ArrayCache>();

// Helper to get or create cache for a store instance
const getCache = (store: UnifiedStore): ArrayCache => {
  let cache = cacheMap.get(store);
  if (!cache) {
    cache = {
      nodes: { version: -1, array: [] },
      arrows: { version: -1, array: [] },
      persons: { version: -1, array: [] },
    };
    cacheMap.set(store, cache);
  }
  return cache;
};

// Memoized getter for nodes array
export const getNodesArray = (store: UnifiedStore): DomainNode[] => {
  const cache = getCache(store);
  // Check if nodes Map exists before trying to use it
  if (!store.nodes) {
    return [];
  }
  if (cache.nodes.version !== store.dataVersion) {
    cache.nodes.array = Array.from(store.nodes.values());
    cache.nodes.version = store.dataVersion;
  }
  return cache.nodes.array;
};

// Memoized getter for arrows array
export const getArrowsArray = (store: UnifiedStore): DomainArrow[] => {
  const cache = getCache(store);
  // Check if arrows Map exists before trying to use it
  if (!store.arrows) {
    return [];
  }
  if (cache.arrows.version !== store.dataVersion) {
    cache.arrows.array = Array.from(store.arrows.values());
    cache.arrows.version = store.dataVersion;
  }
  return cache.arrows.array;
};

// Memoized getter for persons array
export const getPersonsArray = (store: UnifiedStore): DomainPerson[] => {
  const cache = getCache(store);
  // Check if persons Map exists before trying to use it
  if (!store.persons) {
    return [];
  }
  if (cache.persons.version !== store.dataVersion) {
    cache.persons.array = Array.from(store.persons.values());
    cache.persons.version = store.dataVersion;
  }
  return cache.persons.array;
};

// Computed getter creators for zustand store
export const createComputedGetters = () => ({
  get nodesArray() {
    return getNodesArray(this as unknown as UnifiedStore);
  },
  get arrowsArray() {
    return getArrowsArray(this as unknown as UnifiedStore);
  },
  get personsArray() {
    return getPersonsArray(this as unknown as UnifiedStore);
  },
});