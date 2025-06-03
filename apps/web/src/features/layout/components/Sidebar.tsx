// Unified sidebar component that can render as left or right sidebar
import React, { useState, Suspense } from 'react';
import { Button } from '@/shared/components';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { useNodeArrowStore, usePersonStore } from '@/core/stores';
import { usePersons, useSelectedElement, useUIState } from '@/core/hooks/useStoreSelectors';
import { UNIFIED_NODE_CONFIGS, PersonDefinition } from '@/shared/types';
import { useFileImport } from '@/serialization/hooks/useFileImport';
import { FileUploadButton } from '@/shared/components/common/FileUploadButton';
import { useNodeDrag } from '@/features/nodes/hooks/useNodeDrag';

// Lazy load PropertiesRenderer as it's only used in right sidebar
const PropertiesRenderer = React.lazy(() => import('@/features/properties/components/PropertiesRenderer'));

export const DraggableBlock = ({ type, label }: { type: string; label: string }) => {
  const { onDragStart } = useNodeDrag();

  // Extract emoji from label (assuming it's the first character(s))
  const emoji = label.split(' ')[0] || '';
  const text = label.substring((emoji?.length || 0) + 1);

  return (
    <div
      className="p-3 border rounded-lg bg-white hover:bg-gradient-to-br hover:from-blue-50 hover:to-purple-50 cursor-grab text-center text-sm transition-all duration-200 shadow-sm hover:shadow-md hover:border-blue-300 group"
      onDragStart={(event) => onDragStart(event, type)}
      draggable
    >
      <div className="text-lg group-hover:scale-110 transition-transform duration-200">{emoji}</div>
      <div className="text-sm font-medium text-gray-700 leading-tight">{text}</div>
    </div>
  );
};

interface SidebarProps {
  position: 'left' | 'right';
}

