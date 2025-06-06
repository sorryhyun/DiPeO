// apps/web/src/utils/yamlExporter.ts
import { stringify, parse } from 'yaml';
import {
  Diagram,
  Person,
  Arrow,
  ApiKey,
  Node
} from '../../../types';
import { nanoid } from 'nanoid';

interface YamlDiagram {
  version: '1.0';
  title?: string;
  metadata?: {
    description?: string;
  };

  // API Keys section - NEW
  apiKeys: Record<string, {
    service: string;
    name: string;
  }>;

  // Enhanced persons with full details
  persons: Record<string, {
    id: string;  // Original ID preserved
    model: string;
    service: string;
    apiKeyId?: string;
    system?: string;
    temperature?: number;
  }>;

  // Enhanced workflow with positions
  workflow: {
    id: string;  // Original node ID
    type: string;
    label?: string;
    position: { x: number; y: number };  // Preserved positions
    person?: string;

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


export class YamlExporter {
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

    // Convert API keys
    diagram.apiKeys.forEach(key => {
      apiKeys[key.id] = {
        service: key.service,
        name: key.name
      };
    });

    // Convert persons to agents with full details
    diagram.persons.forEach(person => {
      persons[person.id] = {
        id: person.id,
        model: person.modelName || 'gpt-4.1-nano',
        service: person.service || 'chatgpt',
        ...(person.apiKeyId && { apiKeyId: person.apiKeyId }),
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
    _persons: Person[]
  ): YamlDiagram['workflow'][0] | null {
    const data = node.data;
    const baseStep: YamlDiagram['workflow'][0] = {
      id: node.id,
      type: node.type as string,
      position: {
        x: Math.round(node.position.x),
        y: Math.round(node.position.y)
      },
      ...(data.label && { label: data.label })
    };

    // Add connections if any
    if (connections.length > 0) {
      baseStep.connections = connections.map(arrow => ({
        to: arrow.target,
        ...(arrow.data?.label && { label: arrow.data.label }),
        // Prioritize edge's direct handle properties, fallback to data
        ...((arrow.data?.controlPointOffsetX !== undefined || arrow.data?.controlPointOffsetY !== undefined) && {
          control_offset: {
            x: Math.round(arrow.data?.controlPointOffsetX || 0),
            y: Math.round(arrow.data?.controlPointOffsetY || 0)
          }
        })
      }));
    }

    // Add type-specific fields
    switch (node.type) {
      case 'start':
        return baseStep;

      case 'person_job': {
        return {
          ...baseStep,
          ...(data.personId && { person: data.personId }),
          ...(data.defaultPrompt && { prompt: data.defaultPrompt }),
          ...(data.firstOnlyPrompt && { first_prompt: data.firstOnlyPrompt }),
          ...(data.contextCleaningRule && { forget: data.contextCleaningRule }),
          ...(data.iterationCount && { max_iterations: data.iterationCount })
        };
      }

      case 'condition': {
        return {
          ...baseStep,
          ...(data.conditionType && { condition_type: data.conditionType }),
          ...(data.expression && { expression: data.expression }),
          ...(data.maxIterations && { max_iterations: data.maxIterations })
        };
      }

      case 'db': {
        return {
          ...baseStep,
          ...(data.subType && { sub_type: data.subType }),
          ...(data.sourceDetails && { source: data.sourceDetails })
        };
      }

      case 'job': {
        return {
          ...baseStep,
          ...(data.subType && { sub_type: data.subType }),
          ...(data.sourceDetails && { code: data.sourceDetails })
        };
      }

      case 'endpoint': {
        return {
          ...baseStep,
          ...(data.saveToFile && data.filePath && { file: data.filePath }),
          ...(data.fileFormat && { file_format: data.fileFormat })
        };
      }

      default:
        return baseStep;
    }
  }

  /**
   * Convert enhanced YAML format back to DiagramState
   */
  private static fromYamlFormat(yamlDiagram: YamlDiagram): Diagram {
    const nodes: Node[] = [];
    const arrows: Arrow[] = [];
    const persons: Person[] = [];
    const apiKeys: ApiKey[] = [];

    // Convert API keys
    Object.entries(yamlDiagram.apiKeys || {}).forEach(([id, key]) => {
      apiKeys.push({
        id,
        name: key.name,
        service: key.service as ApiKey['service']
      });
    });


    Object.entries(yamlDiagram.persons || {}).forEach(([id, person]) => {
      persons.push({
        id: person.id || id,
        label: this.extractLabelFromId(person.id || id),
        modelName: person.model,
        service: person.service as ApiKey['service'],
        apiKeyId: person.apiKeyId,
        systemPrompt: person.system
      });
    });

    // Convert workflow to nodes and arrows
    yamlDiagram.workflow.forEach(step => {
      const node = this.enhancedStepToNode(step, persons);
      if (node) {
        nodes.push(node);

        // Create arrows from connections
        if (step.connections) {
          step.connections.forEach(conn => {
            const arrowId = `arrow-${nanoid(6)}`;
            arrows.push({
              id: arrowId,
              source: step.id,
              target: conn.to,
              type: 'customArrow',
              sourceHandle: conn.source_handle,
              targetHandle: conn.target_handle,
              data: {
                id: arrowId,
                sourceBlockId: step.id,
                targetBlockId: conn.to,
                sourceHandleId: conn.source_handle,
                targetHandleId: conn.target_handle,
                label: conn.label || 'flow',
                contentType: conn.content_type || 'raw_text',
                branch: conn.branch as 'true' | 'false' | undefined,
                controlPointOffsetX: conn.control_offset?.x,
                controlPointOffsetY: conn.control_offset?.y
              }
            });
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
    _persons: Person[]
  ): Node | null {
    const baseData = {
      id: step.id,
      label: step.label || this.extractLabelFromId(step.id)
    };

    const position = {
      x: step.position.x,
      y: step.position.y
    };

    switch (step.type) {
      case 'start':
        return {
          id: step.id,
          type: 'start',
          position,
          data: {
            ...baseData,
            type: 'start'
          }
        };

      case 'person_job':
        return {
          id: step.id,
          type: 'person_job',
          position,
          data: {
            ...baseData,
            type: 'person_job',
            personId: step.person,
            defaultPrompt: step.prompt || '',
            firstOnlyPrompt: step.first_prompt || '',
            contextCleaningRule: step.forget || 'uponRequest',
            iterationCount: step.max_iterations || 1,
            mode: step.mode || 'sync',
            detectedVariables: this.detectVariables(step.prompt || '', step.first_prompt || '')
          }
        };

      case 'condition':
        return {
          id: step.id,
          type: 'condition',
          position,
          data: {
            ...baseData,
            type: 'condition',
            conditionType: step.condition_type || 'expression',
            expression: step.expression || '',
            maxIterations: step.max_iterations
          }
        };

      case 'db':
        return {
          id: step.id,
          type: 'db',
          position,
          data: {
            ...baseData,
            type: 'db',
            subType: step.sub_type || 'fixed_prompt',
            sourceDetails: step.source || ''
          }
        };

      case 'job':
        return {
          id: step.id,
          type: 'job',
          position,
          data: {
            ...baseData,
            type: 'job',
            subType: step.sub_type || 'code',
            sourceDetails: step.code || ''
          }
        };

      case 'endpoint':
        return {
          id: step.id,
          type: 'endpoint',
          position,
          data: {
            ...baseData,
            type: 'endpoint',
            saveToFile: !!step.file,
            filePath: step.file || '',
            fileFormat: step.file_format || 'text'
          }
        };

      default:
        return null;
    }
  }

  /**
   * Utility functions
   */

  private static extractLabelFromId(id: string): string {
    // Extract meaningful label from IDs like "PERSON_ABC123" -> "Person ABC123"
    return id.replace(/_/g, ' ').replace(/([A-Z]+)([A-Z][a-z])/g, '$1 $2');
  }

  private static detectVariables(...prompts: string[]): string[] {
    const vars = new Set<string>();
    const varPattern = /{{(\w+)}}/g;

    prompts.forEach(prompt => {
      if (prompt) {
        const matches = prompt.matchAll(varPattern);
        for (const match of matches) {
          vars.add(match[1] || '');
        }
      }
    });

    return Array.from(vars);
  }
}