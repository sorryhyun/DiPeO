import { logger } from '@/utils/logger';

// Legacy auto-save functionality - DEPRECATED
// Use AutoSaveManagerGraphQL for GraphQL-based auto-save
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function setupAutoSave(store: any): void {
  logger.warn('setupAutoSave is deprecated. Use AutoSaveManagerGraphQL for GraphQL-based auto-save.');
}

// Legacy load auto-saved data - DEPRECATED
export function loadAutoSavedDiagram(): any | null {
  logger.warn('loadAutoSavedDiagram is deprecated. Diagram persistence is handled by the backend.');
  return null;
}

// Clear auto-save data
export function clearAutoSave(): void {
  localStorage.removeItem('dipeo_autosave');
  localStorage.removeItem('dipeo_autosave_time');
  logger.debug('Cleared auto-save data');
}