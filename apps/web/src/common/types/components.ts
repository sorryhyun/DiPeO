import React from 'react';
import { Position } from '@xyflow/react';
import { UnifiedNodeConfig } from './nodeConfig';

export interface BaseNodeProps extends React.HTMLAttributes<HTMLDivElement> {
  id: string;
  children: React.ReactNode;
  selected?: boolean;
  onFlip?: () => void;
  handles?: {
    type: 'input' | 'output';
    position: Position;
    id?: string;
    style?: React.CSSProperties;
    className?: string;
  }[];
  borderColor?: string;
  showFlipButton?: boolean;
  nodeType?: string;
  data?: unknown;
  autoHandles?: boolean;
  isRunning?: boolean;
  onUpdateData?: (nodeId: string, data: unknown) => void;
  onUpdateNodeInternals?: (nodeId: string) => void;
  nodeConfigs?: Record<string, UnifiedNodeConfig>;
  onDragOver?: React.DragEventHandler<HTMLDivElement>;
  onDragEnter?: React.DragEventHandler<HTMLDivElement>;
  onDragLeave?: React.DragEventHandler<HTMLDivElement>;
  onDrop?: React.DragEventHandler<HTMLDivElement>;
}

export interface GenericNodeProps {
  id: string;
  data: unknown;
  selected?: boolean;
  nodeType: string;
  children: React.ReactNode;
  showFlipButton?: boolean;
  onDragOver?: React.DOMAttributes<HTMLDivElement>['onDragOver'];
  onDragEnter?: React.DOMAttributes<HTMLDivElement>['onDragEnter'];
  onDragLeave?: React.DOMAttributes<HTMLDivElement>['onDragLeave'];
  onDrop?: React.DOMAttributes<HTMLDivElement>['onDrop'];
  isRunning?: boolean;
  onUpdateData?: (nodeId: string, data: unknown) => void;
  onUpdateNodeInternals?: (nodeId: string) => void;
  nodeConfigs?: Record<string, UnifiedNodeConfig>;
  borderColor?: string;
  width?: number | string;
  height?: number | string;
  className?: string;
}