// Unified sidebar component that can render as left or right sidebar
import React, { useState } from 'react';
import { Button } from '@/shared/components';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { useConsolidatedDiagramStore } from '@/shared/stores';
import { usePersons, useSelectedElement, useUIState } from '@/shared/hooks/useStoreSelectors';
import { UNIFIED_NODE_CONFIGS } from '@/shared/types';
import { useFileImport } from '@/features/diagram/hooks/useFileImport';
import PropertiesRenderer from '@/features/properties/components/PropertiesRenderer';
import { FileUploadButton } from '@/shared/components/common/FileUploadButton';
import { useNodeDrag } from '@/features/nodes/hooks/useNodeDrag';

export const DraggableBlock = ({ type, label }: { type: string; label: string }) => {
  const { onDragStart } = useNodeDrag();

  // Extract emoji from label (assuming it's the first character(s))
  const emoji = label.split(' ')[0];
  const text = label.substring(emoji.length + 1);

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
  const nodes = useConsolidatedDiagramStore(state => state.nodes);
  const arrows = useConsolidatedDiagramStore(state => state.arrows);
  const { setDashboardTab } = useUIState();
  const { selectedPersonId, setSelectedPersonId, selectedNodeId, selectedArrowId } = useSelectedElement();
  const { persons, addPerson } = usePersons();
  const { handleImportUML, handleImportYAML } = useFileImport();
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
        <PropertiesRenderer
          selectedNodeId={selectedNodeId}
          selectedArrowId={selectedArrowId}
          selectedPersonId={selectedPersonId}
          nodes={nodes}
          arrows={arrows}
          persons={persons}
        />
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
              <DraggableBlock type="start" label={`${UNIFIED_NODE_CONFIGS.start.emoji} ${UNIFIED_NODE_CONFIGS.start.label} Block`} />
              <DraggableBlock type="person_job" label={`${UNIFIED_NODE_CONFIGS.person_job.emoji} ${UNIFIED_NODE_CONFIGS.person_job.label} Block`} />
              <DraggableBlock type="condition" label={`${UNIFIED_NODE_CONFIGS.condition.emoji} ${UNIFIED_NODE_CONFIGS.condition.label} Block`} />
              <DraggableBlock type="job" label={`${UNIFIED_NODE_CONFIGS.job.emoji} ${UNIFIED_NODE_CONFIGS.job.label} Block`} />
              <DraggableBlock type="endpoint" label={`${UNIFIED_NODE_CONFIGS.endpoint.emoji} ${UNIFIED_NODE_CONFIGS.endpoint.label} Block`} />
            </div>
            <h4 className="font-semibold mb-2 mt-4 text-sm text-gray-600 px-2">Data Blocks</h4>
            <div className="grid grid-cols-2 gap-2 px-2">
              <DraggableBlock type="db" label={`${UNIFIED_NODE_CONFIGS.db.emoji} ${UNIFIED_NODE_CONFIGS.db.label} Block`} />
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
                addPerson({ label: 'New Person' });
                // Get the newly created person's ID and select it
                const newPersonId = useConsolidatedDiagramStore.getState().persons[useConsolidatedDiagramStore.getState().persons.length - 1]?.id;
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
                persons.map((person: any) => (
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
          <div className="grid grid-cols-2 gap-2 px-2">
            <FileUploadButton
              accept=".puml,.mmd"
              onChange={handleImportUML}
              variant="outline"
              className="text-sm py-2 hover:bg-purple-50 hover:border-purple-300 transition-colors duration-200"
              size="sm"
            >
              <span className="mr-1">📋</span> UML
            </FileUploadButton>
            <FileUploadButton
              accept=".yaml,.yml"
              onChange={handleImportYAML}
              variant="outline"
              className="text-sm py-2 hover:bg-green-50 hover:border-green-300 transition-colors duration-200"
              size="sm"
            >
              <span className="mr-1">📄</span> YAML
            </FileUploadButton>
          </div>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;