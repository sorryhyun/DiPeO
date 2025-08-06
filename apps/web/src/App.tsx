import React, { Suspense, useEffect } from 'react';
import { ReactFlowProvider } from '@xyflow/react';
import { GlobalKeyboardHandler } from './ui/components/common/GlobalKeyboardHandler';
import { CanvasProvider } from './domain/diagram/contexts';
import { MainLayout } from './ui/layouts';

const LazyToaster = React.lazy(() => import('sonner').then(module => ({ default: module.Toaster })));

function AppContent() {
  useEffect(() => {
    document.title = 'DiPeO';
  }, []);

  return (
    <>
      <MainLayout />
      
      <Suspense fallback={null}>
        <LazyToaster richColors position="bottom-center" />
      </Suspense>
    </>
  );
}

function App() {
  return (
    <ReactFlowProvider>
      <CanvasProvider>
        <GlobalKeyboardHandler />
        <AppContent />
      </CanvasProvider>
    </ReactFlowProvider>
  );
}

export default App;