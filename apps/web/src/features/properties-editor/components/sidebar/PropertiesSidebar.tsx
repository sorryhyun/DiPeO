// Properties-specific sidebar component
import React, { Suspense } from 'react';
import { useCanvas } from '@/features/diagram-editor/hooks';
import { useUnifiedStore } from '@/core/store/unifiedStore';
import { PersonID, DomainArrow } from '@/core/types';
import type { Node } from '@xyflow/react';
import { SidebarLayout } from '@/shared/components/layout/SidebarLayout';

// Lazy load PropertyPanel as it's only used in right sidebar
const PropertiesPanelComponent = React.lazy(() => import('@/features/properties-editor/components/PropertyPanel').then(m => ({ default: m.PropertyPanel })));
import type { UniversalData } from '@/features/properties-editor/components/PropertyPanel';

export const PropertiesSidebar = React.memo(() => {
  const { nodes, arrows } = useCanvas();
  const { selectedId, selectedType, persons: personsMap } = useUnifiedStore();
  
  // Helper to get person by ID
  const getPersonById = (id: PersonID) => personsMap.get(id) || null;
  
  // Derive selected IDs based on selectedType
  const selectedNodeId = selectedType === 'node' ? selectedId : null;
  const selectedArrowId = selectedType === 'arrow' ? selectedId : null;
  const selectedPersonId = selectedType === 'person' ? selectedId : null;

  // Find the selected element and its data
  let selectedIdToShow: string | null = null;
  let selectedData: UniversalData | null = null;
  
  if (selectedNodeId) {
    const node = nodes.find((n: Node) => n.id === selectedNodeId);
    if (node) {
      selectedIdToShow = node.id;
      selectedData = { ...node.data, type: node.type || 'unknown' };
    }
  } else if (selectedArrowId) {
    // Get arrow data from the arrows array
    const arrow = arrows.find((a: DomainArrow) => a.id === selectedArrowId);
    if (arrow) {
      selectedIdToShow = selectedArrowId;
      // Parse handle ID to get source node ID
      const [sourceNodeId] = arrow.source.split(':');
      const sourceNode = nodes.find((n: Node) => n.id === sourceNodeId);
      
      selectedData = { 
        ...arrow.data,
        id: arrow.id,
        type: 'arrow' as const,
        content_type: arrow.content_type,
        label: arrow.label,
        _sourceNodeType: sourceNode?.type
      };
    }
  } else if (selectedPersonId) {
    const person = getPersonById(selectedPersonId as PersonID);
    if (person) {
      selectedIdToShow = selectedPersonId;
      selectedData = { ...person, type: 'person' };
    }
  }
  
  return (
    <SidebarLayout position="right">
      <Suspense fallback={<div className="p-4 text-gray-500">Loading properties...</div>}>
        {selectedIdToShow && selectedData ? (
          <PropertiesPanelComponent entityId={selectedIdToShow} data={selectedData} />
        ) : (
          <div className="p-4 text-gray-500">Select an element to view properties</div>
        )}
      </Suspense>
    </SidebarLayout>
  );
});

PropertiesSidebar.displayName = 'PropertiesSidebar';

export default PropertiesSidebar;