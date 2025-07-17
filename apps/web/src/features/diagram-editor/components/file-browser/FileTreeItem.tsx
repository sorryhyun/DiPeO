import React from 'react';
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
  const isSelected = selectedPath === node.path;

  const handleClick = () => {
    onFileClick(node);
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
        style={{ paddingLeft: `${level * 16 + 8}px` }}
        onClick={handleClick}
      >
        <span className="w-4" />
        
        <span className="flex-shrink-0 text-base">{getFormatEmoji()}</span>
        
        <span className="flex-1 text-sm truncate">
          {node.name}
        </span>
        
        {node.type === 'file' && node.size && (
          <span className="text-xs text-black/60 ml-2">
            {formatFileSize(node.size)}
          </span>
        )}
      </div>
    </div>
  );
};