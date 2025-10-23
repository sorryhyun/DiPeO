/**
 * Status badge component for execution states
 */

import { Status } from '@dipeo/models';

interface StatusBadgeProps {
  status: Status;
  className?: string;
}

type StatusKey = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'aborted' | 'paused' | 'skipped' | 'maxiter_reached';

const statusConfig: Record<StatusKey, { label: string; color: string; bg: string }> = {
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
  paused: {
    label: 'Paused',
    color: 'text-yellow-700',
    bg: 'bg-yellow-100',
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
  aborted: {
    label: 'Aborted',
    color: 'text-orange-700',
    bg: 'bg-orange-100',
  },
  aborted: {
    label: 'Aborted',
    color: 'text-orange-700',
    bg: 'bg-orange-100',
  },
  paused: {
    label: 'Paused',
    color: 'text-yellow-700',
    bg: 'bg-yellow-100',
  },
  skipped: {
    label: 'Skipped',
    color: 'text-gray-600',
    bg: 'bg-gray-100',
  },
  maxiter_reached: {
    label: 'Max Iter',
    color: 'text-purple-700',
    bg: 'bg-purple-100',
  },
};

export function StatusBadge({ status, className = '' }: StatusBadgeProps) {
  // Convert Status enum to lowercase string key
  const statusKey = status.toLowerCase() as StatusKey;
  const config = statusConfig[statusKey] || statusConfig.pending;

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color} ${config.bg} ${className}`}
    >
      {config.label}
    </span>
  );
}

export type { Status };
