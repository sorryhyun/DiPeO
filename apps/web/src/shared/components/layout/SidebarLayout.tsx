// Generic sidebar layout component without domain knowledge
import React from 'react';

interface SidebarLayoutProps {
  position: 'left' | 'right';
  children: React.ReactNode;
  className?: string;
}

export const SidebarLayout = React.memo<SidebarLayoutProps>(({ position, children, className = '' }) => {
  const baseClasses = position === 'right'
    ? 'h-full border-l bg-gray-50 overflow-y-auto'
    : 'h-full p-4 border-r bg-gradient-to-b from-gray-50 to-gray-100 flex flex-col overflow-hidden';

  return (
    <aside className={`${baseClasses} ${className}`}>
      {children}
    </aside>
  );
});

SidebarLayout.displayName = 'SidebarLayout';