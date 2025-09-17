import React, { useMemo } from 'react';
import { NodeProps } from '@xyflow/react';
import { BaseNode } from './BaseNode';
import './TodoNode.css';

/**
 * TodoNode - Special styling for TODO-backed note nodes
 *
 * This component extends BaseNode to provide custom styling for nodes
 * that represent TODO items from Claude Code integration.
 */

interface TodoMetadata {
  isTodoItem?: boolean;
  todoStatus?: 'pending' | 'in_progress' | 'completed';
  todoBadge?: string;
  todoIcon?: string;
  todoActiveForm?: string;
  todoOriginalContent?: string;
}

interface TodoNodeData extends Record<string, unknown> {
  label?: string;
  content?: string;
  metadata?: TodoMetadata;
  statusColor?: string;
}

const TodoNode = React.memo<NodeProps<TodoNodeData>>(({ id, type, data, selected, dragging }) => {
  const todoData = useMemo(() => {
    // Check if this is a TODO node
    const metadata = data?.metadata as TodoMetadata | undefined;
    const isTodo = metadata?.isTodoItem || false;

    if (!isTodo) {
      // Not a TODO node, render as normal
      return null;
    }

    // Extract TODO-specific data
    const status = metadata?.todoStatus || 'pending';
    const badge = metadata?.todoBadge;
    const icon = metadata?.todoIcon;
    const activeForm = metadata?.todoActiveForm;
    const originalContent = metadata?.todoOriginalContent;

    // Define status colors and styling
    const statusStyles = {
      pending: {
        borderColor: '#FFA500', // Orange
        backgroundColor: '#FFF8E1',
        badgeColor: '#FF8C00',
        statusIcon: '⏳',
        pulseAnimation: false
      },
      in_progress: {
        borderColor: '#1E90FF', // Blue
        backgroundColor: '#E3F2FD',
        badgeColor: '#1976D2',
        statusIcon: '🔄',
        pulseAnimation: true
      },
      completed: {
        borderColor: '#32CD32', // Green
        backgroundColor: '#E8F5E9',
        badgeColor: '#2E7D32',
        statusIcon: '✅',
        pulseAnimation: false
      }
    };

    const style = statusStyles[status] || statusStyles.pending;

    return {
      isTodo,
      status,
      badge,
      icon: icon || style.statusIcon,
      activeForm,
      originalContent,
      style
    };
  }, [data]);

  // If not a TODO node, render standard BaseNode
  if (!todoData) {
    return (
      <BaseNode
        id={id}
        type={type || 'note'}
        selected={selected}
        data={data || {}}
        dragging={dragging}
      />
    );
  }

  // Create enhanced data for BaseNode with TODO styling
  const enhancedData = {
    ...data,
    // Override label with active form if in progress
    label: todoData.status === 'in_progress' && todoData.activeForm
      ? todoData.activeForm
      : data.label || data.content,
    // Add custom color for TODO nodes
    statusColor: todoData.style.borderColor
  };

  // Custom className for TODO styling
  const todoClassName = `
    todo-node
    todo-${todoData.status}
    ${todoData.style.pulseAnimation ? 'animate-pulse-border' : ''}
    relative
    transition-all
    duration-300
  `;

  return (
    <div className="relative">
      {/* Status Badge */}
      {todoData.badge && (
        <div
          className="absolute -top-3 -left-3 z-20 px-2 py-1 text-xs font-bold text-white rounded-full shadow-lg"
          style={{ backgroundColor: todoData.style.badgeColor }}
        >
          {todoData.badge}
        </div>
      )}

      {/* Status Icon */}
      <div className="absolute -top-2 -right-2 z-20 text-2xl">
        {todoData.icon}
      </div>

      {/* Main Node with BaseNode */}
      <div
        style={{
          '--todo-border-color': todoData.style.borderColor,
          '--todo-bg-color': todoData.style.backgroundColor,
        } as React.CSSProperties}
      >
        <BaseNode
          id={id}
          type="note"
          selected={selected}
          data={enhancedData}
          dragging={dragging}
          className={todoClassName}
          showFlipButton={false} // TODO nodes don't need flip buttons
        />
      </div>

      {/* Progress Indicator for In-Progress items */}
      {todoData.status === 'in_progress' && (
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-blue-500 rounded-b overflow-hidden">
          <div className="h-full bg-blue-300 animate-progress-bar" />
        </div>
      )}
    </div>
  );
});

TodoNode.displayName = 'TodoNode';

export default TodoNode;
