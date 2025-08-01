/**
 * Format a timestamp string for display in logs
 * @param timestamp ISO timestamp string
 * @returns Formatted time string (HH:MM:SS.mmm)
 */
export function formatTimestamp(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    const seconds = date.getSeconds().toString().padStart(2, '0');
    const milliseconds = date.getMilliseconds().toString().padStart(3, '0');
    
    return `${hours}:${minutes}:${seconds}.${milliseconds}`;
  } catch {
    return timestamp;
  }
}

/**
 * Format a date for display
 * @param date Date object or ISO string
 * @returns Formatted date string
 */
export function formatDate(date: Date | string): string {
  try {
    const d = typeof date === 'string' ? new Date(date) : date;
    return d.toLocaleDateString();
  } catch {
    return typeof date === 'string' ? date : 'Invalid Date';
  }
}

/**
 * Format a date and time for display
 * @param date Date object or ISO string
 * @returns Formatted date and time string
 */
export function formatDateTime(date: Date | string): string {
  try {
    const d = typeof date === 'string' ? new Date(date) : date;
    return d.toLocaleString();
  } catch {
    return typeof date === 'string' ? date : 'Invalid Date';
  }
}