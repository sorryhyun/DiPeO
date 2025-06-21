import { useUnifiedStore as useStore } from '@/core/store/unifiedStore';

// Re-export the store hook
export const useUnifiedStore = useStore;

// Re-export selector hooks
export { 
  useNodeById,
  useArrowById,
  usePersonById,
  useSelectedEntity,
  useIsExecuting,
  useNodeExecutionState
} from '@/core/store/unifiedStore';