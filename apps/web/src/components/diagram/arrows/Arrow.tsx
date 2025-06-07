import React, { useState, useCallback, useRef, useMemo } from 'react';
import { EdgeProps, EdgeLabelRenderer, BaseEdge, useReactFlow } from '@xyflow/react';
import { useConsolidatedUIStore } from '@/stores';

import { Arrow } from '@/types';

type ArrowData = Arrow['data'];

export interface CustomArrowProps extends EdgeProps {
  onUpdateData?: (edgeId: string, data: Partial<ArrowData>) => void;
}

// Helper function to calculate quadratic bezier point at parameter t
const getQuadraticPoint = (
  t: number,
  sourceX: number,
  sourceY: number,
  controlX: number,
  controlY: number,
  targetX: number,
  targetY: number
) => {
  const oneMinusT = 1 - t;
  const x = oneMinusT * oneMinusT * sourceX + 2 * oneMinusT * t * controlX + t * t * targetX;
  const y = oneMinusT * oneMinusT * sourceY + 2 * oneMinusT * t * controlY + t * t * targetY;
  return { x, y };
};

export const CustomArrow: React.FC<CustomArrowProps> = ({
  id,
  source,
  target,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition: _sourcePosition,
  targetPosition: _targetPosition,
  style = {},
  data,
  markerEnd,
  selected,
  onUpdateData,
}) => {
  const { screenToFlowPosition } = useReactFlow();
  const [isDragging, setIsDragging] = useState(false);
  const dragRef = useRef<{ startX: number; startY: number; controlX: number; controlY: number } | null>(null);
  const { activeCanvas } = useConsolidatedUIStore();
  const isExecutionMode = activeCanvas === 'execution';
  
  const arrowData = data as ArrowData;
  const controlPointOffsetX = arrowData?.controlPointOffsetX ?? 0;
  const controlPointOffsetY = arrowData?.controlPointOffsetY ?? 0;

  // Memoize path and label position calculations
  const { edgePath, labelX, labelY } = useMemo(() => {
    let path: string;
    let lx: number;
    let ly: number;
    
    if (source === target) {
      const x = sourceX;
      const y = sourceY;
      const offset = arrowData?.loopRadius ?? 50;
      path = `M ${x},${y}
        C ${x + offset},${y - offset} ${x + offset},${y + offset} ${x},${y + offset}
        C ${x - offset},${y + offset} ${x - offset},${y - offset} ${x},${y}`;
      lx = x;
      ly = y - offset;
    } else {
      const defaultControlX = (sourceX + targetX) / 2;
      const defaultControlY = (sourceY + targetY) / 2;
      
      // Apply user's control point offset
      const controlX = defaultControlX + controlPointOffsetX;
      const controlY = defaultControlY + controlPointOffsetY;
      
      // Create quadratic bezier path with custom control point
      path = `M ${sourceX},${sourceY} Q ${controlX},${controlY} ${targetX},${targetY}`;
      
      // Calculate point on the bezier curve at t=0.5 (midpoint along the curve)
      const { x, y } = getQuadraticPoint(0.5, sourceX, sourceY, controlX, controlY, targetX, targetY);
      lx = x;
      ly = y;
    }
    
    return { edgePath: path, labelX: lx, labelY: ly };
  }, [source, target, sourceX, sourceY, targetX, targetY, controlPointOffsetX, controlPointOffsetY, arrowData?.loopRadius]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (!onUpdateData) return;
    
    e.stopPropagation();
    setIsDragging(true);
    
    // Convert initial mouse position to flow coordinates
    const initialFlowPosition = screenToFlowPosition({
      x: e.clientX,
      y: e.clientY,
    });
    
    // Store the initial offset between mouse and control point
    if (source === target) {
      // For self-loops, calculate initial distance
      const currentRadius = arrowData?.loopRadius ?? 50;
      dragRef.current = {
        startX: initialFlowPosition.x,
        startY: initialFlowPosition.y,
        controlX: currentRadius,
        controlY: 0,
      };
    } else {
      // For regular arrows, store initial mouse position and current offset
      dragRef.current = {
        startX: initialFlowPosition.x,
        startY: initialFlowPosition.y,
        controlX: controlPointOffsetX,
        controlY: controlPointOffsetY,
      };
    }
    
    const handleMouseMove = (moveEvent: MouseEvent) => {
      if (!dragRef.current) return;
      
      // Convert mouse position to flow coordinates
      const flowPosition = screenToFlowPosition({
        x: moveEvent.clientX,
        y: moveEvent.clientY,
      });
      
      if (source === target) {
        // For self-loops, calculate distance based on initial radius and mouse movement
        const nodeX = sourceX;
        const nodeY = sourceY;
        const deltaX = flowPosition.x - dragRef.current.startX;
        const deltaY = flowPosition.y - dragRef.current.startY;
        
        // Calculate new distance from node center
        const newX = nodeX + dragRef.current.controlX + deltaX;
        const newY = nodeY + deltaY;
        const distance = Math.sqrt(
          Math.pow(newX - nodeX, 2) + 
          Math.pow(newY - nodeY, 2)
        );
        
        onUpdateData(id, {
          loopRadius: Math.max(30, Math.min(100, distance)),
        });
      } else {
        // Calculate the mouse movement delta
        const deltaX = flowPosition.x - dragRef.current.startX;
        const deltaY = flowPosition.y - dragRef.current.startY;
        
        // Apply delta to the original control point offset
        const newControlX = dragRef.current.controlX + deltaX;
        const newControlY = dragRef.current.controlY + deltaY;
        
        onUpdateData(id, {
          controlPointOffsetX: Math.round(newControlX * 10) / 10,
          controlPointOffsetY: Math.round(newControlY * 10) / 10,
        });
      }
    };
    
    const handleMouseUp = () => {
      setIsDragging(false);
      dragRef.current = null;
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, [id, source, target, screenToFlowPosition, sourceX, sourceY, onUpdateData, controlPointOffsetX, controlPointOffsetY, arrowData]);

  // Double-click to reset to straight line
  const handleDoubleClick = useCallback((e: React.MouseEvent) => {
    if (!onUpdateData) return;
    
    e.stopPropagation();
    if (source === target) {
      onUpdateData(id, {
        loopRadius: 50, // Reset to default loop radius
      });
    } else {
      onUpdateData(id, {
        controlPointOffsetX: 0,
        controlPointOffsetY: 0,
      });
    }
  }, [id, source, target, onUpdateData]);

  // Memoize edge style
  const edgeStyle = useMemo(() => ({
    ...(style || {}),
    strokeWidth: selected ? 3 : 1.5,
    stroke: selected ? '#3b82f6' : '#6b7280'
  }), [style, selected]);

  // Memoize label style
  const labelStyle = useMemo(() => ({
    position: 'absolute' as const,
    transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
    fontSize: 14,
    padding: '4px 8px',
    borderRadius: '6px',
    pointerEvents: 'all' as const,
    color: selected ? '#1d4ed8' : (isExecutionMode ? '#111827' : '#374151'),
    fontWeight: selected ? '600' : (isExecutionMode ? '600' : '500'),
    maxWidth: '200px',
    cursor: isDragging ? 'grabbing' : 'grab',
    userSelect: 'none' as const,
  }), [labelX, labelY, selected, isExecutionMode, isDragging]);

  // Memoize label content
  const labelContent = useMemo(() => {
    if (arrowData?.branch) {
      return <span>{arrowData.branch === 'true' ? '✅' : '❌'}</span>;
    }
    
    if (arrowData?.contentType) {
      const icons: Record<string, string> = {
        'conversation_state': '💬',
        'variable_in_object': '📦',
        'raw_text': '📝',
        'empty': '⚪',
        'generic': '🔄',
      };
      return <span>{icons[arrowData.contentType] || '📋'}</span>;
    }
    
    return null;
  }, [arrowData?.branch, arrowData?.contentType]);

  return (
    <>
      <BaseEdge path={edgePath} markerEnd={markerEnd} style={edgeStyle} />
      <EdgeLabelRenderer>
        <div
          style={labelStyle}
          className="bg-white border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
          onMouseDown={handleMouseDown}
          onDoubleClick={handleDoubleClick}
          title="Drag to curve arrow, double-click to straighten"
        >
          <div className="text-center">
            <div className="font-medium flex items-center justify-center gap-1">
              {labelContent}
              {arrowData?.label && (
                <span>{arrowData.label}</span>
              )}
            </div>
          </div>
        </div>
      </EdgeLabelRenderer>
    </>
  );
};

export default CustomArrow;