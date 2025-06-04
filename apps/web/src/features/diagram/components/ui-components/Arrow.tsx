import React, { useState, useCallback, useRef } from 'react';
import { EdgeProps, EdgeLabelRenderer, BaseEdge, useReactFlow } from '@xyflow/react';

import { ArrowData } from '@/shared/types';

export interface CustomArrowProps extends EdgeProps {
  onUpdateData?: (edgeId: string, data: Partial<ArrowData>) => void;
}

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
  
  const arrowData = data as ArrowData;
  const controlPointOffsetX = arrowData?.controlPointOffsetX ?? 0;
  const controlPointOffsetY = arrowData?.controlPointOffsetY ?? 0;

  let edgePath: string;
  let labelX: number;
  let labelY: number;
  
  if (source === target) {
    const x = sourceX;
    const y = sourceY;
    const offset = arrowData?.loopRadius ?? 50;
    edgePath = `M ${x},${y}
      C ${x + offset},${y - offset} ${x + offset},${y + offset} ${x},${y + offset}
      C ${x - offset},${y + offset} ${x - offset},${y - offset} ${x},${y}`;
    labelX = x;
    labelY = y - offset;
  } else {
    const defaultControlX = (sourceX + targetX) / 2;
    const defaultControlY = (sourceY + targetY) / 2;
    
    // Apply user's control point offset
    const controlX = defaultControlX + controlPointOffsetX;
    const controlY = defaultControlY + controlPointOffsetY;
    
    // Create quadratic bezier path with custom control point
    edgePath = `M ${sourceX},${sourceY} Q ${controlX},${controlY} ${targetX},${targetY}`;
    
    // Calculate point on the bezier curve at t=0.5 (midpoint along the curve)
    // For quadratic bezier: B(t) = (1-t)²P0 + 2(1-t)tP1 + t²P2
    const t = 0.5;
    const oneMinusT = 1 - t;
    labelX = oneMinusT * oneMinusT * sourceX + 2 * oneMinusT * t * controlX + t * t * targetX;
    labelY = oneMinusT * oneMinusT * sourceY + 2 * oneMinusT * t * controlY + t * t * targetY;
  }

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (!onUpdateData) return;
    
    e.stopPropagation();
    setIsDragging(true);
    
    const handleMouseMove = (moveEvent: MouseEvent) => {
      // Convert mouse position to flow coordinates
      const flowPosition = screenToFlowPosition({
        x: moveEvent.clientX,
        y: moveEvent.clientY,
      });
      
      if (source === target) {
        // For self-loops, update the loop radius based on distance from node center
        const nodeX = sourceX;
        const nodeY = sourceY;
        const distance = Math.sqrt(
          Math.pow(flowPosition.x - nodeX, 2) + 
          Math.pow(flowPosition.y - nodeY, 2)
        );
        onUpdateData(id, {
          loopRadius: Math.max(30, Math.min(100, distance)),
        });
      } else {
        // Calculate default control point (midpoint between source and target)
        const defaultControlX = (sourceX + targetX) / 2;
        const defaultControlY = (sourceY + targetY) / 2;
        
        // Calculate offset from current mouse position to default control point
        const offsetX = flowPosition.x - defaultControlX;
        const offsetY = flowPosition.y - defaultControlY;
        
        onUpdateData(id, {
          controlPointOffsetX: offsetX,
          controlPointOffsetY: offsetY,
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
  }, [id, source, target, screenToFlowPosition, sourceX, sourceY, targetX, targetY, onUpdateData]);

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

  return (
    <>
      <BaseEdge path={edgePath} markerEnd={markerEnd} style={{...(style || {}), strokeWidth: selected ? 3 : 1.5, stroke: selected ? '#3b82f6' : '#6b7280'}} />
      <EdgeLabelRenderer>
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            fontSize: 14,
            padding: '4px 8px',
            borderRadius: '6px',
            pointerEvents: 'all',
            color: selected ? '#1d4ed8' : '#374151',
            fontWeight: selected ? '600' : '500',
            maxWidth: '200px',
            cursor: isDragging ? 'grabbing' : 'grab',
            userSelect: 'none',
          }}
          className="bg-white border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
          onMouseDown={handleMouseDown}
          onDoubleClick={handleDoubleClick}
          title="Drag to curve arrow, double-click to straighten"
        >
          <div className="text-center">
            <div className="font-medium flex items-center justify-center gap-1">
              {arrowData?.branch ? (
                <span>
                  {arrowData.branch === 'true' ? '✅' : '❌'}
                </span>
              ) : arrowData?.contentType && (
                <span>
                  {arrowData.contentType === 'conversation_state' ? '💬' :
                   arrowData.contentType === 'variable_in_object' ? '📦' : 
                   '📝'}
                </span>
              )}
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