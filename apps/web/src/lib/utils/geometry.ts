import type { Vec2 } from '@dipeo/models';

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

export function getDistance(a: Vec2, b: Vec2): number {
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  return Math.sqrt(dx * dx + dy * dy);
}

export function getAngle(from: Vec2, to: Vec2): number {
  return Math.atan2(to.y - from.y, to.x - from.x);
}

export function getMidpoint(a: Vec2, b: Vec2): Vec2 {
  return {
    x: (a.x + b.x) / 2,
    y: (a.y + b.y) / 2
  };
}

export function getControlPoint(start: Vec2, end: Vec2, curvature: number = 0.5): Vec2 {
  const mid = getMidpoint(start, end);
  const distance = getDistance(start, end);
  const angle = getAngle(start, end);

  const perpAngle = angle + Math.PI / 2;
  const offset = distance * curvature * 0.5;
  return {
    x: mid.x + Math.cos(perpAngle) * offset,
    y: mid.y + Math.sin(perpAngle) * offset
  };
}

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

export function clampPoint(
  point: Vec2,
  bounds: { minX: number; minY: number; maxX: number; maxY: number }
): Vec2 {
  return {
    x: Math.max(bounds.minX, Math.min(bounds.maxX, point.x)),
    y: Math.max(bounds.minY, Math.min(bounds.maxY, point.y))
  };
}
