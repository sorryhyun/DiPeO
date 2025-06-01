import React, { useState, useEffect } from 'react';
import { Layers } from 'lucide-react';
import { Button } from '@/shared/components';
import { useConsolidatedDiagramStore } from '@/shared/stores';
import { useUIState } from '@/shared/hooks/useStoreSelectors';
import { useDiagramActions } from '@/features/diagram/hooks/useDiagramActions';
import { useDiagramRunner } from '@/features/diagram/hooks/useDiagramRunner';
import { useKeyboardShortcuts } from '@/features/diagram/wrappers';
import { LazyApiKeysModal } from '@/features/layout';
import { FileUploadButton } from '@/shared/components/common/FileUploadButton';
import { API_ENDPOINTS, getApiUrl } from '@/shared/utils/apiConfig';
import { toast } from 'sonner';
import { createErrorHandlerFactory } from '@/shared/types';
import { isApiKey, parseApiArrayResponse } from '@/shared/utils/typeGuards';


const TopBar = () => {
  const [isApiModalOpen, setIsApiModalOpen] = useState(false);
  const [hasCheckedBackend, setHasCheckedBackend] = useState(false);
  const [isMonitorMode, setIsMonitorMode] = useState(false);
  const apiKeys = useConsolidatedDiagramStore(state => state.apiKeys);
  const addApiKey = useConsolidatedDiagramStore(state => state.addApiKey);
  const loadApiKeys = useConsolidatedDiagramStore(state => state.loadApiKeys);
  const { onSaveToDirectory, onExportYAML, onExportLLMYAML, onImportYAML } = useDiagramActions();
  const { runStatus, onRunDiagram, stopExecution } = useDiagramRunner();
  const { isMemoryLayerTilted, toggleMemoryLayer } = useUIState();
  
  const createErrorHandler = createErrorHandlerFactory(toast);
  
  // Load API keys on mount
  useEffect(() => {
    loadApiKeys().catch(error => {
      console.error('Failed to load API keys on mount:', error);
    });
  }, [loadApiKeys]);
  
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setIsMonitorMode(params.get('monitor') === 'true');
    const checkBackendApiKeys = async () => {
      try {
        const res = await fetch(getApiUrl(API_ENDPOINTS.API_KEYS));
        if (res.ok) {
          const data = await res.json();
          const backendKeys = parseApiArrayResponse(data.apiKeys || data, isApiKey);
          
          if (backendKeys.length > 0 && apiKeys.length === 0) {
            backendKeys.forEach((key) => {
              addApiKey({
                name: key.name,
                service: key.service,
                keyReference: key.keyReference
              });
            });
          }
          
          if (backendKeys.length === 0 && apiKeys.length === 0) {
            setIsApiModalOpen(true);
          }
        }
      } catch (error) {
        const errorHandler = createErrorHandler('Check Backend API Keys');
        errorHandler(error instanceof Error ? error : new Error('Failed to check backend API keys'));
        if (apiKeys.length === 0) {
          setIsApiModalOpen(true);
        }
      } finally {
        setHasCheckedBackend(true);
      }
    };

    if (!hasCheckedBackend) {
      checkBackendApiKeys();
    }
  }, [hasCheckedBackend, apiKeys.length, addApiKey, createErrorHandler]);

  useKeyboardShortcuts({
    onSave: () => onSaveToDirectory(),
  });

  return (
    <header className="p-3 border-b bg-gradient-to-r from-gray-50 to-gray-100 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Button 
            variant="outline" 
            className="bg-white hover:bg-blue-50 hover:border-blue-300 transition-colors"
          >
            📄 New
          </Button>
          <Button 
            variant="outline" 
            className="bg-white hover:bg-blue-50 hover:border-blue-300 transition-colors"
            onClick={() => onSaveToDirectory()}
            title="Save diagram to server (diagrams folder)"
          >
            💾 Save
          </Button>
          
          <div className="border-l border-gray-300 h-6 mx-2" />
          
          <Button
            variant="outline"
            className="bg-white hover:bg-green-50 hover:border-green-300 transition-colors"
            onClick={onExportYAML}
            title="Export to YAML format (download)"
          >
            📤 Export YAML
          </Button>
          <Button
            variant="outline"
            className="bg-white hover:bg-yellow-50 hover:border-yellow-300 transition-colors"
            onClick={onExportLLMYAML}
            title="Export to LLM-friendly YAML format (download)"
          >
            🤖 Export LLM YAML
          </Button>
          <FileUploadButton
            accept=".yaml,.yml"
            onChange={onImportYAML}
            variant="outline"
            className="bg-white hover:bg-green-50 hover:border-green-300 transition-colors"
            title="Import from YAML format (supports both standard and LLM-friendly formats)"
          >
            📥 Import YAML
          </FileUploadButton>

          <div className="border-l border-gray-300 h-6 mx-2" />
          
          <Button 
            variant="outline" 
            className="bg-white hover:bg-purple-50 hover:border-purple-300 transition-colors"
            onClick={() => setIsApiModalOpen(true)}
          >
            🔑 API Keys
          </Button>
        </div>

        <div className="flex items-center space-x-4">
          {runStatus === 'running' ? (
            <Button 
              variant="outline" 
              className="bg-gradient-to-r from-red-500 to-red-600 text-white border-none hover:from-red-600 hover:to-red-700 shadow-md hover:shadow-lg transition-all"
              onClick={stopExecution}
            >
              ⏹️ Stop
            </Button>
          ) : (
            <Button 
              variant="outline" 
              className="bg-gradient-to-r from-green-500 to-emerald-500 text-white border-none hover:from-green-600 hover:to-emerald-600 shadow-md hover:shadow-lg transition-all"
              onClick={onRunDiagram}
            >
              ▶️ Run Diagram
            </Button>
          )}
          <div className="whitespace-nowrap text-base font-medium">
            {runStatus === 'running' && <span className="text-blue-600 animate-pulse">⚡ Running...</span>}
            {runStatus === 'success' && <span className="text-green-600">✅ Success</span>}
            {runStatus === 'fail' && <span className="text-red-600">❌ Fail</span>}
          </div>
        </div>
        {isMonitorMode && (
          <div className="flex items-center space-x-2 px-3 py-1 bg-blue-100 text-blue-700 rounded-md animate-pulse">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
            </span>
            <span className="text-sm font-medium">Monitor Mode Active</span>
          </div>
        )}
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            className={`bg-white transition-all duration-300 ${
              isMemoryLayerTilted 
                ? 'bg-purple-100 border-purple-400 hover:bg-purple-200' 
                : 'hover:bg-gray-50 hover:border-gray-300'
            }`}
            onClick={toggleMemoryLayer}
            title={isMemoryLayerTilted ? 'Hide Memory Layer' : 'Show Memory Layer'}
          >
            <Layers className={`h-4 w-4 mr-1 transition-transform duration-300 ${
              isMemoryLayerTilted ? 'rotate-12' : ''
            }`} />
            Memory
          </Button>
        </div>

        <div className="w-32" />
      </div>

      <LazyApiKeysModal isOpen={isApiModalOpen} onClose={() => setIsApiModalOpen(false)} />
    </header>
  );
};

export default TopBar;