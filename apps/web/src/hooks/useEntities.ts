/**
 * Concrete entity hooks using the generic entity management pattern
 * These hooks provide type-safe CRUD operations for each entity type
 */

import { useMemo } from 'react';
import { Node, Arrow, Person, ApiKey } from '@/types';
import { useDiagramStore } from '@/stores';
import { useConsolidatedUIStore } from '@/stores/consolidatedUIStore';
import { nanoid } from 'nanoid';

// Type definitions for entity operations
export interface EntityOperations<T> {
  // Read operations
  getAll: () => T[];
  getById: (id: string) => T | undefined;
  find: (predicate: (entity: T) => boolean) => T | undefined;
  filter: (predicate: (entity: T) => boolean) => T[];
  
  // Write operations
  add: (entity: Omit<T, 'id'>) => string;
  update: (id: string, updates: Partial<T>) => void;
  upsert: (entity: T) => void;
  delete: (id: string) => void;
  deleteMany: (predicate: (entity: T) => boolean) => void;
  
  // Batch operations
  setAll: (entities: T[]) => void;
  clear: () => void;
  
  // Selection state
  selectedId: string | null;
  selected: T | null;
  setSelected: (id: string | null) => void;
  isSelected: (id: string) => boolean;
}

/**
 * Hook for managing Node entities
 */
export const useNodeEntities = (): EntityOperations<Node> => {
  const diagramStore = useDiagramStore();
  const uiStore = useConsolidatedUIStore();
  
  const nodes = useMemo(() => {
    return Array.isArray(diagramStore.nodes) ? diagramStore.nodes : Array.from(diagramStore.nodes.values());
  }, [diagramStore.nodes]);
  
  return useMemo(
    () => ({
      // Read operations
      getAll: () => nodes,
      getById: (id: string) => nodes.find(n => n.id === id),
      find: (predicate: (entity: Node) => boolean) => nodes.find(predicate),
      filter: (predicate: (entity: Node) => boolean) => nodes.filter(predicate),
      
      // Write operations
      add: (node: Omit<Node, 'id'>) => {
        if (node.type && node.position) {
          const id = `${node.type}-${nanoid(4)}`;
          diagramStore.addNode(node.type, node.position);
          return id;
        }
        throw new Error('Node type and position are required');
      },
      update: (id: string, updates: Partial<Node>) => diagramStore.updateNode(id, updates),
      upsert: (node: Node) => {
        if (nodes.find(n => n.id === node.id)) {
          const { id: _, ...nodeData } = node;
          diagramStore.updateNode(node.id, nodeData.data || {});
        } else {
          diagramStore.addNode(node.type, node.position);
        }
      },
      delete: (id: string) => diagramStore.deleteNode(id),
      deleteMany: (predicate: (entity: Node) => boolean) => {
        nodes.filter(predicate).forEach(node => diagramStore.deleteNode(node.id));
      },
      
      // Batch operations
      setAll: (entities: Node[]) => diagramStore.setNodes(entities),
      clear: () => diagramStore.setNodes([]),
      
      // Selection state
      selectedId: uiStore.selectedNodeId,
      selected: nodes.find(n => n.id === uiStore.selectedNodeId) || null,
      setSelected: (id: string | null) => uiStore.setSelectedNodeId(id),
      isSelected: (id: string) => uiStore.selectedNodeId === id,
    }),
    [nodes, diagramStore, uiStore]
  );
};

/**
 * Hook for managing Arrow entities
 */
export const useArrowEntities = (): EntityOperations<Arrow> => {
  const diagramStore = useDiagramStore();
  const uiStore = useConsolidatedUIStore();
  
  const arrows = useMemo(() => {
    return Array.isArray(diagramStore.arrows) ? diagramStore.arrows : Array.from(diagramStore.arrows.values());
  }, [diagramStore.arrows]);
  
  return useMemo(
    () => ({
      // Read operations
      getAll: () => arrows,
      getById: (id: string) => arrows.find(a => a.id === id),
      find: (predicate: (entity: Arrow) => boolean) => arrows.find(predicate),
      filter: (predicate: (entity: Arrow) => boolean) => arrows.filter(predicate),
      
      // Write operations
      add: (arrow: Omit<Arrow, 'id'>) => {
        if (arrow.source && arrow.target) {
          const id = `arrow-${nanoid(4)}`;
          diagramStore.addArrow(
            arrow.source,
            arrow.target,
            arrow.sourceHandle,
            arrow.targetHandle
          );
          return id;
        }
        throw new Error('Arrow source and target are required');
      },
      update: (id: string, updates: Partial<Arrow>) => diagramStore.updateArrow(id, updates),
      upsert: (arrow: Arrow) => {
        if (arrows.find(a => a.id === arrow.id)) {
          const { id: _, ...arrowData } = arrow;
          diagramStore.updateArrow(arrow.id, arrowData.data || {});
        } else {
          diagramStore.addArrow(
            arrow.source,
            arrow.target,
            arrow.sourceHandle,
            arrow.targetHandle
          );
        }
      },
      delete: (id: string) => diagramStore.deleteArrow(id),
      deleteMany: (predicate: (entity: Arrow) => boolean) => {
        arrows.filter(predicate).forEach(arrow => diagramStore.deleteArrow(arrow.id));
      },
      
      // Batch operations
      setAll: (entities: Arrow[]) => diagramStore.setArrows(entities),
      clear: () => diagramStore.setArrows([]),
      
      // Selection state
      selectedId: uiStore.selectedArrowId,
      selected: arrows.find(a => a.id === uiStore.selectedArrowId) || null,
      setSelected: (id: string | null) => uiStore.setSelectedArrowId(id),
      isSelected: (id: string) => uiStore.selectedArrowId === id,
    }),
    [arrows, diagramStore, uiStore]
  );
};

