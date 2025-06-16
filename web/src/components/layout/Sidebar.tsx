// Unified sidebar component that can render as left or right sidebar
import React, { useState, Suspense } from 'react';
import { Button } from '@/components/ui/buttons';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { getNodeConfig } from '@/config';
import { useCanvasOperations } from '@/hooks/useCanvasOperations';
import { LazyApiKeysModal } from '@/components/modals/LazyModals';
import { FileOperations } from '@/components/sidebar/FileOperations';
import type { PersonID } from '@/types/branded';
import type { Node } from '@xyflow/react';

// Lazy load UniversalPropertiesPanel as it's only used in right sidebar
const PropertiesPanel = React.lazy(() => import('@/components/properties/PropertiesPanel').then(m => ({ default: m.UniversalPropertiesPanel })));
import type { UniversalData } from '@/components/properties/PropertiesPanel';

// Memoized draggable block component
export const DraggableBlock = React.memo<{ type: string; label: string }>(({ type, label }) => {
  const { onNodeDragStart } = useCanvasOperations();

  // Extract emoji from label (assuming it's the first character(s))
  const icon = label.split(' ')[0] || '';
  const text = label.substring((icon?.length || 0) + 1);

  return (
    <div
      className="p-2 border rounded-lg bg-white hover:bg-gradient-to-br hover:from-blue-50 hover:to-purple-50 cursor-grab text-center text-sm transition-all duration-200 shadow-sm hover:shadow-md hover:border-blue-300 group"
      onDragStart={(event) => onNodeDragStart(event, type)}
      draggable
    >
      <div className="text-base group-hover:scale-110 transition-transform duration-200">{icon}</div>
      <div className="text-sm font-medium text-gray-700 leading-tight">{text}</div>
    </div>
  );
});

DraggableBlock.displayName = 'DraggableBlock';

interface SidebarProps {
  position: 'left' | 'right';
}

// Memoized person item component
const PersonItem = React.memo<{
  person: { id: string; label: string };
  isSelected: boolean;
  onClick: (id: string) => void;
}>(({ person, isSelected, onClick }) => {
  return (
    <div
      className={`p-2 rounded-lg cursor-pointer transition-all duration-200 text-sm ${
        isSelected
          ? 'bg-blue-100 border border-blue-300 shadow-sm'
          : 'bg-gray-100 border border-gray-200 hover:bg-gray-200 hover:border-gray-300'
      }`}
      onClick={() => onClick(person.id)}
    >
      <div className="flex items-center gap-2">
        <span className="text-base">🤖</span>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-xs truncate">{person.label}</p>
        </div>
      </div>
    </div>
  );
});

PersonItem.displayName = 'PersonItem';

