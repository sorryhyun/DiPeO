import { useUnifiedStore } from '../unifiedStore';

// Subscribe to execution state changes and sync UI state
export function setupExecutionUISync() {
  const unsubscribe = useUnifiedStore.subscribe(
    state => state.execution.isRunning,
    (isRunning, previousIsRunning) => {
      const state = useUnifiedStore.getState();
      
      // When execution starts
      if (isRunning && !previousIsRunning) {
        state.setActiveView('execution');
        state.setActiveCanvas('execution');
        state.setReadOnly(true);
      }
      
      // When execution stops
      if (!isRunning && previousIsRunning) {
        state.setReadOnly(false);
      }
    }
  );
  
  return unsubscribe;
}