/**
 * YAML format converter for DiPeO diagrams
 * 
 * Handles export/import of diagrams to/from YAML format
 */

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
  DomainHandle,
  HandleID,
  arrowId,
  personId,
  apiKeyId,
  NodeID,
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
import { ConverterCore } from '../core/converterCore';

export class YamlConverter extends ConverterCore<YamlDiagram> {
  /**
   * Serialize diagram to YAML string
   */
  serialize(diagram: ConverterDiagram): string {
    const yamlDiagram = this.toYamlFormat(diagram);
    return stringify(yamlDiagram, YAML_STRINGIFY_OPTIONS);
  }

  /**
   * Deserialize diagram from YAML string
   */
  deserialize(yamlString: string): ConverterDiagram {
    const yamlDiagram = parse(yamlString);
    return this.fromYamlFormat(yamlDiagram as YamlDiagram);
  }

  /**
   * Convert diagram to YAML format
   */
  private toYamlFormat(diagram: ConverterDiagram): YamlDiagram {
    // Reset state
    this.reset();
    
    const apiKeys: Record<string, { service: string; name: string }> = {};
    const persons: YamlDiagram['persons'] = {};
    const workflow: YamlDiagram['workflow'] = [];

    // Convert API keys - use name as key
    diagram.apiKeys.forEach(key => {
      const baseKey = this.convertApiKeyToBase(key);
      apiKeys[baseKey.label] = {
        service: baseKey.service,
        name: baseKey.label
      };
    });

    // Convert persons with full details - use label as key
    diagram.persons.forEach(person => {
      const basePerson = this.convertPersonToBase(person);
      persons[basePerson.label] = {
        model: basePerson.model || DEFAULT_MODEL,
        service: basePerson.service || DEFAULT_SERVICE,
        ...(basePerson.systemPrompt && { system: basePerson.systemPrompt })
      };
    });

    // Build adjacency map for connections
    const connectionMap = new Map<HandleID, DomainArrow[]>();
    diagram.arrows.forEach(arrow => {
      const arrows = connectionMap.get(arrow.source) || [];
      arrows.push(arrow);
      connectionMap.set(arrow.source, arrows);
    });

    // Convert nodes to workflow steps with full data
    diagram.nodes.forEach(node => {
      const baseNode = this.convertNodeToBase(node);
      const nodeHandleId = createHandleId(node.id, 'output');
      const connections = connectionMap.get(nodeHandleId) || [];
      const workflowNode = this.nodeToEnhancedStep(baseNode, node, connections);
      if (workflowNode) {
        workflow.push(workflowNode);
      }
    });

    return {
      version: YAML_VERSION as '1.0',
      metadata: {
        description: diagram.description || 'DiPeO workflow export'
      },
      title: diagram.name,
      apiKeys,
      persons,
      workflow
    };
  }

