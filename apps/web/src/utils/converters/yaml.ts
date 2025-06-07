// apps/web/src/utils/yaml.ts
import { stringify, parse } from 'yaml';
import { Diagram, Person, Arrow, ApiKey, Node } from '@/types/core';
import { nanoid } from 'nanoid';
import { buildNode, NodeInfo } from './nodeBuilders';

interface YamlDiagram {
  version: '1.0';
  title?: string;
  metadata?: {
    description?: string;
  };

  // API Keys section - labels only
  apiKeys: Record<string, {
    service: string;
    name: string;
  }>;

  // Enhanced persons with full details - label-based
  persons: Record<string, {
    model: string;
    service: string;
    apiKeyLabel?: string;  // Reference by label
    system?: string;
    temperature?: number;
  }>;

  // Enhanced workflow with positions - label-based
  workflow: {
    label: string;  // Use label as primary identifier
    type: string;
    position: { x: number; y: number };  // Preserved positions
    person?: string;  // Person label reference

    // All node-specific fields preserved
    prompt?: string;
    first_prompt?: string;
    source?: string;
    code?: string;
    expression?: string;
    file?: string;
    file_format?: string;
    forget?: string;
    max_iterations?: number;
    mode?: string;
    condition_type?: string;
    sub_type?: string;

    // Connections with full arrow data
    connections?: {
      to: string;
      label?: string;
      content_type?: string;
      branch?: string;
      source_handle?: string;
      target_handle?: string;
      control_offset?: { x: number; y: number };
    }[];
  }[];
}


export class Yaml {
  /**
   * Convert DiagramState to enhanced YAML format with full data preservation
   */
  static toYAML(diagram: Diagram): string {
    const yamlDiagram = this.toYamlFormat(diagram);

    return stringify(yamlDiagram, {
      indent: 2,
      lineWidth: 120,
      defaultKeyType: 'PLAIN',  // Forces plain keys without quotes
      defaultStringType: 'QUOTE_DOUBLE',  // Only quote string values when needed
    });
  }

  static fromYAML(yamlString: string): Diagram {
    const yamlDiagram = parse(yamlString);
    return this.fromYamlFormat(yamlDiagram as YamlDiagram);
  }
  /**
   * Convert DiagramState to YAML format
   */
  private static toYamlFormat(diagram: Diagram): YamlDiagram {
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

    // Convert persons to agents with full details - use label as key
    diagram.persons.forEach(person => {
      // Find API key label by ID
      let apiKeyLabel: string | undefined;
      if (person.apiKeyId) {
        const apiKey = diagram.apiKeys.find(k => k.id === person.apiKeyId);
        if (apiKey) {
          apiKeyLabel = apiKey.name;
        }
      }
      
      persons[person.label] = {
        model: person.modelName || 'gpt-4.1-nano',
        service: person.service || 'chatgpt',
        ...(apiKeyLabel && { apiKeyLabel }),
        ...(person.systemPrompt && { system: person.systemPrompt })
      };
    });

    // Build adjacency map for connections
    const connectionMap = new Map<string, Arrow[]>();
    diagram.arrows.forEach(arrow => {
      const arrows = connectionMap.get(arrow.source) || [];
      arrows.push(arrow);
      connectionMap.set(arrow.source, arrows);
    });

    // Convert nodes to workflow steps with full data
    diagram.nodes.forEach(node => {
      const connections = connectionMap.get(node.id) || [];
      const workflowNode = this.nodeToEnhancedStep(node, connections, diagram.persons);
      if (workflowNode) {
        workflow.push(workflowNode);
      }
    });

    return {
      version: '1.0',
      metadata: {
        description: 'AgentDiagram workflow export'
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
    node: Node,
    connections: Arrow[],
    persons: Person[]
  ): YamlDiagram['workflow'][0] | null {
    const data = node.data;
    const baseStep: YamlDiagram['workflow'][0] = {
      label: data.label || node.id,
      type: node.type as string,
      position: {
        x: Math.round(node.position.x),
        y: Math.round(node.position.y)
      }
    };

    // Add connections if any
    if (connections.length > 0) {
      baseStep.connections = connections.map(arrow => ({
        to: arrow.target,
        ...(arrow.data?.label && { label: arrow.data.label }),
        ...((arrow.data?.controlPointOffsetX !== undefined || arrow.data?.controlPointOffsetY !== undefined) && {
          control_offset: {
            x: Math.round(arrow.data?.controlPointOffsetX || 0),
            y: Math.round(arrow.data?.controlPointOffsetY || 0)
          }
        })
      }));
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
  private static fromYamlFormat(yamlDiagram: YamlDiagram): Diagram {
    const nodes: Node[] = [];
    const arrows: Arrow[] = [];
    const persons: Person[] = [];
    const apiKeys: ApiKey[] = [];

    // Convert API keys - generate new IDs
    Object.entries(yamlDiagram.apiKeys || {}).forEach(([_name, key]) => {
      apiKeys.push({
        id: `APIKEY_${nanoid().slice(0, 4).replace(/-/g, '_').toUpperCase()}`,
        name: key.name,
        service: key.service as ApiKey['service']
      });
    });


    // Create label-to-ID mappings for references
    const apiKeyLabelToId = new Map<string, string>();
    apiKeys.forEach(key => {
      apiKeyLabelToId.set(key.name, key.id);
    });
    
    Object.entries(yamlDiagram.persons || {}).forEach(([label, person]) => {
      // Resolve API key reference
      let apiKeyId: string | undefined;
      if (person.apiKeyLabel && apiKeyLabelToId.has(person.apiKeyLabel)) {
        apiKeyId = apiKeyLabelToId.get(person.apiKeyLabel);
      }
      
      persons.push({
        id: `person-${nanoid(4)}`,  // Generate fresh ID
        label,  // Use the key as label
        modelName: person.model,
        service: person.service as ApiKey['service'],
        apiKeyId,
        systemPrompt: person.system
      });
    });

    // Create label-to-ID mappings for node references
    const nodeLabelToId = new Map<string, string>();
    const personLabelToId = new Map<string, string>();
    persons.forEach(person => {
      personLabelToId.set(person.label, person.id);
    });
    
    // First pass: create nodes and build label-to-ID mapping
    yamlDiagram.workflow.forEach(step => {
      const node = this.enhancedStepToNode(step, persons, personLabelToId);
      if (node) {
        nodes.push(node);
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
              const arrowId = `arrow-${nanoid(4)}`;
              arrows.push({
                id: arrowId,
                source: sourceId,
                target: targetId,
                type: 'customArrow',
                sourceHandle: conn.source_handle,
                targetHandle: conn.target_handle,
                data: {
                  id: arrowId,
                  sourceBlockId: sourceId,
                  targetBlockId: targetId,
                  sourceHandleId: conn.source_handle,
                  targetHandleId: conn.target_handle,
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
      nodes,
      arrows,
      persons,
      apiKeys
    };
  }

  /**
   * Convert enhanced step back to node
   */
  private static enhancedStepToNode(
    step: YamlDiagram['workflow'][0],
    _persons: Person[],
    personLabelToId: Map<string, string>
  ): Node | null {
    const nodeInfo: NodeInfo = {
      name: step.label,
      type: step.type as any,
      position: step.position,
      // Common fields
      personId: step.person ? personLabelToId.get(step.person) : undefined,
      prompt: step.prompt,
      firstPrompt: step.first_prompt,
      contextCleaningRule: step.forget || 'upon_request',
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