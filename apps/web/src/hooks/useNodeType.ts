import { useMemo } from 'react';
import { NODE_CONFIGS } from '@/types';

export const useNodeType = (nodeType: string) => {
  const config = useMemo(() => NODE_CONFIGS[nodeType as keyof typeof NODE_CONFIGS], [nodeType]);

  // Memoize handles once, avoiding multiple map passes per render
  const handles = useMemo(() => {
    if (!config) return [];
    
    const toHandles = (handles: any[] | undefined, type: string) => 
      handles?.map(h => ({ ...h, type })) ?? [];
    
    return [
      ...toHandles(config.handles.input, 'input'),
      ...toHandles(config.handles.output, 'output')
    ];
  }, [config]);

  // Get handle configurations based on flip state
  const getHandles = (isFlipped: boolean = false) => {
    if (isFlipped) {
      // Flip handle positions if needed
      return handles.map((handle: any) => ({
        ...handle,
        position: handle.position === 'left' ? 'right' : 
                 handle.position === 'right' ? 'left' : handle.position
      }));
    }
    
    return handles;
  };

  // Get default node data
  const getDefaultData = () => {
    if (!config) return {};
    
    return {
      type: nodeType,
      label: config.label
    };
  };

  // Get node styling information
  const getNodeStyles = () => {
    if (!config) return {};
    
    return {
      borderColor: config.color || '#ccc' // Use color property as border color
    };
  };

  // Check if node has specific capabilities
  const hasCapability = (_capability: string) => {
    return false;
  };

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