import React, { useState } from 'react';
import { ChevronRight, ChevronDown, File, Folder, FolderOpen } from 'lucide-react';
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
    if (node.type === 'directory') {
      setIsExpanded(!isExpanded);
    } else {
      onFileClick(node);
    }
  };

  const getFileIcon = () => {
    if (node.type === 'directory') {
      return isExpanded ? <FolderOpen size={16} /> : <Folder size={16} />;
    }
    return <File size={16} />;
  };

  const getFileExtension = () => {
    if (node.type === 'file' && node.format) {
      return node.format === 'native' ? '.json' : '.yaml';
    }
    return '';
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
          flex items-center gap-1 px-2 py-1 cursor-pointer hover:bg-gray-700/50 rounded transition-colors
          ${isSelected ? 'bg-blue-600/20 text-blue-400' : 'text-gray-300'}
        `}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
        onClick={handleClick}
      >
        {node.type === 'directory' && (
          <span className="w-4 h-4 flex items-center justify-center">
            {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </span>
        )}
        {node.type === 'file' && <span className="w-4" />}
        
        <span className="flex-shrink-0">{getFileIcon()}</span>
        
        <span className="flex-1 text-sm truncate">
          {node.name}
          <span className="text-gray-500">{getFileExtension()}</span>
        </span>
        
        {node.type === 'file' && node.size && (
          <span className="text-xs text-gray-500 ml-2">
            {formatFileSize(node.size)}
          </span>
        )}
      </div>
      
      {node.type === 'directory' && isExpanded && node.children && (
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