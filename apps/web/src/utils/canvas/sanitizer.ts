// apps/web/src/utils/canvas/sanitizer.ts
import { DomainDiagram, DomainPerson, DomainNode, DomainArrow } from '@/types/domain';
import { NodeID, ArrowID, PersonID } from '@/types/branded';
import { roundPosition } from './layout';

export function sanitizeDiagram(diagram: DomainDiagram): DomainDiagram {
  // Sanitize nodes
  const sanitizedNodes: Record<NodeID, DomainNode> = {};
  for (const [nodeId, node] of Object.entries(diagram.nodes)) {
    sanitizedNodes[nodeId as NodeID] = {
      ...node,
      // Round position to 1 decimal place
      position: roundPosition(node.position),
      data: node.data
    };
  }

  // Sanitize arrows
  const sanitizedArrows: Record<ArrowID, DomainArrow> = {};
  for (const [arrowId, arrow] of Object.entries(diagram.arrows)) {
    const arrowData = arrow.data as any;
    sanitizedArrows[arrowId as ArrowID] = {
      ...arrow,
      data: arrowData ? {
        ...arrowData,
        // Round control point offsets to 1 decimal place
        ...(arrowData.controlPointOffsetX !== undefined && {
          controlPointOffsetX: Math.round(arrowData.controlPointOffsetX * 10) / 10
        }),
        ...(arrowData.controlPointOffsetY !== undefined && {
          controlPointOffsetY: Math.round(arrowData.controlPointOffsetY * 10) / 10
        }),
        // Round loop radius to 1 decimal place
        ...(arrowData.loopRadius !== undefined && {
          loopRadius: Math.round(arrowData.loopRadius * 10) / 10
        })
      } : undefined
    };
  }

  // Sanitize persons - ensure all fields exist with default values
  const sanitizedPersons: Record<PersonID, DomainPerson> = {};
  for (const [personId, person] of Object.entries(diagram.persons || {})) {
    sanitizedPersons[personId as PersonID] = {
      id: person.id,
      label: person.label || 'Unnamed Person',
      model: person.model || 'gpt-4.1-nano',
      service: person.service || 'openai',
      systemPrompt: person.systemPrompt,
      temperature: person.temperature,
      maxTokens: person.maxTokens,
      topP: person.topP,
      frequencyPenalty: person.frequencyPenalty,
      presencePenalty: person.presencePenalty,
      forgettingMode: person.forgettingMode
    };
  }

  return {
    ...diagram,
    nodes: sanitizedNodes,
    arrows: sanitizedArrows,
    persons: sanitizedPersons
  };
}
