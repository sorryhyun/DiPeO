/**
 * Status badge component for execution states
 */

import { Status } from '@dipeo/models';

interface StatusBadgeProps {
  status: Status | string;
  className?: string;
}

type StatusConfigKey = 'pending' | 'running' | 'completed' | 'failed' | 'aborted' | 'paused' | 'skipped' | 'maxiter_reached';

const statusConfig: Record<StatusConfigKey, { label: string; color: string; bg: string }> = {
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
  skipped: {
    label: 'Skipped',
    color: 'text-gray-700',
    bg: 'bg-gray-100',
  },
  maxiter_reached: {
    label: 'Max Iterations',
    color: 'text-purple-700',
    bg: 'bg-purple-100',
  },
};

export function StatusBadge({ status, className = '' }: StatusBadgeProps) {
  // Status enum values are already lowercase strings
  const statusKey = String(status) as StatusConfigKey;
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
