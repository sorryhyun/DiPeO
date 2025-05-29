// Application root component
import React, { Suspense, useEffect } from 'react';
import { ReactFlowProvider } from '@xyflow/react';
import { Toaster, toast } from 'sonner';
import TopBar from './components/layout/TopBar';
import Sidebar from './components/layout/Sidebar';
import { PanelGroup, Panel, PanelResizeHandle } from 'react-resizable-panels';
import { DiagramCanvasSkeleton } from './components/skeletons/SkeletonComponents';
import { useSearchParams } from 'react-router-dom';
import { useExecutionMonitor } from './hooks/useExecutionMonitor';

// Lazy load heavy components
const DiagramCanvas = React.lazy(() => import('./components/diagram/Canvas'));
const IntegratedDashboard = React.lazy(() => import('./components/layout/IntegratedDashboard'));

function App() {
  const [searchParams] = useSearchParams();
  const isMonitorMode = searchParams.get('monitor') === 'true';
    useEffect(() => {
    if (isMonitorMode) {
      toast.info('Monitor Mode Active - Waiting for external executions...', {
        duration: 5000,
        icon: '👁️'
      });

      // You could also set a special UI state
      document.title = 'AgentDiagram - Monitor Mode';
    }
  }, [isMonitorMode]);

  useExecutionMonitor();
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
    </ReactFlowProvider>
  );
}

export default App;