import React, { Suspense, useMemo } from 'react';
import { useCanvasState } from '@/shared/contexts/CanvasContext';
import { LoadingFallback } from '@/shared/components/feedback';

// Lazy load the property panel
const PropertyPanel = React.lazy(() => import('./PropertyPanel').then(module => ({ default: module.PropertyPanel })));

/**
 * PropertiesTab - Refactored to use unified canvas hooks
 * Demonstrates the simplified data access pattern
 */
export const PropertiesTab: React.FC = () => {
  // Use the unified canvas state hook - much simpler!
  const canvasState = useCanvasState();
  const { 
    selectedNodeId, 
    selectedArrowId, 
    selectedPersonId,
    nodes,
    arrows,
    personsWithUsage 
  } = canvasState;
  
  // Get the selected entity
  const selectedPerson = selectedPersonId ? canvasState.persons.get(selectedPersonId) : null;
  const selectedNode = selectedNodeId ? nodes.get(selectedNodeId) : null;
  const selectedArrow = selectedArrowId ? arrows.get(selectedArrowId) : null;
  
  // Memoize entity data separately to ensure stability
  const entityData = useMemo(() => {
    if (selectedPerson) {
      return { ...selectedPerson, type: 'person' as const };
    }
    
    if (selectedNode) {
      const nodeData = selectedNode.data || {};
      return { ...nodeData, type: selectedNode.type || 'unknown' };
    }
    
    if (selectedArrow) {
      // Parse handle ID to get source node ID
      const [sourceNodeId, ...sourceHandleParts] = selectedArrow.source.split(':');
      const sourceHandleName = sourceHandleParts.join(':');
      
      // Find source node to determine if this is a special arrow
      const sourceNode = sourceNodeId ? nodes.get(sourceNodeId as any) : undefined;
      const isFromConditionBranch = sourceHandleName === 'true' || sourceHandleName === 'false';
      
      return {
        ...(selectedArrow.data || {}),
        content_type: selectedArrow.content_type 
          ? typeof selectedArrow.content_type === 'string'
            ? selectedArrow.content_type.toLowerCase()
            : selectedArrow.content_type
          : undefined,
        label: selectedArrow.label,
        id: selectedArrow.id,
        type: 'arrow' as const,
        _sourceNodeType: sourceNode?.type,
        _isFromConditionBranch: isFromConditionBranch
      };
    }
    
    return null;
  }, [selectedPerson, selectedNode, selectedArrow, nodes]);
  
  // Determine selected entity with stable references
  const selectedEntity = useMemo(() => {
    if (!entityData) return null;
    
    if (selectedPersonId && entityData.type === 'person') {
      return {
        type: 'person' as const,
        id: selectedPersonId,
        data: entityData,
        title: `${selectedPerson?.label || 'Person'} Properties`
      };
    }
    
    if (selectedNodeId && selectedNode) {
      return {
        type: 'node' as const,
        id: selectedNodeId,
        data: entityData,
        title: `${selectedNode.data?.label || 'Block'} Properties`
      };
    }
    
    if (selectedArrowId) {
      return {
        type: 'arrow' as const,
        id: selectedArrowId,
        data: entityData,
        title: 'Arrow Properties'
      };
    }
    
    return null;
  }, [selectedPersonId, selectedNodeId, selectedArrowId, entityData, selectedPerson, selectedNode]);
  
  // Simplified rendering logic
  const showWrapperHeader = !selectedEntity;
  const title = selectedEntity?.title || 'Properties';
  
  return (
    <div className="h-full flex flex-col">
      {showWrapperHeader && (
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold">{title}</h2>
        </div>
      )}
      <div className="flex-1 overflow-y-auto">
        {selectedEntity ? (
          <Suspense fallback={<LoadingFallback />}>
            <PropertyPanel 
              entityId={selectedEntity.id} 
              data={selectedEntity.data} 
            />
          </Suspense>
        ) : (
          <p className="p-4 text-sm text-gray-500">
            Select a block, arrow, or person to see its properties.
          </p>
        )}
      </div>
    </div>
  );
};

export default PropertiesTab;