  /**
   * Convert node to enhanced workflow step
   */
  private nodeToEnhancedStep(
    baseNode: ReturnType<typeof this.convertNodeToBase>,
    originalNode: DomainNode,
    connections: DomainArrow[]
  ): YamlDiagram['workflow'][0] | null {
    const data = originalNode.data;
    const baseStep: YamlDiagram['workflow'][0] = {
      label: baseNode.label,
      type: baseNode.type,
      position: {
        x: Math.round(baseNode.position.x),
        y: Math.round(baseNode.position.y)
      }
    };

    // Add connections if any
    if (connections.length > 0) {
      baseStep.connections = connections.map(arrow => {
        // Parse target handle ID to get node ID and handle label
        const { nodeId: targetNodeId, handleLabel: targetHandleLabel } = parseHandleId(arrow.target);
        const { handleLabel: sourceHandleLabel } = parseHandleId(arrow.source);
        
        // Get target node label
        const targetLabel = this.nodeIdToLabel.get(targetNodeId) || targetNodeId;
        
        const connection: any = {
          to: targetLabel,
          source_handle: sourceHandleLabel,
          target_handle: targetHandleLabel,
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
      const personLabel = this.personIdToLabel.get(data.personId as PersonID);
      if (personLabel) {
        baseStep.person = personLabel;
      }
    }

    // Add all non-null fields from data based on node type
    const fieldMappings: Record<string, string> = {
      defaultPrompt: 'prompt',
      firstOnlyPrompt: 'first_prompt',
      contextCleaningRule: 'forget',
      iterationCount: 'max_iterations',
      maxIterations: 'max_iterations',
      conditionType: 'condition_type',
      expression: 'expression',
      sourceDetails: originalNode.type === 'db' ? 'source' : '',
      code: originalNode.type === 'job' ? 'code' : '',
      filePath: 'file',
      fileFormat: 'file_format',
      subType: 'sub_type',
      mode: 'mode'
    };
    
    Object.entries(fieldMappings).forEach(([dataKey, yamlKey]) => {
      if (yamlKey && data[dataKey] !== undefined && data[dataKey] !== null && data[dataKey] !== '') {
        (baseStep as any)[yamlKey] = data[dataKey];
      }
    });

    return baseStep;
  }

  /**
   * Convert from YAML format to diagram
   */
  private fromYamlFormat(yamlDiagram: YamlDiagram): ConverterDiagram {
    // Reset state
    this.reset();
    
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
        label: key.name,
        service: key.service as DomainApiKey['service'],
      });
      this.apiKeyLabelToId.set(key.name, apiKeyIdValue);
    });
    
    // Create API keys for services found in persons
    const serviceToApiKey = new Map<string, ApiKeyID>();
    Object.entries(yamlDiagram.persons || {}).forEach(([_label, person]) => {
      const service = (person.service || 'chatgpt') as DomainApiKey['service'];
      if (!serviceToApiKey.has(service) && !person.apiKeyLabel) {
        // Create API key for this service if not using explicit apiKeyLabel
        const newApiKeyId = apiKeyId(entityIdGenerators.apiKey());
        const newApiKey = {
          id: newApiKeyId,
          label: `${service.charAt(0).toUpperCase() + service.slice(1)} API Key`,
          service,
        };
        apiKeys.push(newApiKey);
        serviceToApiKey.set(service, newApiKeyId);
      }
    });

    // Convert persons
    Object.entries(yamlDiagram.persons || {}).forEach(([label, person]) => {
      const personIdValue = personId(`person-${generateShortId()}`);
      persons.push({
        id: personIdValue,
        label,
        model: person.model,
        service: (person.service || DEFAULT_SERVICE) as DomainPerson['service'],
        systemPrompt: person.system
      });
      this.personLabelToId.set(label, personIdValue);
    });
    
    // First pass: create nodes and build label-to-ID mapping
    yamlDiagram.workflow.forEach(step => {
      const nodeWithHandles = this.enhancedStepToNode(step);
      if (nodeWithHandles) {
        const { handles: nodeHandles, ...node } = nodeWithHandles;
        nodes.push(node);
        handles.push(...nodeHandles);
        this.nodeLabelToId.set(step.label, node.id);
      }
    });
    
    // Second pass: create arrows using label-to-ID mapping
    yamlDiagram.workflow.forEach(step => {
      if (step.connections) {
        const sourceId = this.nodeLabelToId.get(step.label);
        if (sourceId) {
          step.connections.forEach(conn => {
            const targetId = this.nodeLabelToId.get(conn.to);
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
  private enhancedStepToNode(
    step: YamlDiagram['workflow'][0]
  ): ReturnType<typeof buildNode> | null {
    const nodeInfo: NodeInfo = {
      name: step.label,
      type: step.type as NodeKind,
      position: step.position,
      // Common fields
      personId: step.person ? this.personLabelToId.get(step.person) : undefined,
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

// Legacy static class for backward compatibility
export class Yaml {
  private static converter = new YamlConverter();

  static toYAML(diagram: ConverterDiagram): string {
    return this.converter.serialize(diagram);
  }

  static fromYAML(yamlString: string): ConverterDiagram {
    return this.converter.deserialize(yamlString);
  }
}