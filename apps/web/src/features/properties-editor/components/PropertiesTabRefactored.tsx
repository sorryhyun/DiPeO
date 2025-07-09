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
  
  // Determine selected entity with cleaner logic
  const selectedEntity = useMemo(() => {
    if (selectedPersonId) {
      const person = personsWithUsage.find(p => p.id === selectedPersonId);
      if (person) {
        return {
          type: 'person' as const,
          id: selectedPersonId,
          data: { ...person, type: 'person' as const },
          title: `${person.label || 'Person'} Properties`
        };
      }
    }
    
    if (selectedNodeId) {
      const node = nodes.get(selectedNodeId);
      if (node) {
        const nodeData = node.data || {};
        return {
          type: 'node' as const,
          id: selectedNodeId,
          data: { ...nodeData, type: node.type || 'unknown' },
          title: `${nodeData.label || 'Block'} Properties`
        };
      }
    }
    
    if (selectedArrowId) {
      const arrow = arrows.get(selectedArrowId);
      if (arrow) {
        // Parse handle ID to get source node ID
        const [sourceNodeId, ...sourceHandleParts] = arrow.source.split(':');
        const sourceHandleName = sourceHandleParts.join(':');
        
        // Find source node to determine if this is a special arrow
        const sourceNode = sourceNodeId ? nodes.get(sourceNodeId as any) : undefined;
        const isFromConditionBranch = sourceHandleName === 'true' || sourceHandleName === 'false';
        
        return {
          type: 'arrow' as const,
          id: selectedArrowId,
          data: {
            ...arrow.data,
            content_type: arrow.content_type,
            label: arrow.label,
            id: arrow.id,
            type: 'arrow' as const,
            _sourceNodeType: sourceNode?.type,
            _isFromConditionBranch: isFromConditionBranch
          },
          title: 'Arrow Properties'
        };
      }
    }
    
    return null;
  }, [selectedNodeId, selectedArrowId, selectedPersonId, nodes, arrows, personsWithUsage]);
  
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