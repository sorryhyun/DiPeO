// apps/web/src/utils/sanitizer.ts
import { DiagramState, PersonDefinition } from '@/types';
import {roundPosition} from './layout';

export function sanitizeDiagram(diagram: DiagramState): DiagramState {
  return {
    ...diagram,
    // Sanitize nodes
    nodes: diagram.nodes.map(node => ({
      ...node,
      // Round position to 1 decimal place
      position: roundPosition(node.position),
      data: node.data
    })),

    // Sanitize arrows
    arrows: diagram.arrows.map(arrow => ({
      ...arrow,
      data: arrow.data ? {
        ...arrow.data,
        // Round control point offsets to 1 decimal place
        ...(arrow.data.controlPointOffsetX !== undefined && {
          controlPointOffsetX: Math.round(arrow.data.controlPointOffsetX * 10) / 10
        }),
        ...(arrow.data.controlPointOffsetY !== undefined && {
          controlPointOffsetY: Math.round(arrow.data.controlPointOffsetY * 10) / 10
        }),
        // Round loop radius to 1 decimal place
        ...(arrow.data.loopRadius !== undefined && {
          loopRadius: Math.round(arrow.data.loopRadius * 10) / 10
        })
      } : undefined
    })),

    // Sanitize persons - ensure all fields exist with default values
    persons: (diagram.persons || []).map(person => ({
      id: person.id,
      label: person.label || 'Unnamed Person',
      service: person.service || 'chatgpt', // Default service
      apiKeyId: person.apiKeyId || undefined,
      modelName: person.modelName || undefined,
      systemPrompt: person.systemPrompt || undefined
    } as PersonDefinition))
  };
}
