import React, { useState, useEffect } from 'react';
import { Layers } from 'lucide-react';
import { Button } from '@/common/components';
import { useApiKeyStore, useDiagramStore } from '@/state/stores';
import { useUIState } from '@/state/hooks/useStoreSelectors';
import { useFileImport } from '@/features/serialization/hooks/useFileImport';
import { useExport } from '@/features/serialization/hooks/useExport';
import { useDiagramRunner } from '@/features/runtime/hooks/useDiagramRunner';
import { useKeyboardShortcuts } from '@/features/canvas/hooks/useKeyboardShortcuts';
import { LazyApiKeysModal } from '@/features/layout';
import { FileUploadButton } from '@/common/components/common/FileUploadButton';
import { API_ENDPOINTS, getApiUrl } from '@/common/utils/apiConfig';
import { toast } from 'sonner';
import { createErrorHandlerFactory } from '@/common/types';
import { isApiKey, parseApiArrayResponse } from '@/common/utils/typeGuards';


const TopBar = () => {
  const [isApiModalOpen, setIsApiModalOpen] = useState(false);
  const [hasCheckedBackend, setHasCheckedBackend] = useState(false);
  const [isMonitorMode, setIsMonitorMode] = useState(false);
  const [isExitingMonitor, setIsExitingMonitor] = useState(false);
  const apiKeys = useApiKeyStore(state => state.apiKeys);
  const addApiKey = useApiKeyStore(state => state.addApiKey);
  const loadApiKeys = useApiKeyStore(state => state.loadApiKeys);
  const clearDiagramAction = useDiagramStore(state => state.clearDiagram);
  const isReadOnly = useDiagramStore(state => state.isReadOnly);
  const setReadOnly = useDiagramStore(state => state.setReadOnly);
  const { onImportJSON } = useFileImport();
  const { onSaveToDirectory } = useExport();
  const { runStatus, onRunDiagram, stopExecution } = useDiagramRunner();
  const { activeCanvas, toggleCanvas } = useUIState();
  
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
            onClick={() => {
              if (window.confirm('Create a new diagram? This will clear the current diagram.')) {
                clearDiagramAction();
                toast.success('Created new diagram');
              }
            }}
            title="Create a new diagram"
          >
            📄 New
          </Button>
          <FileUploadButton
            accept=".json"
            onChange={onImportJSON}
            variant="outline"
            className="bg-white hover:bg-blue-50 hover:border-blue-300 transition-colors"
            title="Open diagram from JSON file"
          >
            📂 Open
          </FileUploadButton>
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
        {(isMonitorMode || isReadOnly) && (
          <div className="flex items-center space-x-2 px-3 py-1 bg-blue-100 text-blue-700 rounded-md">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
            </span>
            <span className="text-sm font-medium">Monitor Mode Active</span>
            <button
              onClick={() => {
                setIsExitingMonitor(true);
                clearDiagramAction();
                setReadOnly(false);
                // Remove monitor param from URL
                const url = new URL(window.location.href);
                url.searchParams.delete('monitor');
                window.history.replaceState({}, '', url.toString());
                toast.success('Exited monitor mode');
                setTimeout(() => setIsExitingMonitor(false), 300);
              }}
              disabled={isExitingMonitor}
              className={`ml-2 text-xs px-2 py-1 rounded transition-all ${
                isExitingMonitor 
                  ? 'bg-red-600 text-white cursor-not-allowed opacity-75' 
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              {isExitingMonitor ? 'Exiting...' : 'Exit'}
            </button>
          </div>
        )}
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            className={`bg-white transition-all duration-300 ${
              activeCanvas === 'memory'
                ? 'bg-purple-100 border-purple-400 hover:bg-purple-200' 
                : 'hover:bg-gray-50 hover:border-gray-300'
            }`}
            onClick={toggleCanvas}
            title={activeCanvas === 'memory' ? 'Show Diagram Canvas' : 'Show Memory Canvas'}
          >
            <Layers className={`h-4 w-4 mr-1 transition-transform duration-300 ${
              activeCanvas === 'memory' ? 'rotate-12' : ''
            }`} />
            {activeCanvas === 'memory' ? 'Diagram' : 'Memory'}
          </Button>
        </div>

        <div className="w-32" />
      </div>

      <LazyApiKeysModal isOpen={isApiModalOpen} onClose={() => setIsApiModalOpen(false)} />
    </header>
  );
};

export default TopBar;