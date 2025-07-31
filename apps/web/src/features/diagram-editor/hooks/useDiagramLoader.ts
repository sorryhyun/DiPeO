import { useEffect, useState, useRef } from 'react';
import { GetDiagramDocument } from '@/__generated__/graphql';
import { useUnifiedStore } from '@/core/store/unifiedStore';
import { toast } from 'sonner';
import { diagramId } from '@/core/types';
import { diagramArraysToMaps, convertGraphQLDiagramToDomain } from '@/lib/graphql/types';
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
  const checkUrlTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastCheckTimeRef = useRef<number>(0);
  const hasShownToastRef = useRef<string | null>(null); // Track which diagram ID we've shown toast for
  
  // Get activeCanvas to check if we're in execution mode
  const activeCanvas = useUnifiedStore(state => state.activeCanvas);

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
      const isMonitorMode = params.get('monitor') === 'true' || !!params.get('executionId');
      const noAutoExit = params.get('no-auto-exit') === 'true';
      
      // Skip URL-based loading if we're in execution mode but NOT monitor mode
      // This prevents reloading when user enters execution mode to run the canvas diagram
      if (activeCanvas === 'execution' && !isMonitorMode) {
        return;
      }
      
      // Also skip if we're in monitor mode with no-auto-exit and already loaded
      if (isMonitorMode && noAutoExit && loadedDiagramIdRef.current) {
        return;
      }
      
      const { id, format } = parseDiagramParam(diagramParam);
      
      // Only proceed if diagram ID is different from what we've loaded
      if (id !== loadedDiagramIdRef.current) {
        // Debug: Log when we're setting a new diagram ID
        if (id && process.env.NODE_ENV === 'development') {
          console.log(`[DiagramLoader] Setting new diagram ID: ${id} (previous: ${loadedDiagramIdRef.current})`);
        }
        setDiagramIdFromUrl(id);
        setDiagramFormatFromUrl(format);
      }
    };
    
    // Initial check
    checkUrl();
    hasInitializedRef.current = true;
    
    // Debounced popstate handler to prevent rapid repeated calls
    const handlePopState = () => {
      // Rate limit: ignore if called within 500ms of last check
      const now = Date.now();
      if (now - lastCheckTimeRef.current < 500) {
        return;
      }
      
      // Clear any pending timeout
      if (checkUrlTimeoutRef.current) {
        clearTimeout(checkUrlTimeoutRef.current);
      }
      
      // Set a new timeout to debounce rapid popstate events
      checkUrlTimeoutRef.current = setTimeout(() => {
        lastCheckTimeRef.current = Date.now();
        checkUrl();
      }, 100);
    };
    
    // Listen for URL changes
    window.addEventListener('popstate', handlePopState);
    return () => {
      window.removeEventListener('popstate', handlePopState);
      if (checkUrlTimeoutRef.current) {
        clearTimeout(checkUrlTimeoutRef.current);
      }
    };
  }, [activeCanvas]); // Add activeCanvas as dependency

  // Check if we should skip diagram loading
  const isMonitorMode = () => {
    const params = new URLSearchParams(window.location.search);
    return params.get('monitor') === 'true' || !!params.get('executionId');
  };
  
  const shouldSkipLoading = !diagramIdFromUrl || 
    loadedDiagramIdRef.current === diagramIdFromUrl ||
    (activeCanvas === 'execution' && !isMonitorMode());

  // Query for diagram data using factory-generated hook
  const { data, loading, error } = useDiagramQuery(
    { id: diagramId(diagramIdFromUrl || '') },
    { 
      skip: shouldSkipLoading,
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
    
    // Also skip if we're in execution mode but not monitor mode
    if (activeCanvas === 'execution' && !isMonitorMode()) {
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
          const { nodes, handles, persons, arrows: initialArrows } = diagramArraysToMaps({
            nodes: domainDiagram.nodes || [],
            arrows: domainDiagram.arrows || [],
            handles: domainDiagram.handles || [],
            persons: domainDiagram.persons || []
          });
          let arrows = initialArrows;
          
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
                store.setDiagramName(diagramWithCounts.metadata.name || diagramIdFromUrl);
                store.setDiagramDescription(diagramWithCounts.metadata.description || '');
              } else {
                // If no metadata exists, use the full path as the diagram name
                // This allows users to edit the full path for saving
                store.setDiagramName(diagramIdFromUrl);
                store.setDiagramDescription('');
              }
              store.setDiagramId(diagramIdFromUrl);
              store.setDiagramFormat(diagramFormatFromUrl);
            });
          });

          // Mark this diagram as loaded
          loadedDiagramIdRef.current = diagramIdFromUrl;
          
          // Show success message only once per diagram
          if (hasShownToastRef.current !== diagramIdFromUrl) {
            hasShownToastRef.current = diagramIdFromUrl;
            const diagramName = diagramWithCounts.metadata?.name || 'Unnamed diagram';
            toast.success(`Loaded diagram: ${diagramName}`);
          }
          
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
  }, [data, loading, diagramIdFromUrl, diagramFormatFromUrl, activeCanvas]);

  return {
    isLoading: loading || isLoading,
    hasLoaded: loadedDiagramIdRef.current === diagramIdFromUrl,
    diagramId: diagramIdFromUrl,
    diagramFormat: diagramFormatFromUrl,
    error
  };
}