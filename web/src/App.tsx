// Application root component
import React, { Suspense, useEffect } from 'react';
import { ReactFlowProvider } from '@xyflow/react';
import { TopBar, Sidebar } from './components/layout';
import { useExecution, useUnifiedStore } from './hooks';
import { CanvasProvider, useCanvasOperationsContext, useCanvasUIState } from './contexts/CanvasContext';

// Lazy load heavy components
const LazyDiagramCanvas = React.lazy(() => import('./components/diagram/canvas/DiagramCanvas'));
const LazyExecutionView = React.lazy(() => import('./components/execution/ExecutionView'));
const LazyToaster = React.lazy(() => import('sonner').then(module => ({ default: module.Toaster })));
const LazyInteractivePromptModal = React.lazy(() => import('./components/execution/InteractivePrompt/InteractivePromptModal'));

// Inner component that uses React Flow hooks
function AppContent() {
  const { activeCanvas } = useCanvasUIState();
  const { setReadOnly } = useCanvasOperationsContext();
  // Create the main execution connection (GraphQL-based)
  const execution = useExecution({ autoConnect: true });
  
  useEffect(() => {
    const checkMonitorMode = () => {
      const params = new URLSearchParams(window.location.search);
      const monitorParam = params.get('monitor') === 'true';
      setReadOnly?.(monitorParam);

      if (monitorParam) {
        document.title = 'DiPeO - Monitor Mode';
      } else {
        document.title = 'DiPeO';
      }
    };

    // Check on mount
    checkMonitorMode();

    // Listen for URL changes
    const handleUrlChange = () => checkMonitorMode();
    window.addEventListener('popstate', handleUrlChange);

    return () => {
      window.removeEventListener('popstate', handleUrlChange);
    };
  }, [setReadOnly]);

  // Don't create another connection - use the existing execution instance
  
  return (
    <div className="h-screen flex flex-col">
        {/* Top Bar */}
        <TopBar />

        {/* Main Content Area */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left Sidebar */}
          <div className="w-64 border-r flex-shrink-0">
            <Sidebar position="left" />
          </div>

          {/* Right Content - Canvas switching based on activeCanvas */}
          <div className="flex-1 flex flex-col">
            {activeCanvas === 'main' ? (
              <Suspense fallback={
                <div className="h-full bg-gradient-to-br from-slate-50 to-sky-100 flex items-center justify-center">
                  <div className="text-gray-500 animate-pulse">Loading diagram canvas...</div>
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
        
        
        {/* Interactive Prompt Modal */}
        {execution.interactivePrompt && (
          <Suspense fallback={null}>
            <LazyInteractivePromptModal
              prompt={execution.interactivePrompt}
              onResponse={(response) => {
                execution.respondToPrompt(response);
              }}
              onCancel={() => {
                execution.respondToPrompt('');
              }}
            />
          </Suspense>
        )}
      </div>
  );
}

// Main App component that provides ReactFlowProvider
function App() {
  // Set up keyboard shortcuts for undo/redo
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + Z for undo
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        useUnifiedStore.getState().undo();
      }
      // Ctrl/Cmd + Y or Ctrl/Cmd + Shift + Z for redo
      if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault();
        useUnifiedStore.getState().redo();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <ReactFlowProvider>
      <CanvasProvider>
        <AppContent />
      </CanvasProvider>
    </ReactFlowProvider>
  );
}

export default App;