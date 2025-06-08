export type Direction = 'input' | 'output';

// Migration helper to convert old terminology
export function normalizeDirection(kind: 'source' | 'target' | 'input' | 'output'): Direction {
  switch (kind) {
    case 'source':
    case 'output':
      return 'output';
    case 'target':
    case 'input':
      return 'input';
  }
}

// Helper to convert direction back to ReactFlow 'kind' if needed
export function directionToKind(direction: Direction): 'source' | 'target' {
  return direction === 'output' ? 'source' : 'target';
}

// Type guard
export function isDirection(value: string): value is Direction {
  return value === 'input' || value === 'output';
}