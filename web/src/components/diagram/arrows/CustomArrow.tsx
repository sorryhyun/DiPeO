import React, { useState, useCallback, useRef, useMemo } from 'react';
import { EdgeProps, EdgeLabelRenderer, BaseEdge, useReactFlow } from '@xyflow/react';
import { useCanvasOperations } from '@/hooks';
import { useUIState } from '@/hooks/selectors';
import { arrowId } from '@/types';
import { getQuadraticPoint } from '@/utils/geometry';

export interface ArrowData {
  label?: string;
  style?: React.CSSProperties;
  controlPointOffsetX?: number;
  controlPointOffsetY?: number;
  loopRadius?: number;
  branch?: 'true' | 'false';
  contentType?: 'raw_text' | 'variable_in_object' | 'conversation_state' | 'empty' | 'generic';
}

export type CustomArrowProps = EdgeProps;

export const CustomArrow = React.memo<CustomArrowProps>(({
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
  selected = false,
}) => {
  const { screenToFlowPosition } = useReactFlow();
  const [isDragging, setIsDragging] = useState(false);
  const dragRef = useRef<{ startX: number; startY: number; controlX: number; controlY: number } | null>(null);
  const { activeCanvas } = useUIState();
  const canvas = useCanvasOperations();
  const isExecutionMode = activeCanvas === 'execution';
  
  const arrowData = data as ArrowData | undefined;
  const controlPointOffsetX = Number(arrowData?.controlPointOffsetX ?? 0);
  const controlPointOffsetY = Number(arrowData?.controlPointOffsetY ?? 0);

  // Create a type-safe wrapper that updates arrow data in the store
  const handleUpdateData = useCallback((edgeId: string, data: Partial<ArrowData>) => {
    if (!data) return;
    
    // Update the arrow's data property with the new ArrowData
    canvas.updateArrow(arrowId(edgeId), {
      data: data as Record<string, unknown>
    });
  }, [canvas]);

  // Memoize path and label position calculations
  const { edgePath, labelX, labelY } = useMemo(() => {
    let path: string;
    let lx: number;
    let ly: number;
    
    if (source === target) {
      const x = sourceX;
      const y = sourceY;
      const offset = Number(arrowData?.loopRadius ?? 50);
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
      const midPoint = getQuadraticPoint(
        { x: sourceX, y: sourceY },
        { x: controlX, y: controlY },
        { x: targetX, y: targetY },
        0.5
      );
      lx = midPoint.x;
      ly = midPoint.y;
    }
    
    return { edgePath: path, labelX: lx, labelY: ly };
  }, [source, target, sourceX, sourceY, targetX, targetY, controlPointOffsetX, controlPointOffsetY, arrowData?.loopRadius]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
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
        
        handleUpdateData(id as string, {
          loopRadius: Math.max(30, Math.min(100, distance)),
        });
      } else {
        // Calculate the mouse movement delta
        const deltaX = flowPosition.x - dragRef.current.startX;
        const deltaY = flowPosition.y - dragRef.current.startY;
        
        // Apply delta to the original control point offset
        const newControlX = dragRef.current.controlX + deltaX;
        const newControlY = dragRef.current.controlY + deltaY;
        
        handleUpdateData(id as string, {
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
  }, [id, source, target, screenToFlowPosition, sourceX, sourceY, handleUpdateData, controlPointOffsetX, controlPointOffsetY, arrowData]);

  // Double-click to reset to straight line
  const handleDoubleClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    if (source === target) {
      handleUpdateData(id as string, {
        loopRadius: 50, // Reset to default loop radius
      });
    } else {
      handleUpdateData(id as string, {
        controlPointOffsetX: 0,
        controlPointOffsetY: 0,
      });
    }
  }, [id, source, target, handleUpdateData]);

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
      {/* Always render the label element for dragging functionality */}
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
              {/* Show a drag handle if no content */}
              {!labelContent && !arrowData?.label && (
                <span className="text-gray-400">⋮⋮</span>
              )}
            </div>
          </div>
        </div>
      </EdgeLabelRenderer>
    </>
  );
});

CustomArrow.displayName = 'CustomArrow';

export default CustomArrow;