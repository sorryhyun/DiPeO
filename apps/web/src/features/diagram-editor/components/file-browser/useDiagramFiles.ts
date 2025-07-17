import { useMemo } from 'react';
import { useListDiagramsQuery } from '@/__generated__/graphql';

export interface FileNode {
  name: string;
  path: string;
  type: 'file';
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

    const files: FileNode[] = [];

    data.diagrams.forEach(diagram => {
      if (!diagram.metadata?.id) return;

      const fullPath = diagram.metadata.id;
      
      // Extract format from file extension
      let format: 'native' | 'light' | 'readable' = 'native';
      const fileName = fullPath;
      
      if (fullPath.endsWith('.native.json')) {
        format = 'native';
      } else if (fullPath.endsWith('.light.yaml') || fullPath.endsWith('.light.yml')) {
        format = 'light';
      } else if (fullPath.endsWith('.readable.yaml') || fullPath.endsWith('.readable.yml')) {
        format = 'readable';
      } else if (fullPath.endsWith('.json')) {
        format = 'native';
      } else if (fullPath.endsWith('.yaml') || fullPath.endsWith('.yml')) {
        // Check if in format-specific folder for backward compatibility
        const parts = fullPath.split('/');
        if (parts.length > 1 && ['native', 'light', 'readable'].includes(parts[0] || '')) {
          format = parts[0] as 'native' | 'light' | 'readable';
        }
      }

      // Parse size from description if available
      let size: number | undefined;
      if (diagram.metadata?.description) {
        const sizeMatch = diagram.metadata.description.match(/Size: (\d+) bytes/);
        if (sizeMatch && sizeMatch[1]) {
          size = parseInt(sizeMatch[1], 10);
        }
      }

      // Add file to list
      const fileNode: FileNode = {
        name: fileName,
        path: fullPath,
        type: 'file',
        format,
        size,
        modifiedAt: diagram.metadata?.modified
      };

      files.push(fileNode);
    });

    // Sort files alphabetically
    files.sort((a, b) => a.name.localeCompare(b.name));

    return files;
  }, [data]);

  return {
    fileTree,
    loading,
    error,
    refetch
  };
}