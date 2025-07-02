/**
 * useArrowOperations - Simplified hook that directly returns store methods
 */

import { useUnifiedStore } from '@/shared/hooks/useUnifiedStore';
import { useShallow } from 'zustand/react/shallow';

export function useArrowOperations() {
  return useUnifiedStore(
    useShallow(state => ({
      addArrow: state.addArrow,
      updateArrow: state.updateArrow,
      deleteArrow: state.deleteArrow,
    }))
  );
}