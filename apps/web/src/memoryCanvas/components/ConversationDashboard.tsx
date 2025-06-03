import React, { Suspense } from 'react';

// Lazy load the conversation dashboard
const ConversationDashboardComponent = React.lazy(() => import('@/features/conversation/components/ConversationDashboard'));

const ConversationDashboard: React.FC = () => {
  return (
    <div className="h-full bg-white flex flex-col">
      <div className="flex items-center justify-between px-4 py-2 bg-gray-100 border-b">
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-gray-700">Memory & Conversations</span>
        </div>
      </div>
      <div className="flex-1 overflow-hidden">
        <Suspense fallback={
          <div className="h-full bg-white p-4">
            <div className="space-y-4">
              <div className="h-8 bg-gray-200 rounded animate-pulse"></div>
              <div className="h-32 bg-gray-100 rounded animate-pulse"></div>
              <div className="h-32 bg-gray-100 rounded animate-pulse"></div>
            </div>
          </div>
        }>
          <ConversationDashboardComponent />
        </Suspense>
      </div>
    </div>
  );
};

export default ConversationDashboard;