const Sidebar: React.FC<SidebarProps> = ({ position }) => {
  const nodes = useNodeArrowStore(state => state.nodes);
  const arrows = useNodeArrowStore(state => state.arrows);
  const { setDashboardTab } = useUIState();
  const { selectedPersonId, setSelectedPersonId, selectedNodeId, selectedArrowId } = useSelectedElement();
  const { persons, addPerson } = usePersons();
  const { handleImportYAML } = useFileImport();
  const [blocksExpanded, setBlocksExpanded] = useState(true);
  const [personsExpanded, setPersonsExpanded] = useState(true);
  const [importExpanded, setImportExpanded] = useState(true);
  
  const handlePersonClick = (personId: string) => {
    setSelectedPersonId(personId);
    setDashboardTab('properties');
  };

  if (position === 'right') {
    return (
      <aside className="h-full border-l bg-gray-50 overflow-y-auto">
        <Suspense fallback={<div className="p-4 text-gray-500">Loading properties...</div>}>
          <PropertiesRenderer
            selectedNodeId={selectedNodeId}
            selectedArrowId={selectedArrowId}
            selectedPersonId={selectedPersonId}
            nodes={nodes}
            arrows={arrows}
            persons={persons}
          />
        </Suspense>
      </aside>
    );
  }

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
              <DraggableBlock type="start" label={`${UNIFIED_NODE_CONFIGS.start?.emoji || '🚀'} ${UNIFIED_NODE_CONFIGS.start?.label || 'Start'} Block`} />
              <DraggableBlock type="person_job" label={`${UNIFIED_NODE_CONFIGS.person_job?.emoji || '🤖'} ${UNIFIED_NODE_CONFIGS.person_job?.label || 'Person Job'} Block`} />
              <DraggableBlock type="person_batch_job" label={`${UNIFIED_NODE_CONFIGS.person_batch_job?.emoji || '🤖📦'} ${UNIFIED_NODE_CONFIGS.person_batch_job?.label || 'Person Batch Job'} Block`} />
              <DraggableBlock type="condition" label={`${UNIFIED_NODE_CONFIGS.condition?.emoji || '🔀'} ${UNIFIED_NODE_CONFIGS.condition?.label || 'Condition'} Block`} />
              <DraggableBlock type="job" label={`${UNIFIED_NODE_CONFIGS.job?.emoji || '⚙️'} ${UNIFIED_NODE_CONFIGS.job?.label || 'Job'} Block`} />
              <DraggableBlock type="endpoint" label={`${UNIFIED_NODE_CONFIGS.endpoint?.emoji || '🎯'} ${UNIFIED_NODE_CONFIGS.endpoint?.label || 'Endpoint'} Block`} />
            </div>
            <h4 className="font-semibold mb-2 mt-4 text-sm text-gray-600 px-2">Data Blocks</h4>
            <div className="grid grid-cols-2 gap-2 px-2">
              <DraggableBlock type="db" label={`${UNIFIED_NODE_CONFIGS.db?.emoji || '📊'} ${UNIFIED_NODE_CONFIGS.db?.label || 'DB Source'} Block`} />
            </div>
          </div>
        )}
      </div>
      
      {/* LLM Persons Section */}
      <div className="flex-1 flex flex-col min-h-0 mb-4">
        <h3 
          className="font-semibold flex items-center justify-between cursor-pointer hover:bg-white/50 p-2 rounded-lg mb-2 transition-colors duration-200"
          onClick={() => setPersonsExpanded(!personsExpanded)}
        >
          <span className="flex items-center gap-2">
            <span className="text-base">👥</span>
            <span className="text-base font-medium">LLM Persons</span>
            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-normal">{persons.length}</span>
          </span>
          {personsExpanded ? <ChevronDown size={16} className="text-gray-500" /> : <ChevronRight size={16} className="text-gray-500" />}
        </h3>
        {personsExpanded && (
          <div className="flex-1 flex flex-col min-h-0">
            <Button
              variant="outline"
              className="w-full text-base py-2 mb-2 flex-shrink-0 mx-2 hover:bg-blue-50 hover:border-blue-300 transition-colors duration-200"
              onClick={() => {
                // Create person with default values including service field
                addPerson({ 
                  label: 'New Person',
                  service: 'openai', // Default service
                  apiKeyId: undefined,
                  modelName: undefined,
                  systemPrompt: undefined
                });
                // Get the newly created person's ID and select it
                const newPersonId = usePersonStore.getState().persons[usePersonStore.getState().persons.length - 1]?.id;
                if (newPersonId) {
                  handlePersonClick(newPersonId);
                }
              }}
            >
              <span className="mr-1">➕</span> Add Person
            </Button>
            <div className="flex-1 overflow-y-auto space-y-1 px-2">
              {persons.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-4 italic">No persons created</p>
              ) : (
                persons.map((person: PersonDefinition) => (
                  <div
                    key={person.id}
                    className={`p-3 text-base rounded-lg cursor-pointer transition-all duration-200 ${
                      selectedPersonId === person.id 
                        ? 'bg-gradient-to-r from-blue-100 to-purple-100 border border-blue-400 shadow-sm' 
                        : 'bg-white hover:bg-gray-50 hover:shadow-sm'
                    }`}
                    onClick={() => handlePersonClick(person.id)}
                    title={person.label || 'Unnamed Person'}
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-base">🤖</span>
                      <div className="truncate font-medium">
                        {person.label || 'Unnamed Person'}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
      
      {/* Import Section */}
      <div>
        <h3 
          className="font-semibold flex items-center justify-between cursor-pointer hover:bg-white/50 p-2 rounded-lg mb-2 transition-colors duration-200"
          onClick={() => setImportExpanded(!importExpanded)}
        >
          <span className="flex items-center gap-2">
            <span className="text-base">📁</span>
            <span className="text-base font-medium">Import</span>
          </span>
          {importExpanded ? <ChevronDown size={16} className="text-gray-500" /> : <ChevronRight size={16} className="text-gray-500" />}
        </h3>
        {importExpanded && (
          <div className="px-2">
            <FileUploadButton
              accept=".yaml,.yml"
              onChange={handleImportYAML}
              variant="outline"
              className="w-full text-sm py-2 hover:bg-green-50 hover:border-green-300 transition-colors duration-200"
              size="sm"
            >
              <span className="mr-1">📄</span> Import YAML
            </FileUploadButton>
          </div>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;