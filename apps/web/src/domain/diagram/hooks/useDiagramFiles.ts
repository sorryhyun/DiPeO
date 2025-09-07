import { useMemo } from 'react';
import * as React from 'react';
import { useListDiagramsQuery } from '@/__generated__/graphql';

export interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'folder';
  format?: 'native' | 'light' | 'readable';
  size?: number;
  modifiedAt?: string;
  children?: FileNode[];
}

export function useDiagramFiles() {
  const { data, loading, error, refetch, stopPolling } = useListDiagramsQuery({
    variables: {
      limit: 1000, // Get all files
      offset: 0
    },
    pollInterval: 30000, // Refresh every 30 seconds
  });

  // Stop polling if we're in CLI monitor mode and detect server shutdown
  React.useEffect(() => {
    if (error?.networkError) {
      const params = new URLSearchParams(window.location.search);
      const isCliMonitorMode = params.get('monitor') === 'true' && params.get('no-auto-exit') === 'true';
      if (isCliMonitorMode) {
        console.log('[DiagramFiles] Stopping polling due to network error');
        stopPolling();
      }
    }
  }, [error, stopPolling]);

  const fileTree = useMemo(() => {
    if (!data?.diagrams) return [];

    // Type for intermediate tree structure
    interface TreeNode extends Omit<FileNode, 'children'> {
      children?: Record<string, TreeNode>;
    }

    // Helper function to build tree structure
    const buildTree = (files: Array<{ path: string; node: FileNode }>): FileNode[] => {
      const root: Record<string, TreeNode> = {};

      // Sort files by path to ensure folders are created before their files
      files.sort((a, b) => a.path.localeCompare(b.path));

      files.forEach(({ path, node }) => {
        const parts = path.split('/');
        let current = root;

        // Build folder structure
        for (let i = 0; i < parts.length - 1; i++) {
          const folderName = parts[i];
          if (!folderName) continue; // Skip empty parts

          if (!current[folderName]) {
            current[folderName] = {
              name: folderName,
              path: parts.slice(0, i + 1).join('/'),
              type: 'folder',
              children: {}
            };
          }
          const folderNode = current[folderName];
          if (folderNode && folderNode.type === 'folder' && folderNode.children) {
            current = folderNode.children;
          }
        }

        // Add file
        const fileName = parts[parts.length - 1];
        if (fileName) {
          // Convert FileNode to TreeNode (files don't have children object)
          current[fileName] = {
            ...node,
            children: undefined
          } as TreeNode;
        }
      });

      // Convert object to array and sort
      const convertToArray = (obj: Record<string, TreeNode>): FileNode[] => {
        return Object.values(obj).map(item => {
          if (item.type === 'folder' && item.children && typeof item.children === 'object' && !Array.isArray(item.children)) {
            const result: FileNode = {
              ...item,
              children: convertToArray(item.children)
            };
            return result;
          }
          return item as FileNode;
        }).sort((a, b) => {
          // Folders first, then files
          if (a.type !== b.type) {
            return a.type === 'folder' ? -1 : 1;
          }
          return a.name.localeCompare(b.name);
        });
      };

      return convertToArray(root);
    };

    const fileList: Array<{ path: string; node: FileNode }> = [];

    data.diagrams.forEach(diagram => {
      if (!diagram.metadata?.id) return;

      const fullPath = diagram.metadata.id;

      // Extract format from file extension
      let format: 'native' | 'light' | 'readable' = 'native';
      const pathParts = fullPath.split('/');
      const fileName = pathParts[pathParts.length - 1] || fullPath;

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
        if (pathParts.length > 1 && ['native', 'light', 'readable'].includes(pathParts[0] || '')) {
          format = pathParts[0] as 'native' | 'light' | 'readable';
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
        ...(diagram.metadata?.modified && { modifiedAt: diagram.metadata.modified })
      };

      fileList.push({ path: fullPath, node: fileNode });
    });

    return buildTree(fileList);
  }, [data]);

  return {
    fileTree,
    loading,
    error,
    refetch
  };
}
