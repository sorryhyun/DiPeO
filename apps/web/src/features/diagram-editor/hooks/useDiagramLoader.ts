import { useEffect, useState } from 'react';
import { useGetDiagramQuery } from '@/__generated__/graphql';
import { useUnifiedStore } from '@/core/store/unifiedStore';
import { toast } from 'sonner';
import { diagramId, arrowId } from '@/core/types';
import { domainToReactDiagram, diagramToStoreMaps } from '@/graphql/types';
import { migrateArrowBranchData } from '../utils/arrowMigration';

/**
 * Hook that loads a diagram from the backend when a diagram ID is present in the URL
 */
export function useDiagramLoader() {
  const [isLoading, setIsLoading] = useState(false);
  const [hasLoaded, setHasLoaded] = useState(false);
  const [diagramIdFromUrl, setDiagramIdFromUrl] = useState<string | null>(null);

  // Check URL for diagram parameter
  useEffect(() => {
    const checkUrlParams = () => {
      const params = new URLSearchParams(window.location.search);
      const diagramParam = params.get('diagram');
      
      if (diagramParam && diagramParam !== diagramIdFromUrl) {
        setDiagramIdFromUrl(diagramParam);
        setHasLoaded(false); // Reset loaded state when diagram ID changes
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
  }, [diagramIdFromUrl]);

  // Query for diagram data
  const { data, loading, error } = useGetDiagramQuery({
    variables: { id: diagramId(diagramIdFromUrl || '') },
    skip: !diagramIdFromUrl || hasLoaded,
    fetchPolicy: 'cache-first'
  });

  // Load diagram data into store - delay until after mount
  useEffect(() => {
    if (!loading && !hasLoaded && diagramIdFromUrl) {
      // Check if diagram was not found
      if (data && !data.diagram) {
        toast.error(`Diagram "${diagramIdFromUrl}" not found`);
        setHasLoaded(true); // Prevent retry
        return;
      }
      
      if (data?.diagram) {
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
          const reactDiagram = domainToReactDiagram(diagramWithCounts);
          
          // Convert arrays to Maps for the store
          const { nodes, handles, arrows, persons } = diagramToStoreMaps(reactDiagram);
          
          // Migrate arrow data to ensure condition arrows have branch data
          const migratedArrows = migrateArrowBranchData(
            Array.from(arrows.values()),
            nodes
          );
          
          // Update arrows map with migrated data
          migratedArrows.forEach(arrow => {
            arrows.set(arrowId(arrow.id), arrow);
          });
          
          // Update store with all data at once in a single transaction
          const store = useUnifiedStore.getState();
          store.transaction(() => {
            // First clear existing data
            store.clearAll();
            
            // Then set all new data in one atomic update
            useUnifiedStore.setState(state => ({
              nodes,
              handles,
              arrows,
              persons,
              nodesArray: reactDiagram.nodes || [],
              arrowsArray: migratedArrows,
              personsArray: reactDiagram.persons || [],
              dataVersion: state.dataVersion + 1  // Single increment
            }));
          });

          
          // Mark as loaded after store is updated
          setHasLoaded(true);
          
          // Show success message
          const diagramName = reactDiagram.metadata?.name || 'Unnamed diagram';
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
    }
  }, [data, loading, hasLoaded, diagramIdFromUrl]);

  // Handle errors
  useEffect(() => {
    if (error && diagramIdFromUrl) {
      console.error('Failed to fetch diagram:', error);
      toast.error(`Failed to load diagram: ${error.message}`);
      setHasLoaded(true); // Prevent retry loop
    }
  }, [error, diagramIdFromUrl]);

  return {
    isLoading: loading || isLoading,
    hasLoaded,
    diagramId: diagramIdFromUrl,
    error
  };
}