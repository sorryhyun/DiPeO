// Arrow-related types
import { Edge, OnEdgesChange, EdgeChange, Connection,
  applyEdgeChanges as applyEdgeChangesRF,
  addEdge as addEdgeRF
} from '@xyflow/react';

export type ArrowKind = 'normal' | 'fixed';

export enum ContentType {
  VARIABLE = 'variable',
  RAW_TEXT = 'raw_text',
  CONVERSATION_STATE = 'conversation_state'
}

export interface ArrowData {
  id: string;
  sourceBlockId: string;
  targetBlockId: string;
  sourceHandleId?: string;
  targetHandleId?: string;
  label?: string;
  contentType?: 'raw_text' | 'variable_in_object' | 'conversation_state' | 'empty' | 'generic';
  arrowKind?: ArrowKind;
  variableName?: string;
  objectKeyPath?: string;
  loopRadius?: number;
  branch?: 'true' | 'false';
  controlPointOffsetX?: number;
  controlPointOffsetY?: number;
  kind?: 'ALL' | 'SINGLE';
  template?: string;
  conversationState?: boolean;
  inheritedContentType?: boolean; // Indicates if content type is inherited from input arrows
  [key: string]: unknown; // For React Flow compatibility
}

export type Arrow<T extends Record<string, unknown> = ArrowData> = Edge<T>;
export type ArrowChange = EdgeChange;
export type OnArrowsChange = OnEdgesChange;

// React Flow Helper Functions
export function applyArrowChanges(
  changes: EdgeChange[],
  arrows: Arrow<ArrowData>[]
): Arrow<ArrowData>[] {
  return applyEdgeChangesRF(changes, arrows) as Arrow<ArrowData>[];
}

export function addArrow(
  arrow: Edge<ArrowData> | Connection,
  arrows: Edge<ArrowData>[]
): Edge<ArrowData>[] {
  return addEdgeRF(arrow, arrows);
}