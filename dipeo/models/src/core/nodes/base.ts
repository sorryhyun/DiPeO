/**
 * Base node data interface that all node types extend
 */

export interface BaseNodeData {
  label: string;
  flipped?: boolean;
  [key: string]: unknown;
}
