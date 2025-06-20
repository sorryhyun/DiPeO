import React, { Suspense } from 'react';
import { useCanvas } from '@/features/diagram-editor/hooks';
import { useUnifiedStore } from '@/core/store/unifiedStore';
import { LoadingFallback } from '@/shared/components/ui/feedback';
import { personId, DomainPerson } from '@/core/types';

// Lazy load the properties renderer
const PropertiesRenderer = React.lazy(() => import('./renderers/PropertiesRenderer'));

export const PropertiesTab: React.FC = () => {
  const { nodes, arrows, personsArray } = useCanvas();
  const { selectedId, selectedType, persons: personsMap } = useUnifiedStore();
  
  // Derive selected IDs based on selectedType
  const selectedNodeId = selectedType === 'node' ? selectedId : null;
  const selectedArrowId = selectedType === 'arrow' ? selectedId : null;
  const selectedPersonId = selectedType === 'person' ? selectedId : null;
  
  // Convert persons array to person objects
  const personsData = personsArray;
  
  // Pass the actual arrows data from canvas
  const arrowsData = arrows;

  return (
    <div className="flex-1 overflow-y-auto">
      <Suspense fallback={<LoadingFallback />}>
        <PropertiesRenderer
          selectedNodeId={selectedNodeId}
          selectedArrowId={selectedArrowId}
          selectedPersonId={selectedPersonId}
          nodes={nodes}
          arrows={arrowsData}
          persons={personsData}
        />
      </Suspense>
    </div>
  );
};

export default PropertiesTab;