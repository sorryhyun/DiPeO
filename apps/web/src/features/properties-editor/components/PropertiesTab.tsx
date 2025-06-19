import React, { Suspense } from 'react';
import { useCanvasOperations } from '@/features/diagram-editor/hooks';
import { LoadingFallback } from '@/shared/components/ui/feedback';

// Lazy load the properties renderer
const PropertiesRenderer = React.lazy(() => import('./renderers/PropertiesRenderer'));

export const PropertiesTab: React.FC = () => {
  const canvas = useCanvasOperations();
  const { nodes, arrows, selectedId, selectedType } = canvas;
  
  // Derive selected IDs based on selectedType
  const selectedNodeId = selectedType === 'node' ? selectedId : null;
  const selectedArrowId = selectedType === 'arrow' ? selectedId : null;
  const selectedPersonId = selectedType === 'person' ? selectedId : null;
  
  // Convert person IDs to person objects
  const personsData = canvas.persons.map(id => canvas.getPersonById(id)).filter(Boolean);
  
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