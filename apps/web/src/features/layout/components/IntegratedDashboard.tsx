// Integrated dashboard combining conversation view and properties panel with tabs
import React, { Suspense } from 'react';
import { MessageSquare, Settings } from 'lucide-react';
import { useNodes, useArrows, usePersons, useUIState, useSelectedElement } from '@/global/hooks/useStoreSelectors';

// Lazy load heavy components
const ConversationDashboard = React.lazy(() => import('../../conversation/components/ConversationDashboard'));
const PropertiesRenderer = React.lazy(() => import('../../properties/components/PropertiesRenderer'));

const IntegratedDashboard: React.FC = () => {
  const { nodes } = useNodes();
  const { arrows } = useArrows();
  const { dashboardTab, setDashboardTab } = useUIState();
  
  const {
    selectedPersonId,
    selectedNodeId,
    selectedArrowId,
  } = useSelectedElement();
  
  const { persons } = usePersons();

  // Render tab bar
  const renderTabBar = () => (
    <div className="flex items-center justify-between px-4 py-2 bg-gray-100 border-b">
      <div className="flex items-center space-x-1">
        <button
          onClick={() => setDashboardTab('conversation')}
          className={`px-4 py-1.5 rounded-t-md text-sm font-medium transition-colors ${
            dashboardTab === 'conversation' 
              ? 'bg-white text-blue-600 border-t border-l border-r border-gray-300' 
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          <div className="flex items-center space-x-2">
            <MessageSquare className="h-4 w-4" />
            <span>Conversation</span>
          </div>
        </button>
        <button
          onClick={() => setDashboardTab('properties')}
          className={`px-4 py-1.5 rounded-t-md text-sm font-medium transition-colors ${
            dashboardTab === 'properties' 
              ? 'bg-white text-blue-600 border-t border-l border-r border-gray-300' 
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          <div className="flex items-center space-x-2">
            <Settings className="h-4 w-4" />
            <span>Properties</span>
          </div>
        </button>
      </div>
    </div>
  );


  return (
    <div className="h-full bg-white flex flex-col">
      {renderTabBar()}
      <div className="flex-1 overflow-hidden">
        {dashboardTab === 'conversation' && (
          <div className="h-full">
            <Suspense fallback={
              <div className="h-full bg-white p-4">
                <div className="space-y-4">
                  <div className="h-8 bg-gray-200 rounded animate-pulse"></div>
                  <div className="h-32 bg-gray-100 rounded animate-pulse"></div>
                  <div className="h-32 bg-gray-100 rounded animate-pulse"></div>
                </div>
              </div>
            }>
              <ConversationDashboard />
            </Suspense>
          </div>
        )}
        {dashboardTab === 'properties' && (
          <div className="flex-1 overflow-y-auto">
            <Suspense fallback={
              <div className="p-4 space-y-4">
                <div className="h-8 bg-gray-200 rounded animate-pulse"></div>
                <div className="space-y-2">
                  <div className="h-4 bg-gray-100 rounded w-1/2 animate-pulse"></div>
                  <div className="h-10 bg-gray-100 rounded animate-pulse"></div>
                </div>
                <div className="space-y-2">
                  <div className="h-4 bg-gray-100 rounded w-1/2 animate-pulse"></div>
                  <div className="h-10 bg-gray-100 rounded animate-pulse"></div>
                </div>
              </div>
            }>
              <PropertiesRenderer
                selectedNodeId={selectedNodeId}
                selectedArrowId={selectedArrowId}
                selectedPersonId={selectedPersonId}
                nodes={nodes}
                arrows={arrows}
                persons={persons}
              />
            </Suspense>
          </div>
        )}
      </div>
    </div>
  );
};

export default IntegratedDashboard;