// Application root component
import React, { Suspense, useEffect } from 'react';
import { ReactFlowProvider } from '@xyflow/react';
import { TopBar, Sidebar } from '@/features/layout';
import { useExecutionMonitor } from '@/global/hooks/useExecutionMonitor';
import { DiagramProvider } from '@/global/contexts/DiagramContext';
import { useMonitorStore } from '@/global/stores';
import { useUIState } from '@/global/hooks/useStoreSelectors';

// Lazy load heavy components
const LazyDiagramCanvas = React.lazy(() => import('@/diagramCanvas').then(module => ({ default: module.DiagramCanvas })));
const LazyMemoryCanvas = React.lazy(() => import('@/memoryCanvas').then(module => ({ default: module.MemoryCanvas })));
const LazyToaster = React.lazy(() => import('sonner').then(module => ({ default: module.Toaster })));

function App() {
  const { setMonitorMode } = useMonitorStore();
  const { activeCanvas } = useUIState();
  
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const monitorParam = params.get('monitor') === 'true';
    setMonitorMode(monitorParam);

    if (monitorParam) {
      document.title = 'AgentDiagram - Monitor Mode';
    }
  }, [setMonitorMode]);

  useExecutionMonitor();
  return (
    <ReactFlowProvider>
      <DiagramProvider>
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
        </div>

        <Suspense fallback={null}>
          <LazyToaster richColors position="top-center" />
        </Suspense>
      </DiagramProvider>
    </ReactFlowProvider>
  );
}

export default App;