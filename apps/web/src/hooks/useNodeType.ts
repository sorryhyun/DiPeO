import { useCallback, useMemo } from 'react';
import { NODE_CONFIGS } from '@/types';

export const useNodeType = (nodeType: string) => {
  const config = useMemo(() => NODE_CONFIGS[nodeType as keyof typeof NODE_CONFIGS], [nodeType]);

  // Get handle configurations based on flip state
  const getHandles = useCallback((isFlipped: boolean = false) => {
    if (!config) return [];
    
    // Handle configuration logic would go here
    // This is a simplified version - you may need to expand based on actual handle logic
    const inputHandles = (config.handles.input || []).map((handle: any) => ({ ...handle, type: 'input' }));
    const outputHandles = (config.handles.output || []).map((handle: any) => ({ ...handle, type: 'output' }));
    const allHandles = [...inputHandles, ...outputHandles];
    
    if (isFlipped) {
      // Flip handle positions if needed
      return allHandles.map((handle: any) => ({
        ...handle,
        position: handle.position === 'left' ? 'right' : 
                 handle.position === 'right' ? 'left' : handle.position
      }));
    }
    
    return allHandles;
  }, [config]);

  // Get default node data
  const getDefaultData = useCallback(() => {
    if (!config) return {};
    
    return {
      type: nodeType,
      label: config.label
    };
  }, [nodeType, config]);

  // Get node styling information
  const getNodeStyles = useCallback(() => {
    if (!config) return {};
    
    return {
      borderColor: config.color || '#ccc' // Use color property as border color
    };
  }, [config]);

  // Check if node has specific capabilities
  const hasCapability = useCallback((_capability: string) => {
    return false;
  }, []);

  return {
    config,
    emoji: config?.icon, // Map icon to emoji for backward compatibility
    icon: config?.icon,
    label: config?.label,
    reactFlowType: nodeType, // Use nodeType as reactFlowType
    borderColor: config?.color || '#ccc', // Use color property as border color
    getHandles,
    getDefaultData,
    getNodeStyles,
    hasCapability,
    isValid: !!config
  };
};