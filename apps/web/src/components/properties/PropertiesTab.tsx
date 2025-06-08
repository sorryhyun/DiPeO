import React, { Suspense } from 'react';
import { useNodes, useArrows, usePersons, useSelectedElement } from '@/hooks/useStoreSelectors';
import { LoadingFallback } from '@/components/ui/feedback';

// Lazy load the properties renderer
const PropertiesRenderer = React.lazy(() => import('./renderers/PropertiesRenderer'));

export const PropertiesTab: React.FC = () => {
  const { nodes } = useNodes();
  const { arrows } = useArrows();
  const { persons } = usePersons();
  
  const {
    selectedPersonId,
    selectedNodeId,
    selectedArrowId,
  } = useSelectedElement();

  return (
    <div className="flex-1 overflow-y-auto">
      <Suspense fallback={<LoadingFallback />}>
        <PropertiesRenderer
          selectedNodeId={selectedNodeId}
          selectedArrowId={selectedArrowId}
          selectedPersonId={selectedPersonId}
          nodes={nodes}
          arrows={arrows}
          persons={persons}
        />
      </Suspense>
    </div>
  );
};

export default PropertiesTab;