import React from 'react';
import { PanelProps } from '@repo/core-model';

export function Panel({ icon, title, children }: PanelProps) {
  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center space-x-2 border-b pb-2">
        {icon}
        <h3 className="text-lg font-semibold">{title}</h3>
      </div>
      <div className="space-y-4">
        {children}
      </div>
    </div>
  );
}