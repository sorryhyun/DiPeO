import { DiagramNodeData } from '@/common/types';
import { getNodeConfig } from '@/common/types/nodeConfig';

// Factory function to create default node data based on node config
export function createDefaultNodeData(type: string, nodeId: string): DiagramNodeData {
  const config = getNodeConfig(type);
  
  if (!config) {
    // Fallback for unknown types
    return {
      id: nodeId,
      type: 'start' as const,
      label: 'Unknown'
    };
  }
  
  // Base properties common to all nodes
  const baseData: Record<string, unknown> = {
    id: nodeId,
    type,
    label: config.label
  };
  
  // Add type-specific properties based on config and defaults
  switch (type) {
    case 'start':
      baseData.description = '';
      break;
      
    case 'person_job':
      baseData.personId = undefined;
      baseData.llmApi = undefined;
      baseData.apiKeyId = undefined;
      baseData.modelName = undefined;
      baseData.defaultPrompt = '';
      baseData.firstOnlyPrompt = '';
      baseData.detectedVariables = [];
      baseData.contextCleaningRule = 'upon_request';
      baseData.contextCleaningTurns = undefined;
      baseData.iterationCount = 1;
      break;
      
    case 'job':
      baseData.subType = 'code';
      baseData.sourceDetails = '';
      baseData.description = '';
      break;
      
    case 'condition':
      baseData.conditionType = 'expression';
      baseData.expression = '';
      break;
      
    case 'db':
      baseData.subType = 'fixed_prompt';
      baseData.sourceDetails = 'Enter your fixed prompt or content here';
      baseData.description = '';
      break;
      
    case 'endpoint':
      baseData.description = '';
      baseData.saveToFile = false;
      baseData.filePath = '';
      baseData.fileFormat = 'json';
      break;
      
    case 'person_batch_job':
      baseData.personId = undefined;
      baseData.batchPrompt = '';
      baseData.batchSize = 10;
      baseData.parallelProcessing = false;
      baseData.aggregationMethod = 'concatenate';
      baseData.customAggregationPrompt = '';
      baseData.iterationCount = 1;
      break;
  }
  
  return baseData as DiagramNodeData;
}