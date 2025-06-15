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
 * Calculate the average of an array of numbers
 * @param values Array of numbers
 * @returns Average value
 */
export function average(values: number[]): number {
  if (values.length === 0) return 0;
  return values.reduce((sum, val) => sum + val, 0) / values.length;
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