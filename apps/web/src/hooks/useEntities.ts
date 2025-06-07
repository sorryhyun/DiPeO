/**
 * Concrete entity hooks using the generic entity management pattern
 * These hooks provide type-safe CRUD operations for each entity type
 */

import { Node, Arrow, Person, ApiKey } from '@/types';
import { useDiagramStore } from '@/stores';
import { useConsolidatedUIStore } from '@/stores/consolidatedUIStore';
import { createEntityHook, SingleEntityOperations } from './useEntity';
import { nanoid } from 'nanoid';

// Re-export for backward compatibility
export type EntityOperations<T extends { id: string }> = SingleEntityOperations<T>;

/**
 * Hook for managing Node entities
 */
export const useNodeEntities = createEntityHook<Node>({
  getEntities: () => {
    const store = useDiagramStore.getState();
    return store.nodes;
  },
  addEntity: (node) => {
    const store = useDiagramStore.getState();
    // The store's addNode generates ID internally, so we create a proper node object
    if (node.type && node.position) {
      store.addNode(node.type, node.position);
    } else {
      throw new Error('Node type and position are required');
    }
  },
  updateEntity: (id, updates) => {
    const store = useDiagramStore.getState();
    store.updateNode(id, updates.data || updates);
  },
  deleteEntity: (id) => {
    const store = useDiagramStore.getState();
    store.deleteNode(id);
  },
  setEntities: (nodes) => {
    const store = useDiagramStore.getState();
    store.setNodes(nodes);
  },
  getSelectedId: () => useConsolidatedUIStore.getState().selectedNodeId,
  setSelectedId: (id) => useConsolidatedUIStore.getState().setSelectedNodeId(id),
  generateId: () => `node-${nanoid(4)}`,
  validateEntity: (node) => !!node.type && !!node.position,
});

/**
 * Hook for managing Arrow entities
 */
export const useArrowEntities = createEntityHook<Arrow>({
  getEntities: () => {
    const store = useDiagramStore.getState();
    return store.arrows;
  },
  addEntity: (arrow) => {
    const store = useDiagramStore.getState();
    if (arrow.source && arrow.target) {
      store.addArrow(
        arrow.source,
        arrow.target,
        arrow.sourceHandle,
        arrow.targetHandle
      );
    } else {
      throw new Error('Arrow source and target are required');
    }
  },
  updateEntity: (id, updates) => {
    const store = useDiagramStore.getState();
    store.updateArrow(id, updates.data || updates);
  },
  deleteEntity: (id) => {
    const store = useDiagramStore.getState();
    store.deleteArrow(id);
  },
  setEntities: (arrows) => {
    const store = useDiagramStore.getState();
    store.setArrows(arrows);
  },
  getSelectedId: () => useConsolidatedUIStore.getState().selectedArrowId,
  setSelectedId: (id) => useConsolidatedUIStore.getState().setSelectedArrowId(id),
  generateId: () => `arrow-${nanoid(4)}`,
  validateEntity: (arrow) => !!arrow.source && !!arrow.target,
});

/**
 * Hook for managing Person entities
 */
export const usePersonEntities = createEntityHook<Person>({
  getEntities: () => {
    const store = useDiagramStore.getState();
    return store.persons;
  },
  addEntity: (person) => {
    const store = useDiagramStore.getState();
    store.addPerson(person);
  },
  updateEntity: (id, updates) => {
    const store = useDiagramStore.getState();
    store.updatePerson(id, updates);
  },
  deleteEntity: (id) => {
    const store = useDiagramStore.getState();
    store.deletePerson(id);
  },
  setEntities: (persons) => {
    const store = useDiagramStore.getState();
    store.setPersons(persons);
  },
  // Person entities don't have selection state
  generateId: () => `person-${nanoid(4)}`,
});

/**
 * Hook for managing API Key entities
 */
export const useApiKeyEntities = createEntityHook<ApiKey>({
  getEntities: () => {
    const store = useDiagramStore.getState();
    return store.apiKeys;
  },
  addEntity: (apiKey) => {
    const store = useDiagramStore.getState();
    store.addApiKey(apiKey);
  },
  updateEntity: (id, updates) => {
    const store = useDiagramStore.getState();
    store.updateApiKey(id, updates);
  },
  deleteEntity: (id) => {
    const store = useDiagramStore.getState();
    store.deleteApiKey(id);
  },
  setEntities: (apiKeys) => {
    const store = useDiagramStore.getState();
    store.setApiKeys(apiKeys);
  },
  // API keys don't have selection state
  generateId: () => `APIKEY_${nanoid().slice(0, 6).replace(/-/g, '_').toUpperCase()}`,
});