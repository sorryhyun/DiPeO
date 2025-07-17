import { useEffect, useState, useRef } from 'react';
import { GetDiagramDocument } from '@/__generated__/graphql';
import { useUnifiedStore } from '@/core/store/unifiedStore';
import { toast } from 'sonner';
import { diagramId } from '@/core/types';
import { diagramToStoreMaps, convertGraphQLDiagramToDomain } from '@/lib/graphql/types';
import { rebuildHandleIndex } from '@/core/store/helpers/handleIndexHelper';
import { createEntityQuery } from '@/lib/graphql/hooks';
import { DiagramFormat } from '@dipeo/domain-models';

/**
 * Refactored diagram loader using the GraphQL factory pattern
 * Maintains all original functionality with cleaner code structure
 */

// Create the diagram query using factory
const useDiagramQuery = createEntityQuery({
  entityName: 'Diagram',
  document: GetDiagramDocument,
  cacheStrategy: 'cache-first',
  silent: true // We'll handle errors manually for custom logic
});

export function useDiagramLoader() {
  const [isLoading, setIsLoading] = useState(false);
  const [diagramIdFromUrl, setDiagramIdFromUrl] = useState<string | null>(null);
  const [diagramFormatFromUrl, setDiagramFormatFromUrl] = useState<DiagramFormat | null>(null);
  
  // Track what diagram we've actually loaded to prevent reloads
  const loadedDiagramIdRef = useRef<string | null>(null);
  const hasInitializedRef = useRef(false);

  // Parse diagram parameter from URL
  const parseDiagramParam = (diagramParam: string | null): { id: string | null; format: DiagramFormat | null } => {
    if (!diagramParam) return { id: null, format: null };
    
    const parts = diagramParam.split('/');
    let format: DiagramFormat | null = null;
    
    // Parse format from path prefix
    if (parts.length === 2) {
      const [formatStr] = parts;
      switch (formatStr) {
        case 'native':
          format = DiagramFormat.NATIVE;
          break;
        case 'light':
          format = DiagramFormat.LIGHT;
          break;
        case 'readable':
          format = DiagramFormat.READABLE;
          break;
      }
    }
    
    // Detect format from file extension if not found
    if (!format) {
      if (diagramParam.endsWith('.native.json') || diagramParam.endsWith('.json')) {
        format = DiagramFormat.NATIVE;
      } else if (diagramParam.endsWith('.light.yaml') || diagramParam.endsWith('.light.yml')) {
        format = DiagramFormat.LIGHT;
      } else if (diagramParam.endsWith('.readable.yaml') || diagramParam.endsWith('.readable.yml')) {
        format = DiagramFormat.READABLE;
      } else if (diagramParam.endsWith('.yaml') || diagramParam.endsWith('.yml')) {
        format = DiagramFormat.LIGHT; // Default YAML to light format
      }
    }
    
    return { id: diagramParam, format };
  };

  // Check URL for diagram parameter
  useEffect(() => {
    const checkUrl = () => {
      const params = new URLSearchParams(window.location.search);
      const diagramParam = params.get('diagram');
      const { id, format } = parseDiagramParam(diagramParam);
      
      // Only proceed if diagram ID is different from what we've loaded
      if (id !== loadedDiagramIdRef.current) {
        setDiagramIdFromUrl(id);
        setDiagramFormatFromUrl(format);
      }
    };
    
    // Initial check
    checkUrl();
    hasInitializedRef.current = true;
    
    // Listen for URL changes
    window.addEventListener('popstate', checkUrl);
    return () => window.removeEventListener('popstate', checkUrl);
  }, []); // No dependencies - we want this to run once

  // Query for diagram data using factory-generated hook
  const { data, loading, error } = useDiagramQuery(
    { id: diagramId(diagramIdFromUrl || '') },
    { 
      skip: !diagramIdFromUrl || loadedDiagramIdRef.current === diagramIdFromUrl,
      // Custom error handling
      onError: (error) => {
        console.error('Failed to fetch diagram:', error);
        toast.error(`Failed to load diagram: ${error.message}`);
        // Mark as loaded to prevent retry
        loadedDiagramIdRef.current = diagramIdFromUrl;
      },
      // Custom success handling
      onCompleted: (data) => {
        if (!data.diagram && diagramIdFromUrl) {
          toast.error(`Diagram "${diagramIdFromUrl}" not found`);
          // Mark as loaded to prevent retry
          loadedDiagramIdRef.current = diagramIdFromUrl;
        }
      }
    }
  );

  // Load diagram data into store
  useEffect(() => {
    // Skip if already loaded this diagram
    if (loadedDiagramIdRef.current === diagramIdFromUrl) {
      return;
    }
    
    if (!loading && diagramIdFromUrl && data?.diagram) {
      setIsLoading(true);
      
      // Delay loading until after the component tree has mounted
      const loadTimer = setTimeout(() => {
        try {
          if (!data?.diagram) return;
        
          // Convert GraphQL diagram to domain format
          const diagramWithCounts = {
            ...data.diagram,
            nodeCount: data.diagram.nodes.length,
            arrowCount: data.diagram.arrows.length,
            personCount: data.diagram.persons.length
          };
          
          // Convert GraphQL types to domain types
          const domainDiagram = convertGraphQLDiagramToDomain(diagramWithCounts);
          
          // Convert arrays to Maps for the store
          const { nodes, handles, persons } = diagramToStoreMaps(domainDiagram);
          let { arrows } = diagramToStoreMaps(domainDiagram);
          
          // Deduplicate arrows based on source/target
          const arrowMap = new Map<string, typeof arrows extends Map<any, infer V> ? V : never>();
          arrows.forEach((arrow) => {
            // Create a key for deduplication without changing case
            const key = `${arrow.source}->${arrow.target}`;
            
            // Keep the first occurrence
            if (!arrowMap.has(key)) {
              arrowMap.set(key, arrow);
            }
          });
          
          // Convert back to arrow Map with original IDs
          const deduplicatedArrows = new Map();
          arrowMap.forEach((arrow) => {
            deduplicatedArrows.set(arrow.id, arrow);
          });
          arrows = deduplicatedArrows;
          
          // Keep handles as-is without normalization
          // Handle IDs contain node IDs which must preserve their original casing
          
          // Note: We don't clean up orphaned handles during loading anymore
          // This is handled when saving the diagram and when deleting nodes
          // This prevents issues with timing and ensures we don't accidentally
          // remove valid handles during the loading process
          
          // Update store with all data at once in a single transaction
          const store = useUnifiedStore.getState();
          store.transaction(() => {
            // Preserve the active canvas state before clearing
            const currentActiveCanvas = store.activeCanvas;
            
            // First clear existing data to ensure clean slate
            store.clearAll();
            
            // Add a micro-delay to ensure React Flow processes the clear
            requestAnimationFrame(() => {
              // Restore the active canvas state
              store.setActiveCanvas(currentActiveCanvas);
              
              // Then restore the snapshot which properly updates all slices
              store.restoreSnapshot({
                nodes,
                arrows,
                persons,
                handles,
                timestamp: Date.now()
              });
              
              // Set diagram metadata after restoring snapshot
              if (diagramWithCounts.metadata) {
                store.setDiagramName(diagramWithCounts.metadata.name || 'Untitled');
                store.setDiagramDescription(diagramWithCounts.metadata.description || '');
              }
              store.setDiagramId(diagramIdFromUrl);
              store.setDiagramFormat(diagramFormatFromUrl);
            });
          });

          // Mark this diagram as loaded
          loadedDiagramIdRef.current = diagramIdFromUrl;
          
          // Show success message
          const diagramName = diagramWithCounts.metadata?.name || 'Unnamed diagram';
          toast.success(`Loaded diagram: ${diagramName}`);
          
        } catch (err) {
          console.error('Failed to load diagram:', err);
          toast.error('Failed to load diagram');
        } finally {
          // Always clear loading state
          setIsLoading(false);
        }
      }, 250); // Give component tree time to mount and ReactFlow to initialize
      
      // Cleanup timer on unmount or when dependencies change
      return () => clearTimeout(loadTimer);
    }
  }, [data, loading, diagramIdFromUrl, diagramFormatFromUrl]);

  return {
    isLoading: loading || isLoading,
    hasLoaded: loadedDiagramIdRef.current === diagramIdFromUrl,
    diagramId: diagramIdFromUrl,
    diagramFormat: diagramFormatFromUrl,
    error
  };
}