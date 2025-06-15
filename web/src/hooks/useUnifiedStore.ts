import { useUnifiedStore as useStore } from '@/stores/unifiedStore';

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
} from '@/stores/unifiedStore';