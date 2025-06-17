import type { Vec2 } from '@/core/types';

/**
 * Calculate a point on a quadratic bezier curve
 * @param start Start point
 * @param control Control point
 * @param end End point
 * @param t Parameter value (0 to 1)
 * @returns Point on the curve
 */
export function getQuadraticPoint(
  start: Vec2,
  control: Vec2,
  end: Vec2,
  t: number
): Vec2 {
  const x = (1 - t) * (1 - t) * start.x + 2 * (1 - t) * t * control.x + t * t * end.x;
  const y = (1 - t) * (1 - t) * start.y + 2 * (1 - t) * t * control.y + t * t * end.y;
  return { x, y };
}

/**
 * Calculate the distance between two points
 * @param a First point
 * @param b Second point
 * @returns Euclidean distance
 */
export function getDistance(a: Vec2, b: Vec2): number {
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  return Math.sqrt(dx * dx + dy * dy);
}

/**
 * Calculate the angle between two points in radians
 * @param from Start point
 * @param to End point
 * @returns Angle in radians
 */
export function getAngle(from: Vec2, to: Vec2): number {
  return Math.atan2(to.y - from.y, to.x - from.x);
}

/**
 * Calculate the midpoint between two points
 * @param a First point
 * @param b Second point
 * @returns Midpoint
 */
export function getMidpoint(a: Vec2, b: Vec2): Vec2 {
  return {
    x: (a.x + b.x) / 2,
    y: (a.y + b.y) / 2
  };
}

/**
 * Calculate a control point for a smooth curve between two points
 * @param start Start point
 * @param end End point
 * @param curvature Amount of curve (0 to 1)
 * @returns Control point for quadratic bezier
 */
export function getControlPoint(start: Vec2, end: Vec2, curvature: number = 0.5): Vec2 {
  const mid = getMidpoint(start, end);
  const distance = getDistance(start, end);
  const angle = getAngle(start, end);
  
  // Perpendicular angle
  const perpAngle = angle + Math.PI / 2;
  
  // Offset from midpoint
  const offset = distance * curvature * 0.5;
  
  return {
    x: mid.x + Math.cos(perpAngle) * offset,
    y: mid.y + Math.sin(perpAngle) * offset
  };
}

/**
 * Check if a point is within a rectangle
 * @param point Point to check
 * @param rect Rectangle bounds
 * @returns True if point is inside rectangle
 */
export function isPointInRect(
  point: Vec2,
  rect: { x: number; y: number; width: number; height: number }
): boolean {
  return (
    point.x >= rect.x &&
    point.x <= rect.x + rect.width &&
    point.y >= rect.y &&
    point.y <= rect.y + rect.height
  );
}

/**
 * Clamp a point to stay within bounds
 * @param point Point to clamp
 * @param bounds Bounding rectangle
 * @returns Clamped point
 */
export function clampPoint(
  point: Vec2,
  bounds: { minX: number; minY: number; maxX: number; maxY: number }
): Vec2 {
  return {
    x: Math.max(bounds.minX, Math.min(bounds.maxX, point.x)),
    y: Math.max(bounds.minY, Math.min(bounds.maxY, point.y))
  };
}