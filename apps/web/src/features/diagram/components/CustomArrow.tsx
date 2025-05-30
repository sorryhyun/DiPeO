import React from 'react';
import { CustomArrow as CustomArrowBase } from '@repo/diagram-ui';
import { useArrowDataUpdater } from '@/shared/hooks/useStoreSelectors';

// Re-export types from diagram-ui package
export type { CustomArrowProps } from '@repo/diagram-ui';

// Wrapper component that integrates with app stores
export const CustomArrow = React.memo((props: Parameters<typeof CustomArrowBase>[0]) => {
  const updateArrowData = useArrowDataUpdater();
  
  return (
    <CustomArrowBase
      {...props}
      onUpdateData={updateArrowData}
    />
  );
});

CustomArrow.displayName = 'CustomArrowWrapper';