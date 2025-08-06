import React, { Suspense, useEffect } from 'react';
import { ReactFlowProvider } from '@xyflow/react';
import { TopBar, Sidebar } from './components/common/layout';
import GlobalKeyboardHandler from './components/common/GlobalKeyboardHandler';
import { CanvasProvider, useCanvasState, useCanvasOperations } from './shared/contexts/CanvasContext';
import { useUIOperations } from './core/store/hooks';
import { setupExecutionUISync } from './core/store/middleware/executionUISync';

const LazyDiagramCanvas = React.lazy(() => import('./components/diagram/DiagramCanvas'));
const LazyExecutionView = React.lazy(() => import('./components/execution/ExecutionView'));
const LazyToaster = React.lazy(() => import('sonner').then(module => ({ default: module.Toaster })));
const LazyInteractivePromptModal = React.lazy(() => import('./components/execution/InteractivePromptModal'));

function AppContent() {
  const { activeCanvas } = useCanvasState();
  const { executionOps } = useCanvasOperations();
  const { setActiveCanvas: _setActiveCanvas } = useUIOperations();
  
  
  useEffect(() => {
    const unsubscribe = setupExecutionUISync();
    return unsubscribe;
  }, []);
  
  useEffect(() => {
    document.title = 'DiPeO';
  }, []);

  
  return (
    <div className="h-screen flex flex-col">
        <TopBar />

        <div className="flex-1 flex overflow-hidden">
          <div className="w-80 border-r border-border flex-shrink-0 bg-background-secondary">
            <Sidebar position="left" />
          </div>

          <div className="flex-1 flex flex-col">
            {activeCanvas === 'main' ? (
              <Suspense fallback={
                <div className="h-full diagram-canvas flex items-center justify-center">
                  <div className="text-text-secondary animate-pulse">Loading diagram canvas...</div>
                </div>
              }>
                <LazyDiagramCanvas />
              </Suspense>
            ) : activeCanvas === 'execution' ? (
              <Suspense fallback={
                <div className="h-full bg-black flex items-center justify-center">
                  <div className="text-gray-400 animate-pulse">Loading execution view...</div>
                </div>
              }>
                <LazyExecutionView />
              </Suspense>
            ) : (
              <Suspense fallback={
                <div className="h-full bg-black flex items-center justify-center">
                  <div className="text-gray-400 animate-pulse">Loading execution view...</div>
                </div>
              }>
                <LazyExecutionView />
              </Suspense>
            )}
          </div>
        </div>

        <Suspense fallback={null}>
          <LazyToaster richColors position="bottom-center" />
        </Suspense>
        
        
        {executionOps?.interactivePrompt && (
          <Suspense fallback={null}>
            <LazyInteractivePromptModal
              prompt={executionOps.interactivePrompt}
              onResponse={(nodeId: string, response: string) => {
                executionOps.respondToPrompt(response);
              }}
              onCancel={() => {
                executionOps.respondToPrompt('');
              }}
            />
          </Suspense>
        )}
      </div>
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