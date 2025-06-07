import { useCallback, useMemo } from 'react';
import { nanoid } from 'nanoid';

/**
 * Generic entity type with required id field
 */
export interface Entity {
  id: string;
  [key: string]: unknown;
}

/**
 * CRUD operations for any entity type
 */
export interface SingleEntityOperations<T extends Entity> {
  // Read operations
  getAll: () => T[];
  getById: (id: string) => T | undefined;
  find: (predicate: (entity: T) => boolean) => T | undefined;
  filter: (predicate: (entity: T) => boolean) => T[];
  
  // Write operations
  add: (entity: Omit<T, 'id'>) => string; // Returns the generated ID
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
 * Configuration for entity hook
 */
export interface UseEntityConfig<T extends Entity> {
  // Store getters
  getEntities: () => Map<string, T> | T[];
  
  // Store setters
  addEntity?: (entity: T) => void;
  updateEntity?: (id: string, updates: Partial<T>) => void;
  deleteEntity?: (id: string) => void;
  setEntities?: (entities: T[]) => void;
  
  // Selection (optional)
  getSelectedId?: () => string | null;
  setSelectedId?: (id: string | null) => void;
  
  // Options
  generateId?: () => string;
  validateEntity?: (entity: Partial<T>) => boolean;
  onError?: (error: Error) => void;
}

/**
 * Generic entity management hook factory
 * Creates a hook with CRUD operations for any entity type
 */
export function createEntityHook<T extends Entity>(
  config: UseEntityConfig<T>
): () => SingleEntityOperations<T> {
  return function useEntity(): SingleEntityOperations<T> {
    const {
      getEntities,
      addEntity,
      updateEntity,
      deleteEntity,
      setEntities,
      getSelectedId,
      setSelectedId,
      generateId = () => nanoid(8),
      validateEntity,
      onError,
    } = config;

    // Convert entities to array if they're a Map
    const entities = useMemo(() => {
      const raw = getEntities();
      if (raw instanceof Map) {
        return Array.from(raw.values());
      }
      return raw;
    }, [getEntities()]);

    // Entity map for O(1) lookups
    const entityMap = useMemo(() => {
      return new Map(entities.map(e => [e.id, e]));
    }, [entities]);

    // Read operations
    const getAll = useCallback(() => entities, [entities]);
    
    const getById = useCallback((id: string) => {
      return entityMap.get(id);
    }, [entityMap]);

    const find = useCallback((predicate: (entity: T) => boolean) => {
      return entities.find(predicate);
    }, [entities]);

    const filter = useCallback((predicate: (entity: T) => boolean) => {
      return entities.filter(predicate);
    }, [entities]);

    // Write operations
    const add = useCallback((entityData: Omit<T, 'id'>) => {
      if (!addEntity) {
        onError?.(new Error('Add operation not supported'));
        return '';
      }

      const id = generateId();
      const entity = { ...entityData, id } as T;

      if (validateEntity && !validateEntity(entity)) {
        onError?.(new Error('Entity validation failed'));
        return '';
      }

      try {
        addEntity(entity);
        return id;
      } catch (error) {
        onError?.(error as Error);
        return '';
      }
    }, [addEntity, generateId, validateEntity, onError]);

    const update = useCallback((id: string, updates: Partial<T>) => {
      if (!updateEntity) {
        onError?.(new Error('Update operation not supported'));
        return;
      }

      const existing = getById(id);
      if (!existing) {
        onError?.(new Error(`Entity with id ${id} not found`));
        return;
      }

      const updated = { ...existing, ...updates, id }; // Ensure ID isn't changed
      if (validateEntity && !validateEntity(updated)) {
        onError?.(new Error('Entity validation failed'));
        return;
      }

      try {
        updateEntity(id, updates);
      } catch (error) {
        onError?.(error as Error);
      }
    }, [updateEntity, getById, validateEntity, onError]);

    const upsert = useCallback((entity: T) => {
      const existing = getById(entity.id);
      if (existing) {
        update(entity.id, entity);
      } else if (addEntity) {
        addEntity(entity);
      }
    }, [getById, update, addEntity]);

    const deleteOne = useCallback((id: string) => {
      if (!deleteEntity) {
        onError?.(new Error('Delete operation not supported'));
        return;
      }

      try {
        deleteEntity(id);
      } catch (error) {
        onError?.(error as Error);
      }
    }, [deleteEntity, onError]);

    const deleteMany = useCallback((predicate: (entity: T) => boolean) => {
      if (!deleteEntity) {
        onError?.(new Error('Delete operation not supported'));
        return;
      }

      const toDelete = entities.filter(predicate);
      toDelete.forEach(entity => {
        try {
          deleteEntity(entity.id);
        } catch (error) {
          onError?.(error as Error);
        }
      });
    }, [entities, deleteEntity, onError]);

    // Batch operations
    const setAll = useCallback((newEntities: T[]) => {
      if (!setEntities) {
        onError?.(new Error('Set operation not supported'));
        return;
      }

      try {
        setEntities(newEntities);
      } catch (error) {
        onError?.(error as Error);
      }
    }, [setEntities, onError]);

    const clear = useCallback(() => {
      setAll([]);
    }, [setAll]);

    // Selection
    const selectedId = getSelectedId?.() || null;
    const selected = selectedId ? getById(selectedId) || null : null;

    const setSelected = useCallback((id: string | null) => {
      if (!setSelectedId) {
        onError?.(new Error('Selection not supported'));
        return;
      }
      setSelectedId(id);
    }, [setSelectedId, onError]);

    const isSelected = useCallback((id: string) => {
      return selectedId === id;
    }, [selectedId]);

    return {
      // Read
      getAll,
      getById,
      find,
      filter,
      
      // Write
      add,
      update,
      upsert,
      delete: deleteOne,
      deleteMany,
      
      // Batch
      setAll,
      clear,
      
      // Selection
      selectedId,
      selected,
      setSelected,
      isSelected,
    };
  };
}

/**
 * Create specialized entity hooks for common types
 */

// Example: Node entity hook
export const createNodeEntityHook = (store: any) =>
  createEntityHook<any>({
    getEntities: () => store.nodes,
    addEntity: (node) => store.addNode(node.type, node.position),
    updateEntity: store.updateNode,
    deleteEntity: store.deleteNode,
    setEntities: store.setNodes,
    getSelectedId: () => store.selectedNodeId,
    setSelectedId: store.setSelectedNodeId,
  });

// Example: Arrow entity hook
export const createArrowEntityHook = (store: any) =>
  createEntityHook<any>({
    getEntities: () => store.arrows,
    addEntity: (arrow) => store.addArrow(arrow.source, arrow.target, arrow.sourceHandle, arrow.targetHandle),
    updateEntity: store.updateArrow,
    deleteEntity: store.deleteArrow,
    setEntities: store.setArrows,
    getSelectedId: () => store.selectedArrowId,
    setSelectedId: store.setSelectedArrowId,
  });

// Example: Person entity hook  
export const createPersonEntityHook = (store: any) =>
  createEntityHook<any>({
    getEntities: () => store.persons,
    addEntity: store.addPerson,
    updateEntity: store.updatePerson,
    deleteEntity: store.deletePerson,
    setEntities: store.setPersons,
  });