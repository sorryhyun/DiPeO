export type InteractionMode =
  | 'select'
  | 'pan'
  | 'connect'
  | 'add-node'
  | 'multi-select'
  | 'disabled';

export type ViewMode =
  | 'design'
  | 'execution'
  | 'debug'
  | 'preview';

export type ExecutionStatus =
  | 'idle'
  | 'running'
  | 'paused'
  | 'completed'
  | 'error'
  | 'aborted';

export interface ModeState {
  interaction: InteractionMode;
  view: ViewMode;
  execution: ExecutionStatus;
  readonly: boolean;
}

export interface ModeConstraints {
  canEdit: boolean;
  canExecute: boolean;
  canConnect: boolean;
  canDelete: boolean;
  canPan: boolean;
  canZoom: boolean;
  canSelect: boolean;
}

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

export function canEditInMode(mode: ModeState): boolean {
  return getModeConstraints(mode).canEdit;
}

export function canExecuteInMode(mode: ModeState): boolean {
  return getModeConstraints(mode).canExecute && mode.execution === 'idle';
}
