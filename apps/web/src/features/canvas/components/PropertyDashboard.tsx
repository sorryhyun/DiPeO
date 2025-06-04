import React, { Suspense } from 'react';
import { useNodes, useArrows, usePersons, useSelectedElement } from '@/state/hooks/useStoreSelectors';

// Lazy load the properties renderer
const PropertiesRenderer = React.lazy(() => import('@/features/properties/components/PropertiesRenderer'));

const PropertyDashboard: React.FC = () => {
  const { nodes } = useNodes();
  const { arrows } = useArrows();
  const { persons } = usePersons();
  
  const {
    selectedPersonId,
    selectedNodeId,
    selectedArrowId,
  } = useSelectedElement();

  return (
    <div className="h-full bg-white flex flex-col">
      <div className="flex items-center justify-between px-4 py-2 bg-gray-100 border-b">
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-gray-700">Properties</span>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto">
        <Suspense fallback={
          <div className="p-4 space-y-4">
            <div className="h-8 bg-gray-200 rounded animate-pulse"></div>
            <div className="space-y-2">
              <div className="h-4 bg-gray-100 rounded w-1/2 animate-pulse"></div>
              <div className="h-10 bg-gray-100 rounded animate-pulse"></div>
            </div>
            <div className="space-y-2">
              <div className="h-4 bg-gray-100 rounded w-1/2 animate-pulse"></div>
              <div className="h-10 bg-gray-100 rounded animate-pulse"></div>
            </div>
          </div>
        }>
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
    </div>
  );
};

export default PropertyDashboard;