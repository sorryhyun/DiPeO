/**
 * Check if two numbers are equal within a tolerance
 * @param a First number
 * @param b Second number
 * @param tolerance Tolerance value (default: 0.01)
 * @returns True if numbers are within tolerance
 */
export function isWithinTolerance(a: number, b: number, tolerance: number = 0.01): boolean {
  return Math.abs(a - b) < tolerance;
}

/**
 * Snap a value to a grid
 * @param value Value to snap
 * @param gridSize Grid size (default: 10)
 * @returns Snapped value
 */
export function snapToGrid(value: number, gridSize: number = 10): number {
  return Math.round(value / gridSize) * gridSize;
}

/**
 * Clamp a value between min and max
 * @param value Value to clamp
 * @param min Minimum value
 * @param max Maximum value
 * @returns Clamped value
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

/**
 * Linear interpolation between two values
 * @param start Start value
 * @param end End value
 * @param t Interpolation factor (0 to 1)
 * @returns Interpolated value
 */
export function lerp(start: number, end: number, t: number): number {
  return start + (end - start) * t;
}

/**
 * Map a value from one range to another
 * @param value Input value
 * @param inMin Input range minimum
 * @param inMax Input range maximum
 * @param outMin Output range minimum
 * @param outMax Output range maximum
 * @returns Mapped value
 */
export function mapRange(
  value: number,
  inMin: number,
  inMax: number,
  outMin: number,
  outMax: number
): number {
  return ((value - inMin) * (outMax - outMin)) / (inMax - inMin) + outMin;
}

/**
 * Round a number to a specific number of decimal places
 * @param value Number to round
 * @param decimals Number of decimal places (default: 2)
 * @returns Rounded number
 */
export function roundTo(value: number, decimals: number = 2): number {
  const factor = Math.pow(10, decimals);
  return Math.round(value * factor) / factor;
}

/**
 * Generate a random number between min and max
 * @param min Minimum value
 * @param max Maximum value
 * @returns Random number
 */
export function randomRange(min: number, max: number): number {
  return Math.random() * (max - min) + min;
}

/**
 * Calculate the average of an array of numbers
 * @param values Array of numbers
 * @returns Average value
 */
export function average(values: number[]): number {
  if (values.length === 0) return 0;
  return values.reduce((sum, val) => sum + val, 0) / values.length;
}

/**
 * Calculate standard deviation of an array of numbers
 * @param values Array of numbers
 * @returns Standard deviation
 */
export function standardDeviation(values: number[]): number {
  if (values.length === 0) return 0;
  
  const avg = average(values);
  const squaredDiffs = values.map(val => Math.pow(val - avg, 2));
  const avgSquaredDiff = average(squaredDiffs);
  
  return Math.sqrt(avgSquaredDiff);
}

/**
 * Get the sign of a number (-1, 0, or 1)
 * @param value Number to check
 * @returns Sign of the number
 */
export function sign(value: number): number {
  if (value > 0) return 1;
  if (value < 0) return -1;
  return 0;
}

/**
 * Debounce a function to limit how often it can be called
 * @param func Function to debounce
 * @param delay Delay in milliseconds
 * @returns Debounced function
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout>;
  
  return function debounced(...args: Parameters<T>) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
}

/**
 * Throttle a function to limit how often it can be called
 * @param func Function to throttle
 * @param limit Time limit in milliseconds
 * @returns Throttled function
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle = false;
  
  return function throttled(...args: Parameters<T>) {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => {
        inThrottle = false;
      }, limit);
    }
  };
}