import type { StoreApi } from 'zustand';
import type { UnifiedStore } from '../unifiedStore.types';

/**
 * Subscribe to dataVersion changes and sync arrays
 * This avoids cross-slice violations by using the subscription mechanism
 */
export function initializeArraySync(store: StoreApi<UnifiedStore>) {
  let previousDataVersion = store.getState().dataVersion;
  
  // Subscribe to state changes
  return store.subscribe((state, prevState) => {
    // Check if dataVersion changed
    if (state.dataVersion !== previousDataVersion) {
      previousDataVersion = state.dataVersion;
      
      // Update arrays when dataVersion changes
      // This runs outside of the action that caused the change
      const currentState = store.getState();
      store.setState({
        nodesArray: Array.from(currentState.nodes.values()),
        arrowsArray: Array.from(currentState.arrows.values()),
        personsArray: Array.from(currentState.persons.values())
      });
    }
  });
}