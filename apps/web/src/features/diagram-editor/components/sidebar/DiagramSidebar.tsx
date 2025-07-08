// Diagram-specific sidebar component
import React, { useState } from 'react';
import { Button } from '@/shared/components/forms/buttons';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { getNodeConfig } from '@/features/diagram-editor/config/nodes';
import { NodeType } from '@dipeo/domain-models';
import { useCanvas, useCanvasInteractions, usePersonOperations } from '@/features/diagram-editor/hooks';
import { useUnifiedStore } from '@/core/store/unifiedStore';
import { LazyApiKeysModal } from '@/shared/components/feedback/LazyModals';
import { FileOperations } from '@/features/diagram-editor/components/file-operations/FileOperations';
import { PersonID, DomainPerson, personId } from '@/core/types';
import { SidebarLayout } from '@/shared/components/layout/SidebarLayout';

// Memoized draggable block component
export const DraggableBlock = React.memo<{ type: string; label: string }>(({ type, label }) => {
  const { onNodeDragStart } = useCanvasInteractions();

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

// Memoized person item component
const PersonItem = React.memo<{
  person: { id: string; label: string };
  isSelected: boolean;
  isHighlighted: boolean;
  onClick: (id: string) => void;
}>(({ person, isSelected, isHighlighted, onClick }) => {
  return (
    <div
      className={`p-2 rounded-lg cursor-pointer transition-all duration-200 text-sm ${
        isSelected
          ? 'bg-blue-100 border border-blue-300 shadow-sm'
          : isHighlighted
          ? 'bg-yellow-100 border border-yellow-300 shadow-sm'
          : 'bg-gray-100 border border-gray-200 hover:bg-gray-200 hover:border-gray-300'
      }`}
      onClick={() => onClick(person.id)}
    >
      <div className="flex items-center gap-2">
        <span className="text-base">👤</span>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-xs truncate">{person.label}</p>
        </div>
      </div>
    </div>
  );
});

PersonItem.displayName = 'PersonItem';

export const DiagramSidebar = React.memo(() => {
  const { personsArray } = useCanvas();
  const { addPerson } = usePersonOperations();
  const { selectedId, selectedType, select, clearSelection, persons: personsMap, highlightedPersonId } = useUnifiedStore();
  
  // Helper to get person by ID
  const getPersonById = (id: PersonID) => personsMap.get(id) || null;
  
  // Convert persons array to PersonID array like the old hook did
  const persons = React.useMemo(
    () => personsArray.map((p: DomainPerson) => personId(p.id)),
    [personsArray]
  );
  
  // Derive selected person ID
  const selectedPersonId = selectedType === 'person' ? selectedId : null;
  
  const setSelectedPersonId = (id: PersonID | null) => {
    if (id) select(id, 'person');
    else clearSelection();
  };

  const [blocksExpanded, setBlocksExpanded] = useState(true);
  const [personsExpanded, setPersonsExpanded] = useState(true);
  const [isApiModalOpen, setIsApiModalOpen] = useState(false);
  const [fileOperationsExpanded, setFileOperationsExpanded] = useState(false);
  
  const handlePersonClick = (personId: string) => {
    setSelectedPersonId(personId as PersonID);
  };

  return (
    <SidebarLayout position="left">
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
              <DraggableBlock type="start" label={`${getNodeConfig(NodeType.START)?.icon || '🚀'} ${getNodeConfig(NodeType.START)?.label || 'Start'}`} />
              <DraggableBlock type="person_job" label={`${getNodeConfig(NodeType.PERSON_JOB)?.icon || '🤖'} ${getNodeConfig(NodeType.PERSON_JOB)?.label || 'Person Job'}`} />
              <DraggableBlock type="person_batch_job" label={`${getNodeConfig(NodeType.PERSON_BATCH_JOB)?.icon || '🤖📦'} ${getNodeConfig(NodeType.PERSON_BATCH_JOB)?.label || 'Person Batch Job'}`} />
              <DraggableBlock type="condition" label={`${getNodeConfig(NodeType.CONDITION)?.icon || '🔀'} ${getNodeConfig(NodeType.CONDITION)?.label || 'Condition'}`} />
              <DraggableBlock type="code_job" label={`${getNodeConfig(NodeType.CODE_JOB)?.icon || '📝'} ${getNodeConfig(NodeType.CODE_JOB)?.label || 'Code Job'}`} />
              <DraggableBlock type="api_job" label={`${getNodeConfig(NodeType.API_JOB)?.icon || '🌐'} ${getNodeConfig(NodeType.API_JOB)?.label || 'API Job'}`} />
              <DraggableBlock type="user_response" label={`${getNodeConfig(NodeType.USER_RESPONSE)?.icon || '💬'} ${getNodeConfig(NodeType.USER_RESPONSE)?.label || 'User Response'}`} />
              <DraggableBlock type="endpoint" label={`${getNodeConfig(NodeType.ENDPOINT)?.icon || '🎯'} ${getNodeConfig(NodeType.ENDPOINT)?.label || 'Endpoint'}`} />
            </div>
            <h4 className="font-semibold mb-2 mt-4 text-sm text-gray-600 px-2">Data Blocks</h4>
            <div className="grid grid-cols-2 gap-2 px-2">
              <DraggableBlock type="db" label={`${getNodeConfig(NodeType.DB)?.icon || '📊'} ${getNodeConfig(NodeType.DB)?.label || 'DB Source'} Block`} />
              <DraggableBlock type="hook" label={`${getNodeConfig(NodeType.HOOK)?.icon || '🪝'} ${getNodeConfig(NodeType.HOOK)?.label || 'Hook'}`} />
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
                    isHighlighted={highlightedPersonId === person.id}
                    onClick={handlePersonClick}
                  />
                );
              })}
            </div>
            <Button
              variant="outline"
              className="w-full mt-2 text-sm py-2 hover:bg-blue-50 hover:border-blue-300 transition-colors duration-200"
              size="sm"
              onClick={() => addPerson(
                `Person ${persons.length + 1}`,
                'openai',
                'gpt-4.1-nano'
              )}
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
            <span className="text-base font-medium">Other formats</span>
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
    </SidebarLayout>
  );
});

DiagramSidebar.displayName = 'DiagramSidebar';

export default DiagramSidebar;