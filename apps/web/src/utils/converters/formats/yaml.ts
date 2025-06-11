// apps/web/src/utils/yaml.ts
import { stringify, parse } from 'yaml';
import { 
  NodeKind,
  generateShortId,
  entityIdGenerators,
  createHandleId,
  parseHandleId,
  DomainNode,
  DomainArrow,
  DomainPerson,
  DomainApiKey,
  DomainDiagram,
  DomainHandle,
  nodeId,
  arrowId,
  personId,
  apiKeyId,
  NodeID,
  ArrowID,
  PersonID,
  ApiKeyID
} from '@/types';
import { buildNode } from '../core/nodeBuilders';
import type { ConverterDiagram, YamlDiagram, NodeInfo } from '../types';
import { 
  YAML_VERSION, 
  YAML_STRINGIFY_OPTIONS, 
  DEFAULT_MODEL, 
  DEFAULT_SERVICE,
  DEFAULT_CONTEXT_CLEANING_RULE 
} from '../constants';


export class Yaml {
  /**
   * Convert DiagramState to enhanced YAML format with full data preservation
   */
  static toYAML(diagram: ConverterDiagram): string {
    const yamlDiagram = this.toYamlFormat(diagram);

    return stringify(yamlDiagram, YAML_STRINGIFY_OPTIONS);
  }

  static fromYAML(yamlString: string): ConverterDiagram {
    const yamlDiagram = parse(yamlString);
    return this.fromYamlFormat(yamlDiagram as YamlDiagram);
  }
  /**
   * Convert DiagramState to YAML format
   */
  private static toYamlFormat(diagram: ConverterDiagram): YamlDiagram {
    const apiKeys: Record<string, { service: string; name: string }> = {};
    const persons: YamlDiagram['persons'] = {};
    const workflow: YamlDiagram['workflow'] = [];

    // Convert API keys - use name as key
    diagram.apiKeys.forEach(key => {
      apiKeys[key.name] = {
        service: key.service,
        name: key.name
      };
    });

    // Convert persons with full details - use label as key
    diagram.persons.forEach(person => {
      // Use service from person
      const service = person.service || DEFAULT_SERVICE; // default
      
      persons[person.label] = {
        model: person.model || DEFAULT_MODEL,
        service,
        ...(person.systemPrompt && { system: person.systemPrompt })
      };
    });

    // Build adjacency map for connections
    const connectionMap = new Map<string, DomainArrow[]>();
    diagram.arrows.forEach(arrow => {
      const arrows = connectionMap.get(arrow.source) || [];
      arrows.push(arrow);
      connectionMap.set(arrow.source, arrows);
    });

    // Convert nodes to workflow steps with full data
    diagram.nodes.forEach(node => {
      const connections = connectionMap.get(node.id) || [];
      // Find handles for this node
      const nodeHandles = diagram.handles.filter(h => h.nodeId === node.id);
      const workflowNode = this.nodeToEnhancedStep(node, nodeHandles, connections, diagram.persons);
      if (workflowNode) {
        workflow.push(workflowNode);
      }
    });

    return {
      version: YAML_VERSION as '1.0',
      metadata: {
        description: 'DiPeO workflow export'
      },
      apiKeys,
      persons,
      workflow
    };
  }

  /**
   * Convert node to enhanced workflow step
   */
  private static nodeToEnhancedStep(
    node: DomainNode,
    _handles: DomainHandle[],
    connections: DomainArrow[],
    persons: DomainPerson[]
  ): YamlDiagram['workflow'][0] | null {
    const data = node.data;
    const baseStep: YamlDiagram['workflow'][0] = {
      label: String(data.label || node.id),
      type: node.type as string,
      position: {
        x: Math.round(node.position.x),
        y: Math.round(node.position.y)
      }
    };

    // Add connections if any
    if (connections.length > 0) {
      baseStep.connections = connections.map(arrow => {
        // Parse target handle ID to get node ID and handle name
        const { nodeId: targetNodeId, handleName: targetHandleName } = parseHandleId(arrow.target);
        const { handleName: sourceHandleName } = parseHandleId(arrow.source);
        
        const connection: any = {
          to: targetNodeId,
          source_handle: sourceHandleName,
          target_handle: targetHandleName,
        };
        
        if (arrow.data) {
          if (arrow.data.label) connection.label = arrow.data.label;
          if (arrow.data.contentType) connection.content_type = arrow.data.contentType;
          if (arrow.data.branch) connection.branch = arrow.data.branch;
          if (arrow.data.controlPointOffsetX !== undefined && arrow.data.controlPointOffsetY !== undefined) {
            connection.control_offset = {
              x: Math.round(Number(arrow.data.controlPointOffsetX)),
              y: Math.round(Number(arrow.data.controlPointOffsetY))
            };
          }
        }
        
        return connection;
      });
    }

    // Find person label if needed
    if (data.personId) {
      const person = persons.find(p => p.id === data.personId);
      if (person) {
        baseStep.person = person.label;
      }
    }

    // Add all non-null fields from data based on node type
    const fieldMappings: Record<string, string> = {
      defaultPrompt: 'prompt',
      firstOnlyPrompt: 'first_prompt',
      contextCleaningRule: 'forget',
      iterationCount: 'max_iterations',
      conditionType: 'condition_type',
      sourceDetails: node.type === 'db' ? 'source' : 'code',
      filePath: 'file',
      fileFormat: 'file_format',
      subType: 'sub_type'
    };
    
    Object.entries(fieldMappings).forEach(([dataKey, yamlKey]) => {
      if (data[dataKey] !== undefined && data[dataKey] !== null && data[dataKey] !== '') {
        (baseStep as any)[yamlKey] = data[dataKey];
      }
    });

    return baseStep;
  }

