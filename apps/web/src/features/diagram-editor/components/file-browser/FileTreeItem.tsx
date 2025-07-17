import React, { useState } from 'react';
import { ChevronRight, ChevronDown, Folder, FolderOpen } from 'lucide-react';
import { FileNode } from './useDiagramFiles';

interface FileTreeItemProps {
  node: FileNode;
  level: number;
  onFileClick: (file: FileNode) => void;
  selectedPath?: string;
}

export const FileTreeItem: React.FC<FileTreeItemProps> = ({
  node,
  level,
  onFileClick,
  selectedPath
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const isSelected = selectedPath === node.path;

  const handleClick = () => {
    if (node.type === 'folder') {
      setIsExpanded(!isExpanded);
    } else {
      onFileClick(node);
    }
  };

  const getFormatEmoji = () => {
    switch (node.format) {
      case 'native':
        return '🔧'; // Wrench for native (JSON)
      case 'light':
        return '⚡'; // Lightning for light (YAML)
      case 'readable':
        return '📖'; // Book for readable (text-like)
      default:
        return '📄'; // Default file icon
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '';
    const kb = bytes / 1024;
    return kb < 1 ? `${bytes} B` : `${kb.toFixed(1)} KB`;
  };

  return (
    <div>
      <div
        className={`
          flex items-center gap-1 px-2 py-1 cursor-pointer hover:bg-gray-200 rounded transition-colors
          ${isSelected ? 'bg-blue-600/20 text-blue-400' : 'text-black'}
        `}
        style={{ paddingLeft: `${level * 16 + 4}px` }}
        onClick={handleClick}
      >
        {/* Chevron for folders */}
        {node.type === 'folder' ? (
          <span className="w-4 flex-shrink-0">
            {isExpanded ? (
              <ChevronDown size={16} className="text-gray-500" />
            ) : (
              <ChevronRight size={16} className="text-gray-500" />
            )}
          </span>
        ) : (
          <span className="w-4" />
        )}
        
        {/* Icon */}
        <span className="flex-shrink-0 text-base">
          {node.type === 'folder' ? (
            isExpanded ? <FolderOpen size={16} className="text-blue-500" /> : <Folder size={16} className="text-blue-500" />
          ) : (
            getFormatEmoji()
          )}
        </span>
        
        <span className="flex-1 text-sm truncate">
          {node.name}
        </span>
        
        {node.type === 'file' && node.size && (
          <span className="text-xs text-black/60 ml-2">
            {formatFileSize(node.size)}
          </span>
        )}
      </div>
      
      {/* Render children if folder is expanded */}
      {node.type === 'folder' && isExpanded && node.children && (
        <div>
          {node.children.map((child) => (
            <FileTreeItem
              key={child.path}
              node={child}
              level={level + 1}
              onFileClick={onFileClick}
              selectedPath={selectedPath}
            />
          ))}
        </div>
      )}
    </div>
  );
};