import React, { Suspense } from 'react';
import { useCanvas } from '@/hooks/useCanvas';
import { LoadingFallback } from '@/components/ui/feedback';

// Lazy load the properties renderer
const PropertiesRenderer = React.lazy(() => import('./renderers/PropertiesRenderer'));

export const PropertiesTab: React.FC = () => {
  const { nodes, arrows, persons, selectedId, selectedType } = useCanvas();
  
  // Derive selected IDs based on selectedType
  const selectedNodeId = selectedType === 'node' ? selectedId : null;
  const selectedArrowId = selectedType === 'arrow' ? selectedId : null;
  const selectedPersonId = selectedType === 'person' ? selectedId : null;

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