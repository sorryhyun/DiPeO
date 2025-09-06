import React, { Suspense } from 'react';
import { TopBar, Sidebar } from '../components/common/layout';
import { useCanvasState, useCanvasOperations } from '../../domain/diagram/contexts';
import { useUIState } from '../../infrastructure/store/hooks';
import { useMonitorBoardMode } from '../components/monitor-board/useMonitorBoardMode';

const LazyDiagramCanvas = React.lazy(() => import('../components/diagram/DiagramCanvas'));
const LazyExecutionView = React.lazy(() => import('../components/execution/ExecutionView'));
const LazyExecutionBoardView = React.lazy(() => import('../components/monitor-board/ExecutionBoardView'));
const LazyInteractivePromptModal = React.lazy(() => import('../components/execution/InteractivePromptModal'));

interface MainLayoutProps {
  children?: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  const { activeCanvas } = useCanvasState();
  const { executionOps } = useCanvasOperations();
  const { isMonitorMode } = useUIState();
  const { isMonitorBoard, isSingleMonitor } = useMonitorBoardMode();

  return (
    <div className="h-screen flex flex-col">
      <TopBar />

      <div className="flex-1 flex overflow-hidden">
        {!isMonitorMode && (
          <div className="w-80 border-r border-border flex-shrink-0 bg-background-secondary">
            <Sidebar position="left" />
          </div>
        )}

        <div className="flex-1 flex flex-col">
          {children || (
            isMonitorBoard ? (
              <Suspense fallback={
                <div className="h-full bg-gray-950 flex items-center justify-center">
                  <div className="text-gray-400 animate-pulse">Loading monitor board...</div>
                </div>
              }>
                <LazyExecutionBoardView />
              </Suspense>
            ) : isSingleMonitor || activeCanvas === 'execution' ? (
              <Suspense fallback={
                <div className="h-full bg-black flex items-center justify-center">
                  <div className="text-gray-400 animate-pulse">Loading execution view...</div>
                </div>
              }>
                <LazyExecutionView />
              </Suspense>
            ) : activeCanvas === 'main' ? (
              <Suspense fallback={
                <div className="h-full diagram-canvas flex items-center justify-center">
                  <div className="text-text-secondary animate-pulse">Loading diagram canvas...</div>
                </div>
              }>
                <LazyDiagramCanvas />
              </Suspense>
            ) : (
              <Suspense fallback={
                <div className="h-full bg-black flex items-center justify-center">
                  <div className="text-gray-400 animate-pulse">Loading execution view...</div>
                </div>
              }>
                <LazyExecutionView />
              </Suspense>
            )
          )}
        </div>
      </div>

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
