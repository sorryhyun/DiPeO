// Refactored PropertiesTab using the new PropertiesRenderer
// This component is now much simpler as it doesn't need to pass props
import React, { Suspense } from 'react';
import { LoadingFallback } from '@/components/ui/feedback';

// Lazy load the refactored properties renderer
const PropertiesRenderer = React.lazy(() => import('./renderers/PropertiesRenderer.refactored'));

/**
 * PropertiesTab - Container for properties renderer
 * Now just provides a suspense boundary, no prop drilling needed
 */
export const PropertiesTab: React.FC = () => {
  return (
    <div className="flex-1 overflow-y-auto">
      <Suspense fallback={<LoadingFallback />}>
        <PropertiesRenderer />
      </Suspense>
    </div>
  );
};

export default PropertiesTab;