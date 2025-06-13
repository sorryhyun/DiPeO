// Reusable component for rendering property panels based on selection
import React, { Suspense, useCallback } from 'react';
import { DomainArrow, DomainPerson, DiPeoNode, Dict } from '@/types';
import { LoadingFallback } from '@/components/ui/feedback';

// Lazy load PropertiesPanel as it's a heavy component
const UniversalPropertiesPanel = React.lazy(() => 
  import('../PropertiesPanel/PropertiesPanel').then(module => ({ 
    default: module.UniversalPropertiesPanel 
  }))
);

interface PropertiesRendererProps {
  // Optional override - if not provided, uses UI store
  selectedNodeId?: string | null;
  selectedArrowId?: string | null;
  selectedPersonId?: string | null;
  nodes?: DiPeoNode[];
  arrows?: DomainArrow[];
  persons?: DomainPerson[];
}

interface PropertiesResult {
  title: string;
  content: React.ReactNode;
}

const PropertiesRenderer: React.FC<PropertiesRendererProps> = ({
  selectedNodeId,
  selectedArrowId,
  selectedPersonId,
  nodes,
  arrows,
  persons
}) => {
  // Find person data
  const personData = selectedPersonId && persons 
    ? persons.find(p => p.id === selectedPersonId)
    : null;

  // Find and process arrow data
  const arrowData = (() => {
    if (!selectedArrowId || !arrows) return null;
    const arrow = arrows.find(a => a.id === selectedArrowId);
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
      id: arrow.id, // Use arrow's id directly
      type: 'arrow' as const,
      _sourceNodeType: sourceNode?.type,
      _isFromConditionBranch: isFromConditionBranch
    };
  })();

  const getPropertiesContent = useCallback((): PropertiesResult => {
    let content = <p className="p-4 text-sm text-gray-500">Select a block, arrow, or person to see its properties.</p>;
    let title = "Properties";

    if (selectedPersonId && personData) {
      title = `${personData.label || 'Person'} Properties`;
      content = (
        <Suspense fallback={<LoadingFallback />}>
          <UniversalPropertiesPanel nodeId={selectedPersonId} data={{ ...personData, type: 'person' as const }} />
        </Suspense>
      );
    } else if (selectedNodeId) {
      const node = nodes?.find(n => n.id === selectedNodeId);
      if (node) {
        title = `${node.data.label || 'Block'} Properties`;
        content = (
          <Suspense fallback={<LoadingFallback />}>
            <UniversalPropertiesPanel nodeId={selectedNodeId} data={{ ...node.data, type: node.type || 'unknown' }} />
          </Suspense>
        );
      }
    } else if (selectedArrowId && arrowData) {
      title = `Arrow Properties`;
      content = (
        <Suspense fallback={<LoadingFallback />}>
          <UniversalPropertiesPanel nodeId={selectedArrowId} data={arrowData} />
        </Suspense>
      );
    }

    return { title, content };
  }, [selectedPersonId, personData, selectedNodeId, nodes, selectedArrowId, arrowData]);

  const { title, content } = getPropertiesContent();
  const showWrapperHeader = !selectedPersonId && !selectedNodeId && !selectedArrowId;

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

export default PropertiesRenderer;