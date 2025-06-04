import React, { Suspense } from 'react';
import { PanelGroup, Panel, PanelResizeHandle } from 'react-resizable-panels';
import MemoryFlowVisualization from './MemoryFlowVisualization';
import ConversationDashboard from '@/features/conversation/components/ConversationDashboard';

const MemoryCanvas: React.FC = () => {
  return (
    <div className="h-full flex flex-col bg-slate-900">
      <PanelGroup direction="vertical">
        {/* Memory Visualization Panel */}
        <Panel defaultSize={70} minSize={40}>
          <div className="h-full relative">
            <Suspense fallback={
              <div className="h-full bg-gradient-to-b from-slate-700 to-slate-900 flex items-center justify-center">
                <div className="text-gray-400 animate-pulse">Loading memory visualization...</div>
              </div>
            }>
              <MemoryFlowVisualization />
            </Suspense>
          </div>
        </Panel>

        {/* Resizable Handle */}
        <PanelResizeHandle className="h-1 bg-slate-600 hover:bg-slate-500 cursor-row-resize" />

        {/* Conversation Dashboard Panel */}
        <Panel defaultSize={30} minSize={20}>
          <ConversationDashboard />
        </Panel>
      </PanelGroup>
    </div>
  );
};

export default MemoryCanvas;