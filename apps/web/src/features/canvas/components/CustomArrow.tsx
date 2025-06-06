import React from 'react';
import { CustomArrow as CustomArrowBase } from './ui-components/Arrow';
import { useArrowDataUpdater } from '@/state/hooks/useStoreSelectors';
import { ArrowData } from '../../../types';

// Re-export types from local ui-components
export type { CustomArrowProps } from './ui-components/Arrow';

// Wrapper component that integrates with app stores
export const CustomArrow = React.memo((props: Parameters<typeof CustomArrowBase>[0]) => {
  const updateArrowData = useArrowDataUpdater();
  
  // Create a type-safe wrapper that converts diagram-ui ArrowData to engine-model ArrowData
  const handleUpdateData = React.useCallback((edgeId: string, data: Partial<ArrowData>) => {
    // Filter and convert data to match engine-model ArrowData type
    const coreModelData: Partial<ArrowData> = {};
    
    // Copy compatible fields
    if (data.label !== undefined) coreModelData.label = data.label;
    if (data.controlPointOffsetX !== undefined) coreModelData.controlPointOffsetX = data.controlPointOffsetX;
    if (data.controlPointOffsetY !== undefined) coreModelData.controlPointOffsetY = data.controlPointOffsetY;
    if (data.loopRadius !== undefined) coreModelData.loopRadius = data.loopRadius;
    
    // Handle branch conversion - only accept valid values
    if (data.branch !== undefined) {
      if (data.branch === 'true' || data.branch === 'false') {
        coreModelData.branch = data.branch;
      }
    }
    
    // Handle contentType conversion - only accept valid values
    if (data.contentType !== undefined) {
      if (data.contentType === 'raw_text' || 
          data.contentType === 'variable_in_object' || 
          data.contentType === 'conversation_state' ||
          data.contentType === 'empty' ||
          data.contentType === 'generic') {
        coreModelData.contentType = data.contentType;
      }
    }
    
    updateArrowData?.(edgeId, coreModelData);
  }, [updateArrowData]);
  
  return (
    <CustomArrowBase
      {...props}
      onUpdateData={handleUpdateData}
    />
  );
});

CustomArrow.displayName = 'CustomArrowWrapper';