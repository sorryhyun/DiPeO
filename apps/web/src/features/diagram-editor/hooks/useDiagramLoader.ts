import { useEffect, useState } from 'react';
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
  const [hasLoaded, setHasLoaded] = useState(false);
  const [diagramIdFromUrl, setDiagramIdFromUrl] = useState<string | null>(null);
  const [diagramFormatFromUrl, setDiagramFormatFromUrl] = useState<DiagramFormat | null>(null);

  // Check URL for diagram parameter
  useEffect(() => {
    const checkUrlParams = () => {
      const params = new URLSearchParams(window.location.search);
      const diagramParam = params.get('diagram');
      
      if (diagramParam) {
        // Parse format and filename from the diagram parameter
        // Format: {format}/{filename} or just {filename}
        const parts = diagramParam.split('/');
        let format: DiagramFormat | null = null;
        const fullDiagramId = diagramParam;
        
        if (parts.length === 2) {
          // Has format prefix
          const [formatStr, filename] = parts;
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
            default:
              // Unknown format, try to detect from file extension
              format = null;
          }
        }
        
        // If format not detected from path, try to detect from file extension
        if (!format) {
          if (fullDiagramId.endsWith('.native.json') || fullDiagramId.endsWith('.json')) {
            format = DiagramFormat.NATIVE;
          } else if (fullDiagramId.endsWith('.light.yaml') || fullDiagramId.endsWith('.light.yml')) {
            format = DiagramFormat.LIGHT;
          } else if (fullDiagramId.endsWith('.readable.yaml') || fullDiagramId.endsWith('.readable.yml')) {
            format = DiagramFormat.READABLE;
          } else if (fullDiagramId.endsWith('.yaml') || fullDiagramId.endsWith('.yml')) {
            // For generic YAML files, check if in a format directory
            if (parts.length > 1) {
              const firstPart = parts[0];
              if (firstPart === 'light') format = DiagramFormat.LIGHT;
              else if (firstPart === 'readable') format = DiagramFormat.READABLE;
              else format = DiagramFormat.LIGHT; // Default YAML to light format
            } else {
              format = DiagramFormat.LIGHT; // Default YAML to light format
            }
          }
        }
        
        if (diagramParam !== diagramIdFromUrl) {
          setDiagramIdFromUrl(fullDiagramId);
          setDiagramFormatFromUrl(format);
          setHasLoaded(false); // Reset loaded state when diagram ID changes
        }
      }
    };

    // Check on mount
    checkUrlParams();

    // Listen for URL changes
    const handleUrlChange = () => checkUrlParams();
    window.addEventListener('popstate', handleUrlChange);

    return () => {
      window.removeEventListener('popstate', handleUrlChange);
    };
  }, [diagramIdFromUrl, diagramFormatFromUrl]);

  // Query for diagram data using factory-generated hook
  const { data, loading, error } = useDiagramQuery(
    { id: diagramId(diagramIdFromUrl || '') },
    { 
      skip: !diagramIdFromUrl || hasLoaded,
      // Custom error handling
      onError: (error) => {
        console.error('Failed to fetch diagram:', error);
        toast.error(`Failed to load diagram: ${error.message}`);
        setHasLoaded(true); // Prevent retry loop
      },
      // Custom success handling
      onCompleted: (data) => {
        if (!data.diagram && diagramIdFromUrl) {
          toast.error(`Diagram "${diagramIdFromUrl}" not found`);
          setHasLoaded(true); // Prevent retry
        }
      }
    }
  );

  // Load diagram data into store - delay until after mount
  useEffect(() => {
    if (!loading && !hasLoaded && diagramIdFromUrl && data?.diagram) {
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
          let { nodes, handles, arrows, persons } = diagramToStoreMaps(domainDiagram);
          
          // Deduplicate arrows based on source/target
          const arrowMap = new Map<string, typeof arrows extends Map<any, infer V> ? V : never>();
          arrows.forEach((arrow, id) => {
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

          // Mark as loaded after store is updated
          setHasLoaded(true);
          
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
      
      // Cleanup timer on unmount
      return () => clearTimeout(loadTimer);
    }
  }, [data, loading, hasLoaded, diagramIdFromUrl, diagramFormatFromUrl]);

  return {
    isLoading: loading || isLoading,
    hasLoaded,
    diagramId: diagramIdFromUrl,
    diagramFormat: diagramFormatFromUrl,
    error
  };
}