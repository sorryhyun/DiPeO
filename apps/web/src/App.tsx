// Application root component
import React, { Suspense, useEffect } from 'react';
import { ReactFlowProvider } from '@xyflow/react';
import { TopBar, Sidebar } from '@/features/layout';
import { useExecutionMonitor } from '@/state/hooks/useExecutionMonitor';
import { useDiagramStore } from '@/state/stores';
import { useUIState } from '@/state/hooks/useStoreSelectors';
import { useDiagramRunner } from '@/features/runtime/hooks/useDiagramRunner';

// Lazy load heavy components
const LazyDiagramCanvas = React.lazy(() => import('@/features/canvas').then(module => ({ default: module.DiagramCanvas })));
const LazyMemoryCanvas = React.lazy(() => import('@/features/memory').then(module => ({ default: module.MemoryCanvas })));
const LazyToaster = React.lazy(() => import('sonner').then(module => ({ default: module.Toaster })));
const LazyWebSocketTest = React.lazy(() => import('@/features/runtime/components/WebSocketTest').then(module => ({ default: module.WebSocketTest })));
const LazyInteractivePromptModal = React.lazy(() => import('@/features/runtime/components/InteractivePromptModal'));

function App() {
  const { setReadOnly } = useDiagramStore();
  const { activeCanvas } = useUIState();
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
            {activeCanvas === 'diagram' ? (
              <Suspense fallback={
                <div className="h-full bg-gradient-to-br from-slate-50 to-sky-100 flex items-center justify-center">
                  <div className="text-gray-500 animate-pulse">Loading diagram canvas...</div>
                </div>
              }>
                <LazyDiagramCanvas />
              </Suspense>
            ) : (
              <Suspense fallback={
                <div className="h-full bg-gradient-to-b from-slate-700 to-slate-900 flex items-center justify-center">
                  <div className="text-gray-400 animate-pulse">Loading memory canvas...</div>
                </div>
              }>
                <LazyMemoryCanvas />
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