import React, { Suspense } from 'react';

const LazyExecutionView = React.lazy(() => import('../components/execution/ExecutionView'));

export function ExecutionPage() {
  return (
    <Suspense fallback={
      <div className="h-full bg-black flex items-center justify-center">
        <div className="text-gray-400 animate-pulse">Loading execution view...</div>
      </div>
    }>
      <LazyExecutionView />
    </Suspense>
  );
}
