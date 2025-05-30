// Application root component
import React, { Suspense, useEffect, useState } from 'react';
import { ReactFlowProvider } from '@xyflow/react';
import { Toaster, toast } from 'sonner';
import TopBar from './components/layout/TopBar';
import Sidebar from './components/layout/Sidebar';
import { PanelGroup, Panel, PanelResizeHandle } from 'react-resizable-panels';
import { DiagramCanvasSkeleton } from './components/skeletons/SkeletonComponents';
import { useExecutionMonitor } from './hooks/useExecutionMonitor';
import { DiagramProvider } from './contexts/DiagramContext';

// Lazy load heavy components
const DiagramCanvas = React.lazy(() => import('./components/diagram/Canvas'));
const IntegratedDashboard = React.lazy(() => import('./components/layout/IntegratedDashboard'));

function App() {
  const [isMonitorMode, setIsMonitorMode] = useState(false);
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const monitorParam = params.get('monitor') === 'true';
    setIsMonitorMode(monitorParam);

    if (monitorParam) {
      document.title = 'AgentDiagram - Monitor Mode';
    }
  }, []);

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
                    <DiagramCanvas />
                  </Suspense>
                </Panel>

                {/* Resizable Handle */}
                <PanelResizeHandle className="h-1 bg-gray-200 hover:bg-gray-300 cursor-row-resize" />

                {/* Dashboard Panel */}
                <Panel defaultSize={35} minSize={20}>
                  <Suspense fallback={<div className="h-full bg-white flex items-center justify-center animate-pulse"><div className="text-gray-500">Loading dashboard...</div></div>}>
                    <IntegratedDashboard />
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