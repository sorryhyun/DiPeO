// Generic CRUD utilities for Zustand stores
import { nanoid } from 'nanoid';

export interface CrudItem {
  id: string;
}

export interface CrudActions<T extends CrudItem> {
  add: (item: Omit<T, 'id'>) => void;
  update: (id: string, data: Partial<T>) => void;
  delete: (id: string) => void;
  getById: (id: string) => T | undefined;
  clear: () => void;
}

/**
 * Creates generic CRUD operations for a collection in a Zustand store
 */
export function createCrudActions<T extends CrudItem>(
  getItems: () => T[],
  setItems: (items: T[]) => void,
  idPrefix: string
): CrudActions<T> {
  return {
    add: (itemData: Omit<T, 'id'>) => {
      const newItem = {
        ...itemData,
        id: `${idPrefix}_${nanoid().slice(0, 6).replace(/-/g, '_').toUpperCase()}`
      } as T;
      setItems([...getItems(), newItem]);
    },

    update: (id: string, data: Partial<T>) => {
      console.log(`[CRUD Store] Updating ${idPrefix} item:`, {
        id,
        data,
        currentItems: getItems().find(item => item.id === id)
      });
      
      // Optimize updates by checking if the data actually changed
      const currentItem = getItems().find(item => item.id === id);
      if (!currentItem) {
        console.warn(`[CRUD Store] Item ${idPrefix} ${id} not found for update`);
        return;
      }
      
      // Check if any values actually changed
      const hasChanges = Object.entries(data).some(([key, value]) => 
        currentItem[key as keyof T] !== value
      );
      
      if (!hasChanges) {
        console.log(`[CRUD Store] No actual changes detected for ${idPrefix} ${id}, skipping update`);
        return;
      }
      
      console.log(`[CRUD Store] Applying updates to ${idPrefix} ${id}:`, {
        before: currentItem,
        updates: data,
        after: { ...currentItem, ...data }
      });
      
      setItems(
        getItems().map(item => 
          item.id === id ? { ...item, ...data } : item
        )
      );
    },

    delete: (id: string) => {
      setItems(getItems().filter(item => item.id !== id));
    },

    getById: (id: string) => {
      return getItems().find(item => item.id === id);
    },

    clear: () => {
      setItems([]);
    }
  };
}


/**
 * Creates CRUD actions with exact method names for store interfaces
 */
export function createPersonCrudActions<T extends CrudItem>(
  getItems: () => T[],
  setItems: (items: T[]) => void,
  idPrefix: string
) {
  const baseCrud = createCrudActions(getItems, setItems, idPrefix);
  
  return {
    addPerson: (itemData: Omit<T, 'id'>) => {
      baseCrud.add(itemData);
    },
    updatePerson: (id: string, data: Partial<T>) => {
      baseCrud.update(id, data);
    },
    deletePerson: baseCrud.delete,
    getPersonById: baseCrud.getById,
    clearPersons: baseCrud.clear
  };
}

export function createApiKeyCrudActions<T extends CrudItem>(
  getItems: () => T[],
  setItems: (items: T[]) => void,
  idPrefix: string
) {
  const baseCrud = createCrudActions(getItems, setItems, idPrefix);
  
  return {
    addApiKey: baseCrud.add,
    updateApiKey: baseCrud.update,
    deleteApiKey: baseCrud.delete,
    getApiKeyById: baseCrud.getById,
    clearApiKeys: baseCrud.clear
  };
}