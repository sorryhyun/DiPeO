import React, { ReactNode } from 'react';

interface TabListProps {
  children: ReactNode;
  className?: string;
  'aria-label'?: string;
}

export function TabList({ children, className = '', 'aria-label': ariaLabel }: TabListProps) {
  return (
    <div
      role="tablist"
      aria-label={ariaLabel}
      className={`flex border-b border-gray-700 ${className}`}
    >
      {children}
    </div>
  );
}
