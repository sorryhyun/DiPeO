// Application root component
import React, { Suspense, useEffect } from 'react';
import { ReactFlowProvider } from '@xyflow/react';
import { Toaster } from 'sonner';
import { TopBar, Sidebar } from '@/features/layout';
import { PanelGroup, Panel, PanelResizeHandle } from 'react-resizable-panels';
import { DiagramCanvasSkeleton } from '@/shared/components/skeletons/SkeletonComponents';
import { useExecutionMonitor } from '@/core/hooks/useExecutionMonitor';
import { DiagramProvider } from '@/core/contexts/DiagramContext';
import { useConsolidatedDiagramStore } from '@/core/stores/consolidatedDiagramStore';

// Lazy load heavy components
const LazyDiagramCanvas = React.lazy(() => import('@/features/canvas/components/Canvas'));
const LazyIntegratedDashboard = React.lazy(() => import('@/features/layout/components/IntegratedDashboard'));

function App() {
  const { setMonitorMode } = useConsolidatedDiagramStore();
  
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

            {/* Right Content - Canvas + Dashboard */}
            <div className="flex-1 flex flex-col">
              <PanelGroup direction="vertical">
                {/* Canvas Panel */}
                <Panel defaultSize={65} minSize={30}>
                  <Suspense fallback={<DiagramCanvasSkeleton />}>
                    <LazyDiagramCanvas />
                  </Suspense>
                </Panel>

                {/* Resizable Handle */}
                <PanelResizeHandle className="h-1 bg-gray-200 hover:bg-gray-300 cursor-row-resize" />

                {/* Dashboard Panel */}
                <Panel defaultSize={35} minSize={20}>
                  <Suspense fallback={<div className="h-full bg-white flex items-center justify-center animate-pulse"><div className="text-gray-500">Loading dashboard...</div></div>}>
                    <LazyIntegratedDashboard />
                  </Suspense>
                </Panel>
              </PanelGroup>
            </div>
          </div>
        </div>

        <Toaster richColors position="top-center" />
      </DiagramProvider>
    </ReactFlowProvider>
  );
}

export default App;