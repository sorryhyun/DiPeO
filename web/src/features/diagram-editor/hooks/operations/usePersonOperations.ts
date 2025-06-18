/**
 * usePersonOperations - Person CRUD operations
 * 
 * Provides CRUD operations for managing persons in the diagram.
 */

import { useCallback } from 'react';
import { useUnifiedStore } from '@/shared/hooks/useUnifiedStore';
import { PersonID, DomainPerson } from '@/core/types';

export interface UsePersonOperationsReturn {
  // CRUD operations
  addPerson: (label: string, service: string, model: string) => PersonID;
  updatePerson: (id: PersonID, updates: { label?: string; service?: string; model?: string }) => void;
  deletePerson: (id: PersonID) => void;
}

export function usePersonOperations(): UsePersonOperationsReturn {
  const store = useUnifiedStore;

  // Direct operations using store methods
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