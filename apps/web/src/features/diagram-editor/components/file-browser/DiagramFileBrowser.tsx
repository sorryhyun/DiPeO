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
      // Update URL without page refresh
      const newUrl = `/?diagram=${file.path}`;
      window.history.pushState({}, '', newUrl);
      
      // Trigger popstate event to load diagram
      window.dispatchEvent(new PopStateEvent('popstate'));
      
      // Update selected path
      setSelectedPath(file.path);
    }
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refetch();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  // Filter files based on search query
  const filterNodes = (nodes: FileNode[], query: string): FileNode[] => {
    if (!query) return nodes;
    
    const lowerQuery = query.toLowerCase();
    
    return nodes.reduce<FileNode[]>((acc, node) => {
      if (node.type === 'directory') {
        const filteredChildren = filterNodes(node.children || [], query);
        if (filteredChildren.length > 0) {
          acc.push({
            ...node,
            children: filteredChildren
          });
        }
      } else if (node.name.toLowerCase().includes(lowerQuery)) {
        acc.push(node);
      }
      return acc;
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
      <div className="p-3 border-b border-gray-700 space-y-2">
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search files..."
            className="w-full pl-9 pr-3 py-1.5 text-sm bg-gray-800 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-200 placeholder-gray-500"
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
      <div className="flex-1 overflow-y-auto p-2">
        {loading && !fileTree.length ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="animate-spin text-gray-400" size={24} />
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
      <div className="px-3 py-2 border-t border-gray-700 text-xs text-gray-500">
        {loading ? (
          <span>Loading...</span>
        ) : (
          <span>{fileTree.reduce((count, dir) => count + (dir.children?.length || 0), 0)} files</span>
        )}
      </div>
    </div>
  );
};