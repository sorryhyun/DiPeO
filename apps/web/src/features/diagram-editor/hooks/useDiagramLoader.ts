import { useState } from 'react';
import { useUnifiedStore } from '@/infrastructure/store/unifiedStore';
import { toast } from 'sonner';
import { diagramArraysToMaps } from '@/lib/graphql/types';

/**
 * Simplified diagram loader that only provides manual loading functionality
 * All automatic URL-based loading has been removed in favor of CLI session loading
 */

export function useDiagramLoader() {
  const [isLoading, setIsLoading] = useState(false);

  // Function to load diagram from data directly (used by CLI session monitor)
  const loadDiagramFromData = (diagramData: any) => {
    setIsLoading(true);
    
    try {
      // Convert diagram data to domain format
      const diagramWithCounts = {
        ...diagramData,
        nodeCount: diagramData.nodes?.length || 0,
        arrowCount: diagramData.arrows?.length || 0,
        personCount: diagramData.persons?.length || 0
      };
      
      // Convert to Maps for the store
      const { nodes, handles, persons, arrows } = diagramArraysToMaps({
        nodes: diagramData.nodes || [],
        arrows: diagramData.arrows || [],
        handles: diagramData.handles || [],
        persons: diagramData.persons || []
      });
      
      // Update store with diagram data
      const store = useUnifiedStore.getState();
      store.transaction(() => {
        // Clear existing data
        store.clearDiagram();
        
        // Restore the snapshot
        store.restoreSnapshot({
          nodes,
          arrows,
          persons,
          handles,
          timestamp: Date.now()
        });
        
        // Set metadata
        if (diagramData.metadata) {
          store.setDiagramName(diagramData.metadata.name || 'CLI Diagram');
          store.setDiagramDescription(diagramData.metadata.description || '');
          store.setDiagramId(diagramData.metadata.id || null);
        }
      });
      
      toast.success('Loaded diagram from CLI');
    } catch (err) {
      console.error('Failed to load diagram from data:', err);
      toast.error('Failed to load diagram from CLI');
    } finally {
      setIsLoading(false);
    }
  };

  return {
    isLoading,
    hasLoaded: false, // Deprecated - kept for compatibility
    diagramId: null, // Deprecated - kept for compatibility  
    diagramFormat: null, // Deprecated - kept for compatibility
    error: null, // Deprecated - kept for compatibility
    loadDiagramFromData
  };
}