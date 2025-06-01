import React from 'react';
import { Position } from '@xyflow/react';
import { UnifiedNodeConfig } from './nodeType';

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
  data?: any;
  autoHandles?: boolean;
  isRunning?: boolean;
  onUpdateData?: (nodeId: string, data: any) => void;
  onUpdateNodeInternals?: (nodeId: string) => void;
  nodeConfigs?: Record<string, UnifiedNodeConfig>;
  onDragOver?: React.DragEventHandler<HTMLDivElement>;
  onDrop?: React.DragEventHandler<HTMLDivElement>;
}

export interface GenericNodeProps {
  id: string;
  data: any;
  selected?: boolean;
  nodeType: string;
  children: React.ReactNode;
  showFlipButton?: boolean;
  onDragOver?: React.DOMAttributes<HTMLDivElement>['onDragOver'];
  onDrop?: React.DOMAttributes<HTMLDivElement>['onDrop'];
  isRunning?: boolean;
  onUpdateData?: (nodeId: string, data: any) => void;
  onUpdateNodeInternals?: (nodeId: string) => void;
  nodeConfigs?: Record<string, UnifiedNodeConfig>;
}