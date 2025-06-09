/**
 * Geometry-related primitive types
 */

/**
 * 2D vector/point representation
 */
export interface Vec2 { 
  x: number; 
  y: number;
}

/**
 * Rectangle bounds
 */
export interface Rect {
  x: number;
  y: number;
  width: number;
  height: number;
}

/**
 * Size dimensions
 */
export interface Size {
  width: number;
  height: number;
}

/**
 * Position with optional z-index
 */
export interface Position extends Vec2 {
  z?: number;
}