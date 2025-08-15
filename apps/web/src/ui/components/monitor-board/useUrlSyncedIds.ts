import { useEffect, useState, useCallback, useRef } from 'react';

export function useUrlSyncedIds() {
  // Track if IDs were explicitly provided in URL
  const hasExplicitIds = useRef<boolean>(false);
  
  const [executionIds, setExecutionIds] = useState<string[]>(() => {
    const params = new URLSearchParams(window.location.search);
    const idsParam = params.get('ids');
    if (idsParam) {
      hasExplicitIds.current = true;
      // Deduplicate IDs from URL
      const ids = idsParam.split(',').filter(Boolean);
      return [...new Set(ids)];
    }
    return [];
  });

  // Sync state to URL
  useEffect(() => {
    // Don't sync to URL if these are auto-fetched IDs (no explicit IDs were provided)
    if (!hasExplicitIds.current && executionIds.length > 0) {
      return; // Skip URL update for auto-fetched IDs
    }
    
    const params = new URLSearchParams(window.location.search);
    const currentIds = params.get('ids');
    const newIdsString = executionIds.join(',');
    
    if (executionIds.length === 0 && currentIds) {
      // Remove the ids param if no executions
      params.delete('ids');
    } else if (executionIds.length > 0 && currentIds !== newIdsString) {
      // Update the ids param
      params.set('ids', newIdsString);
    } else {
      // No change needed
      return;
    }
    
    // Update URL without reload
    const newUrl = `${window.location.pathname}${params.toString() ? '?' + params.toString() : ''}`;
    window.history.replaceState({}, '', newUrl);
  }, [executionIds]);

  const addExecutionId = useCallback((id: string) => {
    // When user manually adds an ID, mark as explicit
    hasExplicitIds.current = true;
    setExecutionIds(prev => {
      if (prev.includes(id)) return prev;
      return [...prev, id];
    });
  }, []);

  const removeExecutionId = useCallback((id: string) => {
    setExecutionIds(prev => prev.filter(existingId => existingId !== id));
  }, []);

  const reorderExecutionIds = useCallback((fromIndex: number, toIndex: number) => {
    setExecutionIds(prev => {
      const newIds = [...prev];
      const [removed] = newIds.splice(fromIndex, 1);
      if (removed) {
        newIds.splice(toIndex, 0, removed);
      }
      return newIds;
    });
  }, []);

  const clearAll = useCallback(() => {
    setExecutionIds([]);
  }, []);

  // Bulk update for auto-fetched executions
  const setAutoFetchedIds = useCallback((ids: string[]) => {
    // Only update if we're in auto-fetch mode (no explicit IDs)
    if (!hasExplicitIds.current) {
      setExecutionIds(prev => {
        // Deduplicate the incoming IDs first
        const uniqueIds = [...new Set(ids)];
        
        // If nothing changed, return prev to avoid re-render
        if (uniqueIds.length === prev.length && uniqueIds.every((id, i) => id === prev[i])) {
          return prev;
        }
        
        return uniqueIds;
      });
    }
  }, []);

  return {
    executionIds,
    addExecutionId,
    removeExecutionId,
    reorderExecutionIds,
    clearAll,
    setAutoFetchedIds,
    hasExplicitIds: hasExplicitIds.current,
  };
}