/**
 * Hook for managing Person entities
 */
export const usePersonEntities = (): EntityOperations<Person> => {
  const diagramStore = useDiagramStore();
  
  const persons = useMemo(() => {
    return Array.isArray(diagramStore.persons) ? diagramStore.persons : Array.from(diagramStore.persons.values());
  }, [diagramStore.persons]);
  
  return useMemo(
    () => ({
      // Read operations
      getAll: () => persons,
      getById: (id: string) => persons.find(p => p.id === id),
      find: (predicate: (entity: Person) => boolean) => persons.find(predicate),
      filter: (predicate: (entity: Person) => boolean) => persons.filter(predicate),
      
      // Write operations
      add: (person: Omit<Person, 'id'>) => {
        const id = `person-${nanoid(4)}`;
        diagramStore.addPerson(person);
        return id;
      },
      update: (id: string, updates: Partial<Person>) => diagramStore.updatePerson(id, updates),
      upsert: (person: Person) => {
        if (persons.find(p => p.id === person.id)) {
          const { id: _, ...personData } = person;
          diagramStore.updatePerson(person.id, personData);
        } else {
          const { id: _, ...personData } = person;
          diagramStore.addPerson(personData);
        }
      },
      delete: (id: string) => diagramStore.deletePerson(id),
      deleteMany: (predicate: (entity: Person) => boolean) => {
        persons.filter(predicate).forEach(person => diagramStore.deletePerson(person.id));
      },
      
      // Batch operations
      setAll: (entities: Person[]) => diagramStore.setPersons(entities),
      clear: () => diagramStore.setPersons([]),
      
      // Selection state
      selectedId: null,
      selected: null,
      setSelected: () => {},
      isSelected: () => false,
    }),
    [persons, diagramStore]
  );
};

/**
 * Hook for managing API Key entities
 */
export const useApiKeyEntities = (): EntityOperations<ApiKey> => {
  const diagramStore = useDiagramStore();
  
  const apiKeys = useMemo(() => {
    return Array.isArray(diagramStore.apiKeys) ? diagramStore.apiKeys : Array.from(diagramStore.apiKeys.values());
  }, [diagramStore.apiKeys]);
  
  return useMemo(
    () => ({
      // Read operations
      getAll: () => apiKeys,
      getById: (id: string) => apiKeys.find(k => k.id === id),
      find: (predicate: (entity: ApiKey) => boolean) => apiKeys.find(predicate),
      filter: (predicate: (entity: ApiKey) => boolean) => apiKeys.filter(predicate),
      
      // Write operations
      add: (apiKey: Omit<ApiKey, 'id'>) => {
        const id = `APIKEY_${nanoid().slice(0, 6).replace(/-/g, '_').toUpperCase()}`;
        diagramStore.addApiKey(apiKey);
        return id;
      },
      update: (id: string, updates: Partial<ApiKey>) => diagramStore.updateApiKey(id, updates),
      upsert: (apiKey: ApiKey) => {
        if (apiKeys.find(k => k.id === apiKey.id)) {
          const { id: _, ...apiKeyData } = apiKey;
          diagramStore.updateApiKey(apiKey.id, apiKeyData);
        } else {
          const { id: _, ...apiKeyData } = apiKey;
          diagramStore.addApiKey(apiKeyData);
        }
      },
      delete: (id: string) => diagramStore.deleteApiKey(id),
      deleteMany: (predicate: (entity: ApiKey) => boolean) => {
        apiKeys.filter(predicate).forEach(apiKey => diagramStore.deleteApiKey(apiKey.id));
      },
      
      // Batch operations
      setAll: (entities: ApiKey[]) => diagramStore.setApiKeys(entities),
      clear: () => diagramStore.setApiKeys([]),
      
      // Selection state
      selectedId: null,
      selected: null,
      setSelected: () => {},
      isSelected: () => false,
    }),
    [apiKeys, diagramStore]
  );
};


