import { useEffect, useState } from 'react';
import { useGetDiagramQuery } from '@/__generated__/graphql';
import { useUnifiedStore } from '@/core/store/unifiedStore';
import { toast } from 'sonner';
import { diagramId } from '@/core/types';
import { domainToReactDiagram, diagramToStoreMaps } from '@/graphql/types';

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

  // Load diagram data into store
  useEffect(() => {
    if (!loading && data?.diagram && !hasLoaded && diagramIdFromUrl) {
      setIsLoading(true);
      
      try {
        // Convert GraphQL diagram to domain format (identity mapping since GraphQL IS domain)
        // Add missing count fields that aren't in the query result
        const diagramWithCounts = {
          ...data.diagram,
          nodeCount: data.diagram.nodes.length,
          arrowCount: data.diagram.arrows.length,
          personCount: data.diagram.persons.length
        };
        const reactDiagram = domainToReactDiagram(diagramWithCounts);
        
        // Clear existing data
        const store = useUnifiedStore.getState();
        store.clearAll();
        
        // Convert arrays to Maps for the store
        const { nodes, handles, arrows, persons, apiKeys } = diagramToStoreMaps(reactDiagram);
        
        // Update store with all data at once
        useUnifiedStore.setState(state => ({
          nodes,
          handles,
          arrows,
          persons,
          apiKeys,
          nodesArray: reactDiagram.nodes || [],
          arrowsArray: reactDiagram.arrows || [],
          personsArray: reactDiagram.persons || [],
          dataVersion: state.dataVersion + 1  // Increment to trigger re-render
        }));
        
        // Mark as loaded
        setHasLoaded(true);
        
        // Show success message
        const diagramName = reactDiagram.metadata?.name || 'Unnamed diagram';
        toast.success(`Loaded diagram: ${diagramName}`);
        
      } catch (err) {
        console.error('Failed to load diagram:', err);
        toast.error('Failed to load diagram');
      } finally {
        setIsLoading(false);
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