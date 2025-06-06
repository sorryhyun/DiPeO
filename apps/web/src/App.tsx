// Application root component
import React, { Suspense, useEffect } from 'react';
import { ReactFlowProvider } from '@xyflow/react';
import { TopBar, Sidebar } from './components/layout';
import { useExecutionMonitor } from './hooks/useExecutionMonitor';
import { useConsolidatedUIStore, useDiagramStore } from './stores';
import { useDiagramRunner } from './hooks/useDiagramRunner';

// Lazy load heavy components
const LazyDiagramCanvas = React.lazy(() => import('./components/canvas/DiagramCanvas'));
const LazyMemoryCanvas = React.lazy(() => import('./components/panels/MemoryCanvas').then(module => ({ default: module.MemoryCanvas })));
const LazyExecutionView = React.lazy(() => import('./components/layout/ExecutionView'));
const LazyToaster = React.lazy(() => import('sonner').then(module => ({ default: module.Toaster })));
const LazyWebSocketTest = React.lazy(() => import('./components/panels/WebSocketTest').then(module => ({ default: module.WebSocketTest })));
const LazyInteractivePromptModal = React.lazy(() => import('./components/panels/InteractivePromptModal'));

function App() {
  const { activeCanvas } = useConsolidatedUIStore();
  const { setReadOnly } = useDiagramStore();
  const { interactivePrompt, sendInteractiveResponse, cancelInteractivePrompt } = useDiagramRunner();
  const params = new URLSearchParams(window.location.search);
  const useWebSocket = params.get('useWebSocket') === 'true' || params.get('websocket') === 'true';
  
  useEffect(() => {
    const checkMonitorMode = () => {
      const params = new URLSearchParams(window.location.search);
      const monitorParam = params.get('monitor') === 'true';
      setReadOnly(monitorParam);

      if (monitorParam) {
        document.title = 'AgentDiagram - Monitor Mode';
      } else {
        document.title = 'AgentDiagram';
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

  // Use execution monitor - it will automatically use WebSocket when available
  useExecutionMonitor();
  
  // Show WebSocket status when enabled via feature flag
  useEffect(() => {
    if (useWebSocket) {
      console.log('[App] WebSocket monitoring enabled via feature flag');
    }
  }, [useWebSocket]);
  
  return (
    <ReactFlowProvider>
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
            ) : activeCanvas === 'memory' ? (
              <Suspense fallback={
                <div className="h-full bg-gradient-to-b from-slate-700 to-slate-900 flex items-center justify-center">
                  <div className="text-gray-400 animate-pulse">Loading memory canvas...</div>
                </div>
              }>
                <LazyMemoryCanvas />
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
        
        {/* WebSocket Test Component - Enable with ?websocket=true */}
        {new URLSearchParams(window.location.search).get('websocket') === 'true' && (
          <Suspense fallback={null}>
            <LazyWebSocketTest enabled={true} />
          </Suspense>
        )}
        
        {/* Interactive Prompt Modal */}
        {interactivePrompt && (
          <Suspense fallback={null}>
            <LazyInteractivePromptModal
              prompt={interactivePrompt}
              onResponse={sendInteractiveResponse}
              onCancel={cancelInteractivePrompt}
            />
          </Suspense>
        )}
      </div>
    </ReactFlowProvider>
  );
}

export default App;