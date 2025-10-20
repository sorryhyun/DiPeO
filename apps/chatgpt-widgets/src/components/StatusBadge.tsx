/**
 * Status badge component for execution states
 */

import React from 'react';

export type Status = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

interface StatusBadgeProps {
  status: Status;
  className?: string;
}

const statusConfig: Record<Status, { label: string; color: string; bg: string }> = {
  pending: {
    label: 'Pending',
    color: 'text-gray-700',
    bg: 'bg-gray-100',
  },
  running: {
    label: 'Running',
    color: 'text-blue-700',
    bg: 'bg-blue-100',
  },
  completed: {
    label: 'Completed',
    color: 'text-green-700',
    bg: 'bg-green-100',
  },
  failed: {
    label: 'Failed',
    color: 'text-red-700',
    bg: 'bg-red-100',
  },
  cancelled: {
    label: 'Cancelled',
    color: 'text-orange-700',
    bg: 'bg-orange-100',
  },
};

export function StatusBadge({ status, className = '' }: StatusBadgeProps) {
  const config = statusConfig[status] || statusConfig.pending;

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color} ${config.bg} ${className}`}
    >
      {config.label}
    </span>
  );
}