  /**
   * Convert enhanced YAML format back to DiagramState
   */
  private static fromYamlFormat(yamlDiagram: YamlDiagram): ConverterDiagram {
    const nodes: DomainNode[] = [];
    const handles: DomainHandle[] = [];
    const arrows: DomainArrow[] = [];
    const persons: DomainPerson[] = [];
    const apiKeys: DomainApiKey[] = [];

    // Convert API keys - generate new IDs
    Object.entries(yamlDiagram.apiKeys || {}).forEach(([_name, key]) => {
      const apiKeyIdValue = apiKeyId(entityIdGenerators.apiKey());
      apiKeys.push({
        id: apiKeyIdValue,
        name: key.name,
        service: key.service as DomainApiKey['service'],
        // key is optional - not stored in frontend
      });
    });


    // Create label-to-ID mappings for references
    const apiKeyLabelToId = new Map<string, string>();
    apiKeys.forEach(key => {
      apiKeyLabelToId.set(key.name, key.id);
    });
    
    // Create API keys for services found in persons
    const serviceToApiKey = new Map<string, string>();
    Object.entries(yamlDiagram.persons || {}).forEach(([_label, person]) => {
      const service = (person.service || 'chatgpt') as DomainApiKey['service'];
      if (!serviceToApiKey.has(service) && !person.apiKeyLabel) {
        // Create API key for this service if not using explicit apiKeyLabel
        const newApiKeyId = apiKeyId(entityIdGenerators.apiKey());
        const newApiKey = {
          id: newApiKeyId,
          name: `${service.charAt(0).toUpperCase() + service.slice(1)} API Key`,
          service,
          // key is optional - not stored in frontend
        };
        apiKeys.push(newApiKey);
        serviceToApiKey.set(service, newApiKeyId);
      }
    });

    Object.entries(yamlDiagram.persons || {}).forEach(([label, person]) => {
      // Skip API key resolution - not part of DomainPerson
      
      persons.push({
        id: personId(`person-${generateShortId()}`),  // Generate fresh ID
        label,  // Use the key as label
        model: person.model,
        service: (person.service || DEFAULT_SERVICE) as DomainPerson['service'],
        systemPrompt: person.system
      });
    });

    // Create label-to-ID mappings for node references
    const nodeLabelToId = new Map<string, string>();
    const personNameToId = new Map<string, PersonID>();
    persons.forEach(person => {
      personNameToId.set(person.label, person.id);
    });
    
    // First pass: create nodes and build label-to-ID mapping
    yamlDiagram.workflow.forEach(step => {
      const nodeWithHandles = this.enhancedStepToNode(step, persons, personNameToId);
      if (nodeWithHandles) {
        const { handles: nodeHandles, ...node } = nodeWithHandles;
        nodes.push(node);
        handles.push(...nodeHandles);
        nodeLabelToId.set(step.label, node.id);
      }
    });
    
    // Second pass: create arrows using label-to-ID mapping
    yamlDiagram.workflow.forEach(step => {
      if (step.connections) {
        const sourceId = nodeLabelToId.get(step.label);
        if (sourceId) {
          step.connections.forEach(conn => {
            const targetId = nodeLabelToId.get(conn.to);
            if (targetId) {
              const arrowIdValue = arrowId(`arrow-${generateShortId()}`);
              
              // Create handle IDs from node IDs and handle names
              const sourceHandleId = createHandleId(sourceId as NodeID, conn.source_handle || 'output');
              const targetHandleId = createHandleId(targetId as NodeID, conn.target_handle || 'input');
              
              arrows.push({
                id: arrowIdValue,
                source: sourceHandleId,
                target: targetHandleId,
                data: {
                  label: conn.label || 'flow',
                  contentType: conn.content_type || 'raw_text',
                  branch: conn.branch as 'true' | 'false' | undefined,
                  controlPointOffsetX: conn.control_offset?.x,
                  controlPointOffsetY: conn.control_offset?.y
                }
              });
            }
          });
        }
      }
    });

    return {
      id: `diagram-${generateShortId()}`,
      name: yamlDiagram.title || 'Imported Diagram',
      description: yamlDiagram.metadata?.description,
      nodes,
      arrows,
      persons,
      apiKeys,
      handles
    };
  }

  /**
   * Convert enhanced step back to node
   */
  private static enhancedStepToNode(
    step: YamlDiagram['workflow'][0],
    _persons: DomainPerson[],
    personLabelToId: Map<string, PersonID>
  ): ReturnType<typeof buildNode> | null {
    const nodeInfo: NodeInfo = {
      name: step.label,
      type: step.type as NodeKind,
      position: step.position,
      // Common fields
      personId: step.person ? personLabelToId.get(step.person) : undefined,
      prompt: step.prompt,
      firstPrompt: step.first_prompt,
      contextCleaningRule: step.forget || DEFAULT_CONTEXT_CLEANING_RULE,
      maxIterations: step.max_iterations,
      mode: step.mode,
      // Condition fields
      conditionType: step.condition_type,
      expression: step.expression,
      // DB fields
      subType: step.sub_type,
      sourceDetails: step.source,
      // Job fields
      code: step.code,
      // Endpoint fields
      filePath: step.file,
      fileFormat: step.file_format
    };
    
    return buildNode(nodeInfo);
  }

}