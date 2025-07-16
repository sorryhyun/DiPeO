import { useMemo } from 'react';
import { useListDiagramsQuery } from '@/__generated__/graphql';

export interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileNode[];
  format?: 'native' | 'light' | 'readable';
  size?: number;
  modifiedAt?: string;
}

export function useDiagramFiles() {
  const { data, loading, error, refetch } = useListDiagramsQuery({
    variables: {
      limit: 1000, // Get all files
      offset: 0
    },
    pollInterval: 30000, // Refresh every 30 seconds
  });

  const fileTree = useMemo(() => {
    if (!data?.diagrams) return [];

    // Build tree structure from flat file list
    const root: FileNode = {
      name: 'diagrams',
      path: '/files/diagrams',
      type: 'directory',
      children: []
    };

    const formatDirs = new Map<string, FileNode>();

    data.diagrams.forEach(diagram => {
      if (!diagram.metadata?.id) return;

      const fullPath = diagram.metadata.id;
      const parts = fullPath.split('/');
      
      // Extract format from path (e.g., "native/example" -> "native")
      let format: 'native' | 'light' | 'readable' = 'native';
      let fileName = fullPath;
      
      if (parts.length > 1 && ['native', 'light', 'readable'].includes(parts[0] || '')) {
        format = parts[0] as 'native' | 'light' | 'readable';
        fileName = parts.slice(1).join('/');
      }

      // Get or create format directory
      if (!formatDirs.has(format)) {
        const formatDir: FileNode = {
          name: format,
          path: `${format}`,
          type: 'directory',
          children: []
        };
        formatDirs.set(format, formatDir);
        root.children!.push(formatDir);
      }

      const formatDir = formatDirs.get(format)!;

      // Parse size from description if available
      let size: number | undefined;
      if (diagram.metadata?.description) {
        const sizeMatch = diagram.metadata.description.match(/Size: (\d+) bytes/);
        if (sizeMatch && sizeMatch[1]) {
          size = parseInt(sizeMatch[1], 10);
        }
      }

      // Add file to appropriate format directory
      const fileNode: FileNode = {
        name: fileName,
        path: fullPath,
        type: 'file',
        format,
        size,
        modifiedAt: diagram.metadata?.modified
      };

      formatDir.children!.push(fileNode);
    });

    // Sort directories and files
    root.children!.forEach(dir => {
      if (dir.children) {
        dir.children.sort((a, b) => a.name.localeCompare(b.name));
      }
    });

    // Sort format directories
    root.children!.sort((a, b) => {
      const order = { native: 0, light: 1, readable: 2 };
      return (order[a.name as keyof typeof order] || 3) - (order[b.name as keyof typeof order] || 3);
    });

    return root.children || [];
  }, [data]);

  return {
    fileTree,
    loading,
    error,
    refetch
  };
}