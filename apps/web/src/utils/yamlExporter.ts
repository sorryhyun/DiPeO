// apps/web/src/utils/yamlExporter.ts
import { stringify, parse } from 'yaml';
import {
  DiagramState,
  PersonDefinition,
  PersonJobBlockData,
  JobBlockData,
  DBBlockData,
  ConditionBlockData,
  EndpointBlockData,
  ArrowData,
  ApiKey,
  DiagramNode
} from '@repo/core-model';
import type { Edge } from '@xyflow/react';
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
  static toYAML(diagram: DiagramState): string {
    const yamlDiagram = this.toYamlFormat(diagram);

    return stringify(yamlDiagram, {
      indent: 2,
      lineWidth: 120,
      defaultKeyType: 'PLAIN',  // Forces plain keys without quotes
      defaultStringType: 'QUOTE_DOUBLE',  // Only quote string values when needed
    });
  }

  static fromYAML(yamlString: string): DiagramState {
    const yamlDiagram = parse(yamlString);
    return this.fromYamlFormat(yamlDiagram as YamlDiagram);
  }
  /**
   * Convert DiagramState to YAML format
   */
  private static toYamlFormat(diagram: DiagramState): YamlDiagram {
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
    const connectionMap = new Map<string, Edge<ArrowData>[]>();
    diagram.arrows.forEach(arrow => {
      const edges = connectionMap.get(arrow.source) || [];
      edges.push(arrow);
      connectionMap.set(arrow.source, edges);
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
    node: DiagramNode,
    connections: Edge<ArrowData>[],
    _persons: PersonDefinition[]
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
      baseStep.connections = connections.map(edge => ({
        to: edge.target,
        ...(edge.data?.label && { label: edge.data.label }),
        ...(edge.data?.contentType && { content_type: edge.data.contentType }),
        ...(edge.data?.branch && { branch: edge.data.branch }),
        // Prioritize edge's direct handle properties, fallback to data
        ...((edge.sourceHandle || edge.data?.sourceHandleId) && { 
          source_handle: edge.sourceHandle || edge.data?.sourceHandleId 
        }),
        ...((edge.targetHandle || edge.data?.targetHandleId) && { 
          target_handle: edge.targetHandle || edge.data?.targetHandleId 
        }),
        ...((edge.data?.controlPointOffsetX !== undefined || edge.data?.controlPointOffsetY !== undefined) && {
          control_offset: {
            x: Math.round(edge.data?.controlPointOffsetX || 0),
            y: Math.round(edge.data?.controlPointOffsetY || 0)
          }
        })
      }));
    }

    // Add type-specific fields
    switch (node.type) {
      case 'startNode':
        return baseStep;

      case 'personjobNode': {
        const pjData = data as PersonJobBlockData;
        return {
          ...baseStep,
          ...(pjData.personId && { person: pjData.personId }),
          ...(pjData.defaultPrompt && { prompt: pjData.defaultPrompt }),
          ...(pjData.firstOnlyPrompt && { first_prompt: pjData.firstOnlyPrompt }),
          ...(pjData.contextCleaningRule && { forget: pjData.contextCleaningRule }),
          ...(pjData.iterationCount && { max_iterations: pjData.iterationCount }),
          ...(pjData.mode && { mode: pjData.mode })
        };
      }

      case 'conditionNode': {
        const cData = data as ConditionBlockData;
        return {
          ...baseStep,
          ...(cData.conditionType && { condition_type: cData.conditionType }),
          ...(cData.expression && { expression: cData.expression }),
          ...(cData.maxIterations && { max_iterations: cData.maxIterations })
        };
      }

      case 'dbNode': {
        const dbData = data as DBBlockData;
        return {
          ...baseStep,
          ...(dbData.subType && { sub_type: dbData.subType }),
          ...(dbData.sourceDetails && { source: dbData.sourceDetails })
        };
      }

      case 'jobNode': {
        const jobData = data as JobBlockData;
        return {
          ...baseStep,
          ...(jobData.subType && { sub_type: jobData.subType }),
          ...(jobData.sourceDetails && { code: jobData.sourceDetails })
        };
      }

      case 'endpointNode': {
        const epData = data as EndpointBlockData;
        return {
          ...baseStep,
          ...(epData.saveToFile && epData.filePath && { file: epData.filePath }),
          ...(epData.fileFormat && { file_format: epData.fileFormat })
        };
      }

      default:
        return baseStep;
    }
  }

  /**
   * Convert enhanced YAML format back to DiagramState
   */
  private static fromYamlFormat(yamlDiagram: YamlDiagram): DiagramState {
    const nodes: DiagramNode[] = [];
    const arrows: Edge<ArrowData>[] = [];
    const persons: PersonDefinition[] = [];
    const apiKeys: ApiKey[] = [];

    // Convert API keys
    Object.entries(yamlDiagram.apiKeys || {}).forEach(([id, key]) => {
      apiKeys.push({
        id,
        name: key.name,
        service: key.service as any
      });
    });


    Object.entries(yamlDiagram.persons || {}).forEach(([id, person]) => {
      persons.push({
        id: person.id || id,
        label: this.extractLabelFromId(person.id || id),
        modelName: person.model,
        service: person.service as any,
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
                contentType: conn.content_type as any,
                branch: conn.branch as any,
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
    _persons: PersonDefinition[]
  ): DiagramNode | null {
    const baseData = {
      id: step.id,
      label: step.label || this.extractLabelFromId(step.id)
    };

    const position = {
      x: step.position.x,
      y: step.position.y
    };

    switch (step.type) {
      case 'startNode':
        return {
          id: step.id,
          type: 'startNode',
          position,
          data: {
            ...baseData,
            type: 'start'
          }
        };

      case 'personjobNode':
        return {
          id: step.id,
          type: 'personjobNode',
          position,
          data: {
            ...baseData,
            type: 'person_job',
            personId: step.person,
            defaultPrompt: step.prompt || '',
            firstOnlyPrompt: step.first_prompt || '',
            contextCleaningRule: step.forget as any || 'upon_request',
            iterationCount: step.max_iterations || 1,
            mode: step.mode as any || 'sync',
            detectedVariables: this.detectVariables(step.prompt || '', step.first_prompt || '')
          } as PersonJobBlockData
        };

      case 'conditionNode':
        return {
          id: step.id,
          type: 'conditionNode',
          position,
          data: {
            ...baseData,
            type: 'condition',
            conditionType: step.condition_type as any || 'expression',
            expression: step.expression || '',
            maxIterations: step.max_iterations
          } as ConditionBlockData
        };

      case 'dbNode':
        return {
          id: step.id,
          type: 'dbNode',
          position,
          data: {
            ...baseData,
            type: 'db',
            subType: step.sub_type as any || 'fixed_prompt',
            sourceDetails: step.source || ''
          } as DBBlockData
        };

      case 'jobNode':
        return {
          id: step.id,
          type: 'jobNode',
          position,
          data: {
            ...baseData,
            type: 'job',
            subType: step.sub_type as any || 'code',
            sourceDetails: step.code || ''
          } as JobBlockData
        };

      case 'endpointNode':
        return {
          id: step.id,
          type: 'endpointNode',
          position,
          data: {
            ...baseData,
            type: 'endpoint',
            saveToFile: !!step.file,
            filePath: step.file || '',
            fileFormat: step.file_format as any || 'text'
          } as EndpointBlockData
        };

      default:
        return null;
    }
  }

  /**
   * Utility functions
   */
  private static toCleanId(label: string): string {
    return label
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_|_$/g, '')
      .substring(0, 30);
  }

  private static fromCleanId(id: string): string {
    return id
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  private static stepToNodeId(step: YamlDiagram['workflow'][0]): string {
    const typeMap: Record<string, string> = {
      'task': 'personjobNode',
      'condition': 'conditionNode',
      'data': 'dbNode',
      'process': 'jobNode',
      'save': 'endpointNode',
      'start': 'startNode'
    };

    const nodeType = typeMap[step.type] || 'personjobNode';
    return `${nodeType}-${nanoid(6)}`;
  }

  private static createArrow(
    source: string,
    target: string,
    branch?: 'true' | 'false'
  ): Edge<ArrowData> {
    const arrowId = `arrow-${nanoid(6)}`;
    return {
      id: arrowId,
      source,
      target,
      type: 'customArrow',
      data: {
        id: arrowId,
        sourceBlockId: source,
        targetBlockId: target,
        label: branch || 'flow',
        ...(branch && { branch })
      }
    };
  }

  private static extractLabelFromId(id: string): string {
    // Extract meaningful label from IDs like "PERSON_ABC123" -> "Person ABC123"
    return id.replace(/_/g, ' ').replace(/([A-Z]+)([A-Z][a-z])/g, '$1 $2');
  }

  private static detectVariables(...prompts: string[]): string[] {
    const vars = new Set<string>();
    const varPattern = /\{\{(\w+)\}\}/g;

    prompts.forEach(prompt => {
      if (prompt) {
        const matches = prompt.matchAll(varPattern);
        for (const match of matches) {
          vars.add(match[1]);
        }
      }
    });

    return Array.from(vars);
  }
}