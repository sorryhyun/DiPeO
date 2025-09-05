/**
 * Validation and priority-related enumerations
 */

/**
 * Validation issue severity levels
 */
export enum Severity {
  ERROR = 'error',
  WARNING = 'warning',
  INFO = 'info'
}

/**
 * Event processing priority levels
 */
export enum EventPriority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  CRITICAL = 'critical'
}
