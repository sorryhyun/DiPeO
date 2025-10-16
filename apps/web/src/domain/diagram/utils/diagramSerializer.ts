import { HandleDirection, HandleLabel, DataType, createHandleId, NodeID, JsonDict, type ApiKeyID, type PersonID } from '@dipeo/models';
import { DomainNode, DomainArrow, DomainPerson, DomainHandle, NodeType, apiKeyId } from '@/infrastructure/types';
import { getNodeConfig } from '@/domain/diagram/config/nodes';
import { diagramMapsToArrays } from '@/lib/graphql/types';
import { useUnifiedStore } from '@/infrastructure/store/unifiedStore';
import { Converters } from '@/infrastructure/converters';
import { stripTypenames } from '@/lib/utils';

export interface SerializedDiagram {
  nodes: DomainNode[];
  arrows: DomainArrow[];
  persons: DomainPerson[];
  handles: DomainHandle[];
  metadata: {
    name?: string | null;
    description?: string | null;
    author?: string | null;
    tags?: string[] | null;
    created: string;
    modified: string;
    version: string;
    id?: string | null;
  };
}


function cleanNodeData(node: DomainNode): DomainNode {
  const { data, ...nodeProps } = node;

  if (!data) {
    return {
      ...nodeProps,
      data: {
        label: nodeProps.type || 'Node'
      }
    };
  }

  const { _handles: _, inputs: _inputs, outputs: _outputs, type: _type, ...cleanData } = data as Record<string, unknown>;

  const nodeData = {
    ...cleanData
  };

  if (!nodeData.label) {
    nodeData.label = nodeProps.type || 'Node';
  }

  switch (nodeProps.type) {
    case NodeType.START:
      nodeData.custom_data = nodeData.custom_data || {};
      nodeData.output_data_structure = nodeData.output_data_structure || {};
      break;
    case NodeType.CONDITION:
      nodeData.condition_type = nodeData.condition_type || 'simple';
      break;
    case NodeType.PERSON_JOB:
      nodeData.first_only_prompt = nodeData.first_only_prompt || '';
      nodeData.max_iteration = typeof nodeData.max_iteration === 'number'
        ? nodeData.max_iteration
        : (Number(nodeData.max_iteration) || 1);
      if (typeof nodeData.tools === 'string') {
        nodeData.tools = nodeData.tools ? Converters.stringToToolsArray(nodeData.tools) : null;
      }
      break;
    case NodeType.ENDPOINT:
      nodeData.save_to_file = nodeData.save_to_file ?? false;
      break;
    case NodeType.DB:
      nodeData.sub_type = nodeData.sub_type || 'fixed_prompt';
      nodeData.operation = nodeData.operation || 'read';
      break;
    case NodeType.USER_RESPONSE:
      nodeData.prompt = nodeData.prompt || '';
      nodeData.timeout = nodeData.timeout || 60;
      break;
  }

  return {
    ...nodeProps,
    data: nodeData as JsonDict
  };
}

function generateHandlesForNode(node: DomainNode): DomainHandle[] {
  const handles: DomainHandle[] = [];
  const nodeType = node.type as string;
  const config = getNodeConfig(nodeType);

  if (!config?.handles) {
    return handles;
  }

  if (config.handles.input) {
    config.handles.input.forEach((handleConfig: { label: string; displayLabel?: string; position?: string }) => {
      const handleLabel = handleConfig.label as HandleLabel;
      const handleId = Converters.createHandleId(Converters.toNodeId(node.id), handleLabel, HandleDirection.INPUT);
      handles.push({
        id: handleId,
        node_id: node.id,
        label: handleLabel,
        direction: HandleDirection.INPUT,
        data_type: DataType.ANY,
        position: handleConfig.position || 'left'
      });
    });
  }

  if (config.handles.output) {
    config.handles.output.forEach((handleConfig: { label: string; displayLabel?: string; position?: string }) => {
      const handleLabel = handleConfig.label as HandleLabel;
      const handleId = Converters.createHandleId(Converters.toNodeId(node.id), handleLabel, HandleDirection.OUTPUT);
      handles.push({
        id: handleId,
        node_id: node.id,
        label: handleLabel,
        direction: HandleDirection.OUTPUT,
        data_type: DataType.ANY,
        position: handleConfig.position || 'right'
      });
    });
  }

  return handles;
}

