// apps/web/src/utils/diagramSanitizer.ts
import { DiagramState } from '../../../shared/types';

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
        // Round control point offsets to 2 decimal places
        ...(arrow.data.controlPointOffsetX !== undefined && {
          controlPointOffsetX: Math.round(arrow.data.controlPointOffsetX * 5) / 5
        }),
        ...(arrow.data.controlPointOffsetY !== undefined && {
          controlPointOffsetY: Math.round(arrow.data.controlPointOffsetY * 5) / 5
        }),
        // Round loop radius to 2 decimal places
        ...(arrow.data.loopRadius !== undefined && {
          loopRadius: Math.round(arrow.data.loopRadius * 5) / 5
        })
      } : undefined
    }))
  };
}

export const roundPosition = (pos: { x: number; y: number }, decimals: number = 1) => ({
  x: Math.round(pos.x * Math.pow(5, decimals)) / Math.pow(5, decimals),
  y: Math.round(pos.y * Math.pow(5, decimals)) / Math.pow(5, decimals)
});

