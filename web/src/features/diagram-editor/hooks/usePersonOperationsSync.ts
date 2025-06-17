/**
 * usePersonOperationsSync - Synchronous adapter for person operations
 * 
 * This provides a sync API that matches the original useCanvasOperations interface
 * by directly using the store's synchronous person operations.
 */

import { useCallback } from 'react';
import { useUnifiedStore } from '@/shared/hooks/useUnifiedStore';
import { PersonID, DomainPerson } from '@/core/types';

export interface UsePersonOperationsSyncReturn {
  // Sync CRUD operations matching original API
  addPerson: (label: string, service: string, model: string) => PersonID;
  updatePerson: (id: PersonID, updates: { label?: string; service?: string; model?: string }) => void;
  deletePerson: (id: PersonID) => void;
}

export function usePersonOperationsSync(): UsePersonOperationsSyncReturn {
  const store = useUnifiedStore;

  // Direct sync operations using store methods
  const addPerson = useCallback((label: string, service: string, model: string): PersonID => {
    return store.getState().addPerson(label, service, model);
  }, []);

  const updatePerson = useCallback((id: PersonID, updates: { label?: string; service?: string; model?: string }): void => {
    store.getState().updatePerson(id, updates as Partial<DomainPerson>);
  }, []);

  const deletePerson = useCallback((id: PersonID): void => {
    store.getState().deletePerson(id);
  }, []);

  return {
    addPerson,
    updatePerson,
    deletePerson
  };
}