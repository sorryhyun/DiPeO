// Unified sidebar component that can render as left or right sidebar
import React, { useState, Suspense } from 'react';
import { Button } from '@/components/common/Button';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { NODE_CONFIGS, PersonDefinition } from '@/types';
import { useFileImport } from '@/hooks/useFileImport';
import { useExport } from '@/hooks/useExport';
import { FileUploadButton } from '@/components/common/common/FileUploadButton';
import { useNodeDrag } from '@/hooks/useNodeDrag';
import { 
  useNodes, 
  useArrows, 
  usePersons,
  useSelectedElement 
} from '@/hooks/useStoreSelectors';

// Lazy load UniversalPropertiesPanel as it's only used in right sidebar
const PropertiesPanel = React.lazy(() => import('@/components/panels/UniversalPropertiesPanel').then(m => ({ default: m.UniversalPropertiesPanel })));

export const DraggableBlock = ({ type, label }: { type: string; label: string }) => {
  const { onDragStart } = useNodeDrag();

  // Extract emoji from label (assuming it's the first character(s))
  const icon = label.split(' ')[0] || '';
  const text = label.substring((icon?.length || 0) + 1);

  return (
    <div
      className="p-3 border rounded-lg bg-white hover:bg-gradient-to-br hover:from-blue-50 hover:to-purple-50 cursor-grab text-center text-sm transition-all duration-200 shadow-sm hover:shadow-md hover:border-blue-300 group"
      onDragStart={(event) => onDragStart(event, type)}
      draggable
    >
      <div className="text-lg group-hover:scale-110 transition-transform duration-200">{icon}</div>
      <div className="text-sm font-medium text-gray-700 leading-tight">{text}</div>
    </div>
  );
};

interface SidebarProps {
  position: 'left' | 'right';
}

const Sidebar: React.FC<SidebarProps> = ({ position }) => {
  const { nodes } = useNodes();
  const { arrows } = useArrows();
  const { 
    selectedPersonId, 
    selectedNodeId, 
    selectedArrowId,
    setSelectedPersonId 
  } = useSelectedElement();
  const { persons, addPerson } = usePersons();
  const { handleImportYAML } = useFileImport();
  const { onSaveYAMLToDirectory, onSaveLLMYAMLToDirectory } = useExport();
  const [blocksExpanded, setBlocksExpanded] = useState(true);
  const [personsExpanded, setPersonsExpanded] = useState(true);
  const [fileOperationsExpanded, setFileOperationsExpanded] = useState(true);
  const [conversationExpanded, setConversationExpanded] = useState(true);
  const [memoryExpanded, setMemoryExpanded] = useState(true);
  
  const handlePersonClick = (personId: string) => {
    setSelectedPersonId(personId);
  };

  if (position === 'right') {
    return (
      <aside className="h-full border-l bg-gray-50 overflow-y-auto">
        <Suspense fallback={<div className="p-4 text-gray-500">Loading properties...</div>}>
          <PropertiesPanel />
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
              <DraggableBlock type="start" label={`${NODE_CONFIGS.start?.icon || '🚀'} ${NODE_CONFIGS.start?.label || 'Start'} Block`} />
              <DraggableBlock type="person_job" label={`${NODE_CONFIGS.person_job?.icon || '🤖'} ${NODE_CONFIGS.person_job?.label || 'Person Job'} Block`} />
              <DraggableBlock type="person_batch_job" label={`${NODE_CONFIGS.person_batch_job?.icon || '🤖📦'} ${NODE_CONFIGS.person_batch_job?.label || 'Person Batch Job'} Block`} />
              <DraggableBlock type="condition" label={`${NODE_CONFIGS.condition?.icon || '🔀'} ${NODE_CONFIGS.condition?.label || 'Condition'} Block`} />
              <DraggableBlock type="job" label={`${NODE_CONFIGS.job?.icon || '⚙️'} ${NODE_CONFIGS.job?.label || 'Job'} Block`} />
              <DraggableBlock type="user_response" label={`${NODE_CONFIGS.user_response?.icon || '💬'} ${NODE_CONFIGS.user_response?.label || 'User Response'} Block`} />
              <DraggableBlock type="endpoint" label={`${NODE_CONFIGS.endpoint?.icon || '🎯'} ${NODE_CONFIGS.endpoint?.label || 'Endpoint'} Block`} />
            </div>
            <h4 className="font-semibold mb-2 mt-4 text-sm text-gray-600 px-2">Data Blocks</h4>
            <div className="grid grid-cols-2 gap-2 px-2">
              <DraggableBlock type="db" label={`${NODE_CONFIGS.db?.icon || '📊'} ${NODE_CONFIGS.db?.label || 'DB Source'} Block`} />
            </div>
          </div>
        )}
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
              {persons.map(person => (
                <div
                  key={person.id}
                  className={`p-2 rounded-lg cursor-pointer transition-all duration-200 text-sm ${
                    selectedPersonId === person.id
                      ? 'bg-blue-100 border border-blue-300 shadow-sm'
                      : 'bg-gray-100 border border-gray-200 hover:bg-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => handlePersonClick(person.id)}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-base">{person.emoji || '🤖'}</span>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-xs truncate">{person.name}</p>
                      <p className="text-xs text-gray-500 truncate">{person.service || 'No service'}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <Button
              variant="outline"
              className="w-full mt-2 text-sm py-2 hover:bg-blue-50 hover:border-blue-300 transition-colors duration-200"
              size="sm"
              onClick={() => addPerson({
                name: `Person ${persons.length + 1}`,
                emoji: '🤖',
                service: 'openai',
                modelName: 'gpt-4.1-nano',
                apiKeyId: '',
                systemPrompt: '',
                description: ''
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
            <span className="text-base font-medium">File Operations</span>
          </span>
          {fileOperationsExpanded ? <ChevronDown size={16} className="text-gray-500" /> : <ChevronRight size={16} className="text-gray-500" />}
        </h3>
        {fileOperationsExpanded && (
          <div className="mt-3 space-y-2 px-2">
            <FileUploadButton
              onFileUpload={handleImportYAML}
              className="w-full text-sm py-2 hover:bg-blue-50 hover:border-blue-300 transition-colors duration-200"
              variant="outline"
              size="sm"
              title="Import diagram from YAML file"
            >
              <span className="mr-1">📥</span> Import YAML
            </FileUploadButton>
            <Button
              variant="outline"
              className="w-full text-sm py-2 hover:bg-green-50 hover:border-green-300 transition-colors duration-200"
              size="sm"
              onClick={() => onSaveYAMLToDirectory()}
              title="Export to YAML format (saves to /files/yaml_diagrams/)"
            >
              <span className="mr-1">📤</span> Export YAML
            </Button>
            <Button
              variant="outline"
              className="w-full text-sm py-2 hover:bg-yellow-50 hover:border-yellow-300 transition-colors duration-200"
              size="sm"
              onClick={() => onSaveLLMYAMLToDirectory()}
              title="Export to LLM-friendly YAML format (saves to /files/llm-yaml_diagrams/)"
            >
              <span className="mr-1">🤖</span> Export LLM YAML
            </Button>
          </div>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;