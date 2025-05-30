import { Node, Edge } from '@xyflow/react';

/**
 * Canvas and layout utility functions
 */

export const calculateNodeBounds = (nodes: Node[]) => {
  if (nodes.length === 0) {
    return { minX: 0, minY: 0, maxX: 0, maxY: 0, width: 0, height: 0 };
  }

  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;

  nodes.forEach(node => {
    const x = node.position?.x || 0;
    const y = node.position?.y || 0;
    const width = node.width || 200;
    const height = node.height || 100;

    minX = Math.min(minX, x);
    minY = Math.min(minY, y);
    maxX = Math.max(maxX, x + width);
    maxY = Math.max(maxY, y + height);
  });

  return {
    minX,
    minY,
    maxX,
    maxY,
    width: maxX - minX,
    height: maxY - minY,
  };
};

export const centerViewport = (nodes: Node[]) => {
  const bounds = calculateNodeBounds(nodes);
  const centerX = bounds.minX + bounds.width / 2;
  const centerY = bounds.minY + bounds.height / 2;

  return { x: centerX, y: centerY, zoom: 1 };
};

export const fitNodesToView = (nodes: Node[], viewportWidth: number, viewportHeight: number) => {
  const bounds = calculateNodeBounds(nodes);
  const padding = 50;
  
  const scaleX = (viewportWidth - padding * 2) / bounds.width;
  const scaleY = (viewportHeight - padding * 2) / bounds.height;
  const scale = Math.min(scaleX, scaleY, 1); // Don't zoom in beyond 100%

  const centerX = bounds.minX + bounds.width / 2;
  const centerY = bounds.minY + bounds.height / 2;

  return {
    x: centerX,
    y: centerY,
    zoom: scale,
  };
};

export const getOptimalNodePosition = (existingNodes: Node[], preferredX = 100, preferredY = 100) => {
  const gridSize = 20;
  const nodeSpacing = 300;

  // Simple grid-based placement
  const occupiedPositions = new Set(
    existingNodes.map(node => 
      `${Math.round((node.position?.x || 0) / gridSize)},${Math.round((node.position?.y || 0) / gridSize)}`
    )
  );

  let x = Math.round(preferredX / gridSize) * gridSize;
  let y = Math.round(preferredY / gridSize) * gridSize;

  while (occupiedPositions.has(`${x / gridSize},${y / gridSize}`)) {
    x += nodeSpacing;
    if (x > 2000) {
      x = preferredX;
      y += nodeSpacing;
    }
  }

  return { x, y };
};