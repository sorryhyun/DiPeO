import React, { useState, ReactNode } from 'react';
import { TabsContext } from './TabsContext';

interface TabsProps {
  defaultValue: string;
  children: ReactNode;
  className?: string;
  onValueChange?: (value: string) => void;
}

export function Tabs({ defaultValue, children, className = '', onValueChange }: TabsProps) {
  const [activeTab, setActiveTabState] = useState(defaultValue);

  const setActiveTab = (value: string) => {
    setActiveTabState(value);
    onValueChange?.(value);
  };

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className={`flex flex-col h-full ${className}`}>
        {children}
      </div>
    </TabsContext.Provider>
  );
}
