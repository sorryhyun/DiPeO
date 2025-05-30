export function createHandleId(nodeId: string, type: string, name?: string): string {
  return name ? `${nodeId}-${type}-${name}` : `${nodeId}-${type}`;
}