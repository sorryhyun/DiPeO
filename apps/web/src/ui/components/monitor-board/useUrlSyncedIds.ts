import { useEffect, useState, useCallback } from 'react';

export function useUrlSyncedIds() {
  const [executionIds, setExecutionIds] = useState<string[]>(() => {
    const params = new URLSearchParams(window.location.search);
    const idsParam = params.get('ids');
    return idsParam ? idsParam.split(',').filter(Boolean) : [];
  });

  // Sync state to URL
  useEffect(() => {
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

  return {
    executionIds,
    addExecutionId,
    removeExecutionId,
    reorderExecutionIds,
    clearAll,
  };
}