function getStoreStateWithMaps() {
  const state = useUnifiedStore.getState();

  const personsWithRequiredFields = new Map(state.persons);
  personsWithRequiredFields.forEach((person, id) => {
    if (person.llm_config && !person.llm_config.api_key_id) {
      personsWithRequiredFields.set(id, {
        ...person,
        llm_config: {
          ...person.llm_config,
          api_key_id: apiKeyId('default')
        }
      });
    }
  });

  return {
    nodes: state.nodes,
    handles: state.handles,
    arrows: state.arrows,
    persons: personsWithRequiredFields as Map<PersonID, DomainPerson>
  };
}

export function serializeDiagram(): SerializedDiagram {
  const now = new Date();

  const state = useUnifiedStore.getState();

  const metadata = {
    name: state.diagramName || 'Untitled Diagram',
    description: state.diagramDescription || null,
    author: null,
    tags: null,
    created: now.toISOString(),
    modified: now.toISOString(),
    version: '1.0.0',
    id: state.diagramId || null
  };

  const storeMaps = getStoreStateWithMaps();
  const diagramArrays = diagramMapsToArrays(storeMaps);

  const cleanNodes = diagramArrays.nodes?.map(node => cleanNodeData(node)) || [];

  const existingHandles = diagramArrays.handles || [];

  const existingHandleMap = Converters.arrayToMap(existingHandles, handle => handle.id);

  const generatedHandles: DomainHandle[] = [];
  cleanNodes.forEach(node => {
    const nodeHandles = generateHandlesForNode(node);

    nodeHandles.forEach(newHandle => {
      if (!existingHandleMap.has(newHandle.id)) {
        generatedHandles.push(newHandle);
        existingHandleMap.set(newHandle.id, newHandle);
      }
    });
  });

  const allHandles = Array.from(existingHandleMap.values());

  const nodeIds = Converters.arrayToUniqueSet(cleanNodes, node => node.id);
  const validHandles = allHandles.filter(handle => {
    if (!nodeIds.has(handle.node_id)) {
      console.warn(`Removing orphaned handle ${handle.id} for non-existent node ${handle.node_id}`);
      return false;
    }
    return true;
  });

  const allHandleIds = Converters.arrayToUniqueSet(allHandles, handle => handle.id);

  const validArrows = (diagramArrays.arrows || []).filter(arrow => {
    const sourceValid = allHandleIds.has(arrow.source);
    const targetValid = allHandleIds.has(arrow.target);

    if (!sourceValid || !targetValid) {
      console.warn(`Removing arrow ${arrow.id} with invalid handle references: ${arrow.source} -> ${arrow.target}`);
      return false;
    }

    const sourceHandle = existingHandleMap.get(arrow.source);
    const targetHandle = existingHandleMap.get(arrow.target);

    if (sourceHandle && !nodeIds.has(sourceHandle.node_id)) {
      console.warn(`Removing arrow ${arrow.id} - source handle belongs to non-existent node`);
      return false;
    }

    if (targetHandle && !nodeIds.has(targetHandle.node_id)) {
      console.warn(`Removing arrow ${arrow.id} - target handle belongs to non-existent node`);
      return false;
    }

    return true;
  });

  const cleanPersons = (diagramArrays.persons || []).map(person => {
    const { masked_api_key: _masked_api_key, ...cleanPerson } = person as DomainPerson & { masked_api_key?: string };
    return cleanPerson as DomainPerson;
  });

  return stripTypenames({
    nodes: cleanNodes,
    arrows: validArrows,
    persons: cleanPersons,
    handles: validHandles,
    metadata
  });
}
