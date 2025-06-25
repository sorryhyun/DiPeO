import { NodeType } from '@dipeo/domain-models';
import { NODE_ICONS, NODE_COLORS } from '@/core/config/nodeMeta';

export function formatTime(startTime: Date | null, endTime: Date | null, formatDuration: boolean = true): string {
  if (!startTime) return formatDuration ? '0s' : '-';
  
  const end = endTime || new Date();
  const elapsed = Math.floor((end.getTime() - startTime.getTime()) / 1000);
  
  if (!formatDuration) return `${elapsed}s`;
  
  const minutes = Math.floor(elapsed / 60);
  const seconds = elapsed % 60;
  
  return minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;
}

export function getNodeIcon(nodeType: string): string {
  return NODE_ICONS[nodeType as NodeType] || '📦';
}

export function getNodeColor(nodeType: string): string {
  return NODE_COLORS[nodeType as NodeType] || '#6b7280';
}