const Sidebar = React.memo<SidebarProps>(({ position }) => {
  const canvas = useCanvasOperations();
  const { 
    nodes, 
    persons, 
    addPerson,
    selectedId,
    selectedType,
    select,
    clearSelection,
    getPersonById
  } = canvas;
  
  // Derive selected IDs based on selectedType
  const selectedNodeId = selectedType === 'node' ? selectedId : null;
  const selectedArrowId = selectedType === 'arrow' ? selectedId : null;
  const selectedPersonId = selectedType === 'person' ? selectedId : null;
  
  const setSelectedPersonId = (id: PersonID | null) => {
    if (id) select(id, 'person');
    else clearSelection();
  };
  const [blocksExpanded, setBlocksExpanded] = useState(true);
  const [personsExpanded, setPersonsExpanded] = useState(true);
  const [_conversationExpanded, _setConversationExpanded] = useState(true);
  const [_memoryExpanded, _setMemoryExpanded] = useState(true);
  const [isApiModalOpen, setIsApiModalOpen] = useState(false);
  const [fileOperationsExpanded, setFileOperationsExpanded] = useState(false);
  
  const handlePersonClick = (personId: string) => {
    setSelectedPersonId(personId as PersonID);
  };

  if (position === 'right') {
    // Find the selected element and its data
    let selectedId: string | null = null;
    let selectedData: UniversalData | null = null;
    
    if (selectedNodeId) {
      const node = nodes.find((n: Node) => n.id === selectedNodeId);
      if (node) {
        selectedId = node.id;
        selectedData = { ...node.data, type: node.type || 'unknown' };
      }
    } else if (selectedArrowId) {
      // For arrows, we need to get the arrow data from the store
      // Since arrows array only contains IDs, we'll skip arrow properties for now
      selectedId = selectedArrowId;
      selectedData = { type: 'arrow' };
    } else if (selectedPersonId) {
      const person = getPersonById(selectedPersonId as PersonID);
      if (person) {
        selectedId = selectedPersonId;
        selectedData = { ...person, type: 'person' };
      }
    }
    
    return (
      <aside className="h-full border-l bg-gray-50 overflow-y-auto">
        <Suspense fallback={<div className="p-4 text-gray-500">Loading properties...</div>}>
          {selectedId && selectedData ? (
            <PropertiesPanel nodeId={selectedId} data={selectedData} />
          ) : (
            <div className="p-4 text-gray-500">Select an element to view properties</div>
          )}
        </Suspense>
      </aside>
    );
  }

  // Left sidebar - regular mode
  return (
    <aside className="h-full p-4 border-r bg-gradient-to-b from-gray-50 to-gray-100 flex flex-col overflow-hidden">
      {/* Blocks Palette Section */}
      <div className="mb-4">
        <h3 
          className="font-semibold flex items-center justify-between cursor-pointer hover:bg-white/50 p-2 rounded-lg transition-colors duration-200"
          onClick={() => setBlocksExpanded(!blocksExpanded)}
        >
          <span className="flex items-center gap-2">
            <span className="text-base">🎨</span>
            <span className="text-base font-medium">Blocks Palette</span>
          </span>
          {blocksExpanded ? <ChevronDown size={16} className="text-gray-500" /> : <ChevronRight size={16} className="text-gray-500" />}
        </h3>
        {blocksExpanded && (
          <div className="mt-3">
            <h4 className="font-semibold mb-2 text-sm text-gray-600 px-2">Job Blocks</h4>
            <div className="grid grid-cols-2 gap-2 px-2">
              <DraggableBlock type="start" label={`${getNodeConfig('start').icon || '🚀'} ${getNodeConfig('start')?.label || 'Start'}`} />
              <DraggableBlock type="person_job" label={`${getNodeConfig('person_job')?.icon || '🤖'} ${getNodeConfig('person_job').label || 'Person Job'}`} />
              <DraggableBlock type="person_batch_job" label={`${getNodeConfig('person_batch_job').icon || '🤖📦'} ${getNodeConfig('person_batch_job').label || 'Person Batch Job'}`} />
              <DraggableBlock type="condition" label={`${getNodeConfig('condition').icon || '🔀'} ${getNodeConfig('condition').label || 'Condition'}`} />
              <DraggableBlock type="job" label={`${getNodeConfig('job').icon || '⚙️'} ${getNodeConfig('job').label || 'Job'}`} />
              <DraggableBlock type="user_response" label={`${getNodeConfig('user_response').icon || '💬'} ${getNodeConfig('user_response').label || 'User Response'}`} />
              <DraggableBlock type="endpoint" label={`${getNodeConfig('endpoint').icon || '🎯'} ${getNodeConfig('endpoint').label || 'Endpoint'}`} />
            </div>
            <h4 className="font-semibold mb-2 mt-4 text-sm text-gray-600 px-2">Data Blocks</h4>
            <div className="grid grid-cols-2 gap-2 px-2">
              <DraggableBlock type="db" label={`${getNodeConfig('db').icon || '📊'} ${getNodeConfig('db').label || 'DB Source'} Block`} />
            </div>
          </div>
        )}
      </div>

      {/* API Keys Button */}
      <div className="mb-4 px-2">
        <Button 
          variant="outline" 
          className="w-full bg-white hover:bg-purple-50 hover:border-purple-300 transition-colors duration-200 py-2"
          onClick={() => setIsApiModalOpen(true)}
        >
          🔑 API Keys
        </Button>
      </div>

      {/* Persons Section */}
      <div className="mb-4">
        <h3 
          className="font-semibold flex items-center justify-between cursor-pointer hover:bg-white/50 p-2 rounded-lg transition-colors duration-200"
          onClick={() => setPersonsExpanded(!personsExpanded)}
        >
          <span className="flex items-center gap-2">
            <span className="text-base">👥</span>
            <span className="text-base font-medium">Persons ({persons.length})</span>
          </span>
          {personsExpanded ? <ChevronDown size={16} className="text-gray-500" /> : <ChevronRight size={16} className="text-gray-500" />}
        </h3>
        {personsExpanded && (
          <div className="mt-3 max-h-48 overflow-y-auto px-2">
            <div className="space-y-1">
              {persons.map((personId) => {
                const person = getPersonById(personId);
                if (!person) return null;
                return (
                  <PersonItem
                    key={person.id}
                    person={person}
                    isSelected={selectedPersonId === person.id}
                    onClick={handlePersonClick}
                  />
                );
              })}
            </div>
            <Button
              variant="outline"
              className="w-full mt-2 text-sm py-2 hover:bg-blue-50 hover:border-blue-300 transition-colors duration-200"
              size="sm"
              onClick={() => addPerson({
                label: `Person ${persons.length + 1}`,
                model: 'gpt-4.1-nano',
                service: 'openai',
              })}
            >
              <span className="mr-1">➕</span> Add Person
            </Button>
          </div>
        )}
      </div>

      {/* File Operations Section */}
      <div className="mb-4">
        <h3 
          className="font-semibold flex items-center justify-between cursor-pointer hover:bg-white/50 p-2 rounded-lg transition-colors duration-200"
          onClick={() => setFileOperationsExpanded(!fileOperationsExpanded)}
        >
          <span className="flex items-center gap-2">
            <span className="text-base">📁</span>
            <span className="text-base font-medium">Import / Export</span>
          </span>
          {fileOperationsExpanded ? <ChevronDown size={16} className="text-gray-500" /> : <ChevronRight size={16} className="text-gray-500" />}
        </h3>
        {fileOperationsExpanded && (
          <div className="mt-3 px-2">
            <FileOperations />
          </div>
        )}
      </div>
      
      <LazyApiKeysModal isOpen={isApiModalOpen} onClose={() => setIsApiModalOpen(false)} />
    </aside>
  );
});

Sidebar.displayName = 'Sidebar';

export default Sidebar;