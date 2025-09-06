import React, { Suspense } from 'react';

const LazyDiagramCanvas = React.lazy(() => import('../components/diagram/DiagramCanvas'));

export function DiagramPage() {
  return (
    <Suspense fallback={
      <div className="h-full diagram-canvas flex items-center justify-center">
        <div className="text-text-secondary animate-pulse">Loading diagram canvas...</div>
      </div>
    }>
      <LazyDiagramCanvas />
    </Suspense>
  );
}
