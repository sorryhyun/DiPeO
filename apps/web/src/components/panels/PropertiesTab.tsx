import React, { Suspense } from 'react';
import { useNodes, useArrows, usePersons, useSelectedElement } from '@/state/hooks/useStoreSelectors';

// Lazy load the unified properties panel
const PropertiesPanel = React.lazy(() => import('../../../components/panels/PropertiesPanel'));

export const PropertiesTab: React.FC = () => {
  return (
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
        <PropertiesPanel />
      </Suspense>
    </div>
  );
};

export default PropertiesTab;