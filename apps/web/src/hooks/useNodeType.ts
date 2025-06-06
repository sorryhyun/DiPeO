import { useCallback, useMemo } from 'react';
import { UNIFIED_NODE_CONFIGS } from '../../../types';

export const useNodeType = (nodeType: string) => {
  const config = useMemo(() => UNIFIED_NODE_CONFIGS[nodeType as keyof typeof UNIFIED_NODE_CONFIGS], [nodeType]);

  // Get handle configurations based on flip state
  const getHandles = useCallback((isFlipped: boolean = false) => {
    if (!config) return [];
    
    // Handle configuration logic would go here
    // This is a simplified version - you may need to expand based on actual handle logic
    const allHandles = [
      ...config.handles.sources.map((handle: any) => ({ ...handle, type: 'output' })),
      ...config.handles.targets.map((handle: any) => ({ ...handle, type: 'input' }))
    ];
    
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
      borderColor: config.borderColor
    };
  }, [config]);

  // Check if node has specific capabilities
  const hasCapability = useCallback((_capability: string) => {
    return false;
  }, []);

  return {
    config,
    emoji: config?.emoji,
    label: config?.label,
    reactFlowType: config?.reactFlowType,
    borderColor: config?.borderColor,
    getHandles,
    getDefaultData,
    getNodeStyles,
    hasCapability,
    isValid: !!config
  };
};