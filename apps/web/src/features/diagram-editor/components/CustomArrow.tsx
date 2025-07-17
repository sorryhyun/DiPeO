import React, { useState, useCallback, useRef, useMemo } from 'react';
import { EdgeProps, EdgeLabelRenderer, BaseEdge, useReactFlow } from '@xyflow/react';
import { useCanvasState, useCanvasOperations } from '@/shared/contexts/CanvasContext';
import { useArrowData } from '@/core/store/hooks';
import { arrowId } from '@/core/types';
import type { ArrowData } from '@/lib/graphql/types';
import { getQuadraticPoint } from '@/lib/utils/geometry';

export type CustomArrowProps = EdgeProps & {
  sourceHandle?: string | null;
  targetHandle?: string | null;
};

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
  sourceHandle,
  targetHandle: _targetHandle,
}) => {
  const { screenToFlowPosition } = useReactFlow();
  const [isDragging, setIsDragging] = useState(false);
  const dragRef = useRef<{ startX: number; startY: number; controlX: number; controlY: number } | null>(null);
  const { activeCanvas } = useCanvasState();
  const { arrowOps } = useCanvasOperations();
  const currentArrow = useArrowData(arrowId(id));
  const isExecutionMode = activeCanvas === 'execution';
  
  const arrowData = data as ArrowData | undefined;
  const controlPointOffsetX = Number(arrowData?.controlPointOffsetX ?? 0);
  const controlPointOffsetY = Number(arrowData?.controlPointOffsetY ?? 0);

  // Memoize label content - moved here to avoid initialization error
  const labelContent = useMemo(() => {
    // Extract handle name from the full handle ID (e.g., "node-123_condtrue_output" -> "condtrue")
    const sourceHandleParts = sourceHandle?.split('_') || [];
    const sourceHandleName = sourceHandleParts[sourceHandleParts.length - 2]?.toLowerCase();
    
    // Check if this is a branch arrow from a condition node
    // by looking at the source handle name
    const isConditionBranch = sourceHandleName === 'condtrue' || sourceHandleName === 'condfalse';
    
    if (arrowData?.branch) {
      return <span>{arrowData.branch === 'true' ? '✅' : '❌'}</span>;
    }
    
    // If no explicit branch data but it's from a condition node, infer from handle name
    if (isConditionBranch) {
      const isTrueBranch = sourceHandleName === 'condtrue';
      return <span>{isTrueBranch ? '✅' : '❌'}</span>;
    }
    
    if (arrowData?.content_type) {
      const icons: Record<string, string> = {
        'conversation_state': '💬',
        'variable_in_object': '📦',
        'raw_text': '📝',
        'empty': '⚪',
        'generic': '🔄',
      };
      return <span>{icons[arrowData.content_type] || '📋'}</span>;
    }
    
    // If arrow has a label but no content_type, assume it's raw text
    if (arrowData?.label) {
      return <span>📝</span>;
    }
    
    // No emoji for arrows without explicit content_type or label
    return null;
  }, [arrowData?.branch, arrowData?.content_type, arrowData?.label, source, sourceHandle]);


  // Create a type-safe wrapper that updates arrow data in the store
  const handleUpdateData = useCallback(async (edgeId: string, newData: Partial<ArrowData>) => {
    if (!newData) return;
    
    // Use the current arrow data to preserve existing data
    const currentData = (currentArrow?.data || {}) as ArrowData;
    
    // Merge the new data with existing data
    await arrowOps.updateArrow(arrowId(edgeId), {
      data: { ...currentData, ...newData } as Record<string, unknown>
    });
  }, [arrowOps, currentArrow]);

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
    zIndex: 1000, // Ensure labels are above other elements
  }), [labelX, labelY, selected, isExecutionMode, isDragging]);


  return (
    <>
      <BaseEdge path={edgePath} markerEnd={markerEnd} style={edgeStyle} />
      {/* Always render the label element for dragging functionality */}
      <EdgeLabelRenderer>
        <div
          style={labelStyle}
          className="bg-white border border-gray-200 shadow-sm hover:shadow-md"
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
              {/* Show a drag handle if no emoji and no label */}
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