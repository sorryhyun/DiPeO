import React from 'react';
import { FileTreeItem } from './FileTreeItem';
import { FileNode } from './useDiagramFiles';

interface FileTreeProps {
  nodes: FileNode[];
  onFileClick: (file: FileNode) => void;
  selectedPath?: string;
}

export const FileTree: React.FC<FileTreeProps> = ({
  nodes,
  onFileClick,
  selectedPath
}) => {
  if (nodes.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8">
        <p className="text-sm">No diagram files found</p>
      </div>
    );
  }

  return (
    <div className="space-y-0.5">
      {nodes.map((node) => (
        <FileTreeItem
          key={node.path}
          node={node}
          level={0}
          onFileClick={onFileClick}
          selectedPath={selectedPath}
        />
      ))}
    </div>
  );
};