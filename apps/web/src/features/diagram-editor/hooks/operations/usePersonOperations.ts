/**
 * usePersonOperations - Simplified hook that directly returns store methods
 */

import { useUnifiedStore } from '@/shared/hooks/useUnifiedStore';
import { useShallow } from 'zustand/react/shallow';

export function usePersonOperations() {
  return useUnifiedStore(
    useShallow(state => ({
      addPerson: state.addPerson,
      updatePerson: state.updatePerson,
      deletePerson: state.deletePerson,
    }))
  );
}