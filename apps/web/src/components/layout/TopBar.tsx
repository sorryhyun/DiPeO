import React, { useState, useEffect } from 'react';
import { Layers } from 'lucide-react';
import { Button } from '@/components/common';
import { useApiKeyStore } from '@/stores/apiKeyStore';
import { useConsolidatedUIStore } from '@/stores';
import { useDiagramStore } from '@/stores/diagramStore';
import { useExecutionStore } from '@/stores';
import { useFileImport } from '@/hooks/useFileImport';
import { useExport } from '@/hooks/useExport';
import { useDiagramRunner } from '@/hooks/useDiagramRunner';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import { LazyApiKeysModal } from '@/components/layout/modals/LazyModals';
import { FileUploadButton } from '@/components/common/common/FileUploadButton';
import { API_ENDPOINTS, getApiUrl } from '@/utils/apiConfig';
import { toast } from 'sonner';
import { isApiKey, parseApiArrayResponse } from '@/utils/typeGuards';


const TopBar = () => {
  const [isApiModalOpen, setIsApiModalOpen] = useState(false);
  const [hasCheckedBackend, setHasCheckedBackend] = useState(false);
  const [isMonitorMode, setIsMonitorMode] = useState(false);
  const [isExitingMonitor, setIsExitingMonitor] = useState(false);
  const { apiKeys, addApiKey, loadApiKeys } = useApiKeyStore();
  const { activeCanvas, toggleCanvas, setActiveCanvas } = useConsolidatedUIStore();
  const { clearDiagram, isReadOnly, setReadOnly } = useDiagramStore();
  const { currentRunningNode } = useExecutionStore();
  const { onImportJSON } = useFileImport();
  const { onSaveToDirectory } = useExport();
  const { 
    runStatus, 
    onRunDiagram, 
    stopExecution,
    pauseNode,
    resumeNode,
    skipNode
  } = useDiagramRunner();
  
  // Load API keys on mount
  useEffect(() => {
    loadApiKeys().catch(error => {
      console.error('Failed to load API keys on mount:', error);
    });
  }, [loadApiKeys]);
  
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const isMonitor = params.get('monitor') === 'true';
    setIsMonitorMode(isMonitor);
    
    // Auto-open execution mode when monitor mode is triggered
    if (isMonitor) {
      setActiveCanvas('execution');
      setReadOnly(true);
    }
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
        console.error('[Check Backend API Keys]', error);
        toast.error(`Check Backend API Keys: ${(error as Error).message}`);
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
  }, [hasCheckedBackend, apiKeys.length, addApiKey, setReadOnly]);

  useKeyboardShortcuts({
    onSave: () => onSaveToDirectory().catch(console.error),
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
                clearDiagram();
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
            onClick={() => onSaveToDirectory().catch(console.error)}
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
            <>
              <Button 
                variant="outline" 
                className="bg-gradient-to-r from-red-500 to-red-600 text-white border-none hover:from-red-600 hover:to-red-700 shadow-md hover:shadow-lg transition-all"
                onClick={stopExecution}
              >
                ⏹️ Stop
              </Button>
              {currentRunningNode && (
                <>
                  <Button
                    variant="outline"
                    className="bg-gradient-to-r from-yellow-500 to-amber-500 text-white border-none hover:from-yellow-600 hover:to-amber-600 shadow-md hover:shadow-lg transition-all"
                    onClick={() => pauseNode(currentRunningNode)}
                    title="Pause current node"
                  >
                    ⏸️ Pause
                  </Button>
                  <Button
                    variant="outline"
                    className="bg-gradient-to-r from-blue-500 to-cyan-500 text-white border-none hover:from-blue-600 hover:to-cyan-600 shadow-md hover:shadow-lg transition-all"
                    onClick={() => resumeNode(currentRunningNode)}
                    title="Resume current node"
                  >
                    ▶️ Resume
                  </Button>
                  <Button
                    variant="outline"
                    className="bg-gradient-to-r from-purple-500 to-pink-500 text-white border-none hover:from-purple-600 hover:to-pink-600 shadow-md hover:shadow-lg transition-all"
                    onClick={() => skipNode(currentRunningNode)}
                    title="Skip current node"
                  >
                    ⏭️ Skip
                  </Button>
                </>
              )}
            </>
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
        
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            className={`bg-white transition-all duration-300 ${
              activeCanvas === 'execution'
                ? 'bg-green-100 border-green-400 hover:bg-green-200' 
                : 'hover:bg-gray-50 hover:border-gray-300'
            }`}
            onClick={() => {
              if (activeCanvas === 'execution') {
                toggleCanvas();
                // Exit read-only mode when leaving execution mode
                setReadOnly(false);
              } else {
                setActiveCanvas('execution');
                // Set the diagram to read-only when entering execution mode
                setReadOnly(true);
              }
            }}
            title={activeCanvas === 'execution' ? 'Back to Diagram Canvas' : 'Enter Execution Mode'}
          >
            <Layers className={`h-4 w-4 mr-1 transition-transform duration-300 ${
              activeCanvas === 'execution' ? 'rotate-12' : ''
            }`} />
            {activeCanvas === 'execution' ? 'Exit Execution Mode' : 'Execution Mode'}
          </Button>
          
          {(isMonitorMode || isReadOnly) ? (
            <div className="flex items-center space-x-2 px-3 py-1 bg-blue-100 text-blue-700 rounded-md">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
              </span>
              <span className="text-sm font-medium">Monitor Mode Active</span>
              <button
                onClick={() => {
                  setIsExitingMonitor(true);
                  clearDiagram();
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
          ) : (
            <div className="flex items-center space-x-2 px-3 py-1 bg-gray-100 text-gray-600 rounded-md">
              <span className="relative flex h-3 w-3">
                <span className="relative inline-flex rounded-full h-3 w-3 bg-gray-400"></span>
              </span>
              <span className="text-sm font-medium">Monitor Mode Off</span>
            </div>
          )}
        </div>
      </div>

      <LazyApiKeysModal isOpen={isApiModalOpen} onClose={() => setIsApiModalOpen(false)} />
    </header>
  );
};

export default TopBar;