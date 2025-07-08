import React, { Suspense, useCallback } from 'react';
import { useCanvas } from '@/features/diagram-editor/hooks';
import { useUnifiedStore } from '@/core/store/unifiedStore';
import { LoadingFallback } from '@/shared/components/feedback';

// Lazy load the property panel
const PropertyPanel = React.lazy(() => import('./PropertyPanel').then(module => ({ default: module.PropertyPanel })));

export const PropertiesTab: React.FC = () => {
  const { nodes, arrows, personsArray } = useCanvas();
  const { selectedId, selectedType } = useUnifiedStore();
  
  // Find person data
  const personData = selectedType === 'person' && selectedId && personsArray 
    ? personsArray.find(p => p.id === selectedId)
    : null;

  // Find and process arrow data
  const arrowData = (() => {
    if (selectedType !== 'arrow' || !selectedId || !arrows) return null;
    const arrow = arrows.find(a => a.id === selectedId);
    if (!arrow?.data) return null;
    
    // Parse handle ID to get source node ID
    const [sourceNodeId, ...sourceHandleParts] = arrow.source.split(':');
    const sourceHandleName = sourceHandleParts.join(':');
    
    // Find source node to determine if this is a special arrow
    const sourceNode = nodes?.find(n => n.id === sourceNodeId);
    const isFromConditionBranch = sourceHandleName === 'true' || sourceHandleName === 'false';
    
    // Ensure we have a valid id from arrow data
    return { 
      ...arrow.data,
      content_type: arrow.content_type,  // Include direct property
      label: arrow.label,                 // Include direct property
      id: arrow.id, // Use arrow's id directly
      type: 'arrow' as const,
      _sourceNodeType: sourceNode?.type,
      _isFromConditionBranch: isFromConditionBranch
    };
  })();

  const getPropertiesContent = useCallback(() => {
    let content = <p className="p-4 text-sm text-gray-500">Select a block, arrow, or person to see its properties.</p>;
    let title = "Properties";

    if (selectedType === 'person' && selectedId && personData) {
      title = `${personData.label || 'Person'} Properties`;
      content = (
        <Suspense fallback={<LoadingFallback />}>
          <PropertyPanel entityId={selectedId} data={{ ...personData, type: 'person' as const }} />
        </Suspense>
      );
    } else if (selectedType === 'node' && selectedId) {
      const node = nodes?.find(n => n.id === selectedId);
      if (node) {
        // Safely access node.data which might be null
        const nodeData = node.data || {};
        const label = nodeData.label || 'Block';
        title = `${label} Properties`;
        content = (
          <Suspense fallback={<LoadingFallback />}>
            <PropertyPanel entityId={selectedId} data={{ ...nodeData, type: node.type || 'unknown' }} />
          </Suspense>
        );
      }
    } else if (selectedType === 'arrow' && selectedId && arrowData) {
      title = `Arrow Properties`;
      content = (
        <Suspense fallback={<LoadingFallback />}>
          <PropertyPanel entityId={selectedId} data={arrowData} />
        </Suspense>
      );
    }

    return { title, content };
  }, [selectedType, selectedId, personData, nodes, arrowData]);

  const { title, content } = getPropertiesContent();
  const showWrapperHeader = !selectedId;

  return (
    <div className="h-full flex flex-col">
      {showWrapperHeader && (
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold">{title}</h2>
        </div>
      )}
      <div className="flex-1 overflow-y-auto">
        {content}
      </div>
    </div>
  );
};

export default PropertiesTab;