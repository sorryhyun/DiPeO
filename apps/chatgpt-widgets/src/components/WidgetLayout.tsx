/**
 * Common layout wrapper for widgets
 */

import React, { ReactNode } from 'react';

interface WidgetLayoutProps {
  title?: string;
  children: ReactNode;
  error?: Error | null;
  loading?: boolean;
}

export function WidgetLayout({ title, children, error, loading }: WidgetLayoutProps) {
  if (error) {
    return (
      <div className="widget-container">
        <div className="widget-error">
          <h3 className="text-sm font-semibold mb-1">Error</h3>
          <p className="text-sm">{error.message}</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="widget-container">
        <div className="widget-loading">
          <div className="widget-spinner"></div>
          <span className="ml-2">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="widget-container">
      {title && (
        <h2 className="text-lg font-semibold mb-4 text-gray-900">{title}</h2>
      )}
      {children}
    </div>
  );
}
