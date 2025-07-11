import type { StoreApi } from 'zustand';
import type { UnifiedStore } from '../unifiedStore.types';

// Subscribe to dataVersion changes and sync arrays
export function initializeArraySync(store: StoreApi<UnifiedStore>) {
  // Perform initial sync to ensure arrays are populated
  const initialState = store.getState();
  store.setState({
    nodesArray: Array.from(initialState.nodes.values()),
    arrowsArray: Array.from(initialState.arrows.values()),
    personsArray: Array.from(initialState.persons.values()),
    handlesArray: Array.from(initialState.handles.values())
  });
  
  let previousDataVersion = initialState.dataVersion;
  
  // Subscribe to state changes
  return store.subscribe((state) => {
    // Check if dataVersion changed
    if (state.dataVersion !== previousDataVersion) {
      previousDataVersion = state.dataVersion;
      
      // Update arrays when dataVersion changes
      // This runs outside of the action that caused the change
      const currentState = store.getState();
      store.setState({
        nodesArray: Array.from(currentState.nodes.values()),
        arrowsArray: Array.from(currentState.arrows.values()),
        personsArray: Array.from(currentState.persons.values()),
        handlesArray: Array.from(currentState.handles.values())
      });
    }
  });
}