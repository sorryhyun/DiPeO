// Reusable component for rendering property panels based on selection
import React, { useMemo, Suspense } from 'react';
import { DiagramNode, Arrow, PersonDefinition, ArrowData } from '../../../types';

// Lazy load UniversalPropertiesPanel as it's a heavy component
const UniversalPropertiesPanel = React.lazy(() => 
  import('./UniversalPropertiesPanel').then(module => ({ 
    default: module.UniversalPropertiesPanel 
  }))
);

interface PropertiesRendererProps {
  selectedNodeId?: string | null;
  selectedArrowId?: string | null;
  selectedPersonId?: string | null;
  nodes: DiagramNode[];
  arrows: Arrow<ArrowData>[];
  persons: PersonDefinition[];
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
  // Memoize person data to avoid creating new object references
  const personData = useMemo(() => {
    if (!selectedPersonId) return null;
    const person = persons.find(p => p.id === selectedPersonId);
    if (!person) return null;
    return { ...person, type: 'person' as const };
  }, [selectedPersonId, persons]);

  // Memoize arrow data to avoid creating new object references
  const arrowData = useMemo(() => {
    if (!selectedArrowId) return null;
    const arrow = arrows.find(a => a.id === selectedArrowId);
    if (!arrow || !arrow.data) return null;
    
    // Find source node to determine if this is a special arrow
    const sourceNode = nodes.find(n => n.id === arrow.source);
    const isFromConditionBranch = arrow.sourceHandle === 'true' || arrow.sourceHandle === 'false';
    
    // Ensure we have a valid id from arrow data
    const arrowDataWithType = { 
      ...arrow.data,
      id: arrow.data.id || arrow.id, // Ensure id is always present
      type: 'arrow' as const,
      _sourceNodeType: sourceNode?.data.type,
      _isFromConditionBranch: isFromConditionBranch
    };
    
    return arrowDataWithType;
  }, [selectedArrowId, arrows, nodes]);

  const getPropertiesContent = (): PropertiesResult => {
    let content = <p className="p-4 text-sm text-gray-500">Select a block, arrow, or person to see its properties.</p>;
    let title = "Properties";

    if (selectedPersonId && personData) {
      title = `${personData.label || 'Person'} Properties`;
      content = (
        <Suspense fallback={<div className="p-4 text-gray-500">Loading properties...</div>}>
          <UniversalPropertiesPanel nodeId={selectedPersonId} data={personData} />
        </Suspense>
      );
    } else if (selectedNodeId) {
      const node = nodes.find(n => n.id === selectedNodeId);
      if (node) {
        title = `${node.data.label || 'Block'} Properties`;
        content = (
          <Suspense fallback={<div className="p-4 text-gray-500">Loading properties...</div>}>
            <UniversalPropertiesPanel nodeId={selectedNodeId} data={node.data} />
          </Suspense>
        );
      }
    } else if (selectedArrowId && arrowData) {
      title = `Arrow Properties`;
      content = (
        <Suspense fallback={<div className="p-4 text-gray-500">Loading properties...</div>}>
          <UniversalPropertiesPanel nodeId={selectedArrowId} data={arrowData} />
        </Suspense>
      );
    }

    return { title, content };
  };

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