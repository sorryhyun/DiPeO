import React from 'react';
import { CustomArrow as CustomArrowBase, ArrowData } from './Arrow';
import { useArrowDataUpdater } from '@/hooks/useStoreSelectors';
import { arrowId } from '@/types';

// Re-export types from local ui-components
export type { CustomArrowProps, ArrowData } from './Arrow';

// Wrapper component that integrates with app stores
export const CustomArrow = React.memo((props: Parameters<typeof CustomArrowBase>[0]) => {
  const updateArrowData = useArrowDataUpdater();
  
  // Create a type-safe wrapper that updates arrow data in the store
  const handleUpdateData = React.useCallback((edgeId: string, data: Partial<ArrowData> | undefined) => {
    if (!data || !updateArrowData) return;
    
    // Update the arrow's data property with the new ArrowData
    updateArrowData(arrowId(edgeId), {
      data: data as Record<string, unknown>
    });
  }, [updateArrowData]);
  
  return (
    <CustomArrowBase
      {...props}
      onUpdateData={handleUpdateData}
    />
  );
});

CustomArrow.displayName = 'CustomArrowWrapper';