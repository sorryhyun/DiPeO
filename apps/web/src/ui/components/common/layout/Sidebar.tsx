// Sidebar component that delegates to feature-specific sidebars
import React, { Suspense } from 'react';

// Lazy load feature-specific sidebars
const DiagramSidebar = React.lazy(() => import('@/ui/components/diagram/sidebar/DiagramSidebar'));
const PropertiesSidebar = React.lazy(() => import('@/ui/components/diagram/properties/sidebar/PropertiesSidebar'));

interface SidebarProps {
  position: 'left' | 'right';
}

const Sidebar = React.memo<SidebarProps>(({ position }) => {
  if (position === 'right') {
    return (
      <Suspense fallback={<div className="p-4 text-gray-500">Loading properties sidebar...</div>}>
        <PropertiesSidebar />
      </Suspense>
    );
  }

  // Left sidebar - diagram operations
  return (
    <Suspense fallback={<div className="p-4 text-gray-500">Loading diagram sidebar...</div>}>
      <DiagramSidebar />
    </Suspense>
  );
});

Sidebar.displayName = 'Sidebar';

export default Sidebar;
