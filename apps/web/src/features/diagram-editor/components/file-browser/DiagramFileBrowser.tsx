import React, { useState, useEffect, useCallback } from 'react';
import { Search, RefreshCw, Loader2 } from 'lucide-react';
import { FileTree } from './FileTree';
import { FileNode, useDiagramFiles } from './useDiagramFiles';
import { Button } from '@/shared/components/forms/buttons';

export const DiagramFileBrowser: React.FC = () => {
  const { fileTree, loading, error, refetch } = useDiagramFiles();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPath, setSelectedPath] = useState<string>();
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Get current diagram from URL
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const diagramId = urlParams.get('diagram');
    if (diagramId) {
      setSelectedPath(diagramId);
    }
  }, []);

  const handleFileClick = useCallback((file: FileNode) => {
    if (file.type === 'file') {
      // Update selected path immediately for UI feedback
      setSelectedPath(file.path);
      
      // Add a small delay to ensure React Flow has time to clean up
      setTimeout(() => {
        // Update URL without page refresh
        const newUrl = `/?diagram=${file.path}`;
        window.history.pushState({}, '', newUrl);
        
        // Trigger popstate event to load diagram
        window.dispatchEvent(new PopStateEvent('popstate'));
      }, 100); // Small delay for cleanup
    }
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refetch();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  // Filter files based on search query
  // Count files recursively
  const countFiles = (nodes: FileNode[]): number => {
    return nodes.reduce((count, node) => {
      if (node.type === 'file') {
        return count + 1;
      } else if (node.type === 'folder' && node.children) {
        return count + countFiles(node.children);
      }
      return count;
    }, 0);
  };

  const filterNodes = (nodes: FileNode[], query: string): FileNode[] => {
    if (!query) return nodes;
    
    const lowerQuery = query.toLowerCase();
    
    return nodes.reduce<FileNode[]>((filtered, node) => {
      // Check if current node matches
      const matches = node.name.toLowerCase().includes(lowerQuery);
      
      if (node.type === 'folder' && node.children) {
        // For folders, check children recursively
        const filteredChildren = filterNodes(node.children, query);
        if (filteredChildren.length > 0) {
          // Include folder if it has matching children
          filtered.push({
            ...node,
            children: filteredChildren
          });
        } else if (matches) {
          // Include folder if its name matches (even without matching children)
          filtered.push(node);
        }
      } else if (matches) {
        // Include file if it matches
        filtered.push(node);
      }
      
      return filtered;
    }, []);
  };

  const filteredTree = filterNodes(fileTree, searchQuery);

  if (error) {
    return (
      <div className="p-4 text-center">
        <p className="text-red-400 text-sm mb-2">Failed to load diagram files</p>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          className="text-xs"
        >
          <RefreshCw size={12} className="mr-1" />
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Search and refresh controls */}
      <div className="p-3 border-b border-gray-200 space-y-2">
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-600" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search files..."
            className="w-full pl-9 pr-3 py-1.5 text-sm bg-white border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black placeholder-gray-400"
          />
        </div>
        
        <Button
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          disabled={isRefreshing || loading}
          className="w-full text-xs"
        >
          {isRefreshing || loading ? (
            <Loader2 size={12} className="mr-1 animate-spin" />
          ) : (
            <RefreshCw size={12} className="mr-1" />
          )}
          Refresh Files
        </Button>
      </div>

      {/* File tree */}
      <div className="flex-1 overflow-y-auto px-1 py-2">
        {loading && !fileTree.length ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="animate-spin text-gray-600" size={24} />
          </div>
        ) : (
          <FileTree 
            nodes={filteredTree} 
            onFileClick={handleFileClick}
            selectedPath={selectedPath}
          />
        )}
      </div>

      {/* Status bar */}
      <div className="px-3 py-2 border-t border-gray-200 text-xs text-black/60">
        {loading ? (
          <span>Loading...</span>
        ) : (
          <span>{countFiles(fileTree)} files</span>
        )}
      </div>
    </div>
  );
};