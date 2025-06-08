/**
 * Canvas interaction modes
 */
export type InteractionMode = 
  | 'select'      // Default mode for selecting nodes/arrows
  | 'pan'         // Pan the canvas
  | 'connect'     // Creating connections between nodes
  | 'add-node'    // Adding new nodes
  | 'multi-select' // Box selection mode
  | 'disabled';   // Read-only mode

/**
 * Application view modes
 */
export type ViewMode = 
  | 'design'      // Design/edit diagram
  | 'execution'   // Monitor execution
  | 'debug'       // Debug mode with extra info
  | 'preview';    // Preview mode (read-only)

/**
 * Execution states
 */
export type ExecutionState = 
  | 'idle'
  | 'running'
  | 'paused'
  | 'completed'
  | 'error'
  | 'aborted';

/**
 * Mode configuration
 */
export interface ModeState {
  interaction: InteractionMode;
  view: ViewMode;
  execution: ExecutionState;
  readonly: boolean;
}

/**
 * Mode constraints
 */
export interface ModeConstraints {
  canEdit: boolean;
  canExecute: boolean;
  canConnect: boolean;
  canDelete: boolean;
  canPan: boolean;
  canZoom: boolean;
  canSelect: boolean;
}

/**
 * Get constraints for current mode
 */
export function getModeConstraints(mode: ModeState): ModeConstraints {
  if (mode.readonly || mode.view === 'preview') {
    return {
      canEdit: false,
      canExecute: false,
      canConnect: false,
      canDelete: false,
      canPan: true,
      canZoom: true,
      canSelect: false
    };
  }

  if (mode.view === 'execution') {
    return {
      canEdit: false,
      canExecute: true,
      canConnect: false,
      canDelete: false,
      canPan: true,
      canZoom: true,
      canSelect: true
    };
  }

  if (mode.view === 'design') {
    return {
      canEdit: true,
      canExecute: true,
      canConnect: true,
      canDelete: true,
      canPan: true,
      canZoom: true,
      canSelect: true
    };
  }

  // Debug mode
  return {
    canEdit: true,
    canExecute: true,
    canConnect: true,
    canDelete: true,
    canPan: true,
    canZoom: true,
    canSelect: true
  };
}

/**
 * Check if mode allows editing
 */
export function canEditInMode(mode: ModeState): boolean {
  return getModeConstraints(mode).canEdit;
}

/**
 * Check if mode allows execution
 */
export function canExecuteInMode(mode: ModeState): boolean {
  return getModeConstraints(mode).canExecute && mode.execution === 'idle';
}