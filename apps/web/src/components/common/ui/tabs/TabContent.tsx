import React, { ReactNode } from 'react';
import { useTabsContext } from './useTabsContext';

interface TabContentProps {
  value: string;
  children: ReactNode;
  className?: string;
  forceMount?: boolean;
}

export function TabContent({ value, children, className = '', forceMount = false }: TabContentProps) {
  const { activeTab } = useTabsContext();
  const isActive = activeTab === value;

  if (!isActive && !forceMount) {
    return null;
  }

  return (
    <div
      role="tabpanel"
      id={`panel-${value}`}
      aria-labelledby={`tab-${value}`}
      tabIndex={0}
      hidden={!isActive}
      className={`flex-1 overflow-hidden ${isActive ? 'block' : 'hidden'} ${className}`}
    >
      {children}
    </div>
  );
}