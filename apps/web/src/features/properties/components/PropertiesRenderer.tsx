// Reusable component for rendering property panels based on selection
import React from 'react';
import { UniversalPropertiesPanel } from './PropertyPanels';

interface PropertiesRendererProps {
  selectedNodeId?: string | null;
  selectedArrowId?: string | null;
  selectedPersonId?: string | null;
  nodes: any[];
  arrows: any[];
  persons: any[];
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
  const getPropertiesContent = (): PropertiesResult => {
    let content = <p className="p-4 text-sm text-gray-500">Select a block, arrow, or person to see its properties.</p>;
    let title = "Properties";

    if (selectedPersonId) {
      const person = persons.find(p => p.id === selectedPersonId);
      if (person) {
        title = `${person.label || 'Person'} Properties`;
        content = <UniversalPropertiesPanel nodeId={selectedPersonId} data={{...person, type: 'person'}} />;
      }
    } else if (selectedNodeId) {
      const node = nodes.find(n => n.id === selectedNodeId);
      if (node) {
        title = `${node.data.label || 'Block'} Properties`;
        content = <UniversalPropertiesPanel nodeId={selectedNodeId} data={node.data} />;
      }
    } else if (selectedArrowId) {
      const arrow = arrows.find(a => a.id === selectedArrowId);
      if (arrow) {
        title = `Arrow Properties`;
        content = <UniversalPropertiesPanel nodeId={selectedArrowId} data={{...arrow.data, type: 'arrow'}} />;
      }
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