import { logger } from '@/utils/logger';
import type { ExportFormat } from './diagramExporter';

// Auto-save functionality
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function setupAutoSave(store: any): void {
  // Save to localStorage every 5 seconds if there are changes
  let lastSaveTime = Date.now();
  let hasChanges = false;
  
  // Create a debounced save function
  let debounceTimer: NodeJS.Timeout | null = null;
  const debouncedSave = () => {
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      if (hasChanges) {
        try {
          const exportData = store.getState().exportDiagram();
          localStorage.setItem('dipeo_autosave', JSON.stringify(exportData));
          localStorage.setItem('dipeo_autosave_time', new Date().toISOString());
          hasChanges = false;
          lastSaveTime = Date.now();
          logger.debug('Auto-saved diagram (debounced)');
        } catch (e) {
          logger.error('Debounced auto-save failed:', e);
        }
      }
    }, 2000); // 2 second debounce
  };
  
  // Track changes only for data-bearing Maps to avoid unnecessary saves
  const unsubscribe = store.subscribe(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (state: any) => ({
      nodes: state.nodes,
      arrows: state.arrows,
      persons: state.persons,
      handles: state.handles,
      apiKeys: state.apiKeys
    }),
    () => {
      hasChanges = true;
      debouncedSave();
    },
    {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      equalityFn: (a: any, b: any) => {
        // Check if the Map references have changed
        return a.nodes === b.nodes &&
               a.arrows === b.arrows &&
               a.persons === b.persons &&
               a.handles === b.handles &&
               a.apiKeys === b.apiKeys;
      }
    }
  );
  
  // Auto-save interval
  const intervalId = setInterval(() => {
    if (hasChanges && Date.now() - lastSaveTime > 5000) {
      try {
        // Get the export data using the store's exportDiagram method
        const exportData = store.getState().exportDiagram();
        localStorage.setItem('dipeo_autosave', JSON.stringify(exportData));
        localStorage.setItem('dipeo_autosave_time', new Date().toISOString());
        hasChanges = false;
        lastSaveTime = Date.now();
        logger.debug('Auto-saved diagram');
      } catch (e) {
        logger.error('Auto-save failed:', e);
      }
    }
  }, 5000);
  
  // Clean up on page unload
  if (typeof window !== 'undefined') {
    window.addEventListener('beforeunload', () => {
      clearInterval(intervalId);
      if (debounceTimer) clearTimeout(debounceTimer);
      unsubscribe();
    });
  }
}

// Load auto-saved data
export function loadAutoSavedDiagram(): ExportFormat | null {
  try {
    const saved = localStorage.getItem('dipeo_autosave');
    if (!saved) return null;
    
    const data = JSON.parse(saved);
    const saveTime = localStorage.getItem('dipeo_autosave_time');
    
    // Check if save is recent (within 24 hours)
    if (saveTime) {
      const timeDiff = Date.now() - new Date(saveTime).getTime();
      if (timeDiff > 24 * 60 * 60 * 1000) {
        // Clear old auto-save
        localStorage.removeItem('dipeo_autosave');
        localStorage.removeItem('dipeo_autosave_time');
        return null;
      }
    }
    
    return data;
  } catch {
    return null;
  }
}

// Clear auto-saved data
export function clearAutoSave(): void {
  localStorage.removeItem('dipeo_autosave');
  localStorage.removeItem('dipeo_autosave_time');
}