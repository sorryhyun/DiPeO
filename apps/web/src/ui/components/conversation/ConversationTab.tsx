import React, { Suspense } from 'react';

// Lazy load the conversation dashboard
const ConversationDashboard = React.lazy(() => import('./ConversationDashboard'));

export const ConversationTab: React.FC = () => {
  return (
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
  );
};

export default ConversationTab;
