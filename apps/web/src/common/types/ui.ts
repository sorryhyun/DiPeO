// UI types - State management and component interfaces

export interface UIState {
  selectedId: string | null;
  selectedType: 'node' | 'arrow' | 'person' | null;
  activeView: 'diagram' | 'memory' | 'execution' | 'conversation';
  isMonitorMode: boolean;
  isPropertyPanelOpen: boolean;
  contextMenu: {
    isOpen: boolean;
    position: { x: number; y: number };
    nodeId?: string;
  } | null;
}

export interface SelectionState {
  id: string;
  type: 'node' | 'arrow' | 'person';
}

export interface ModalState {
  apiKeys: boolean;
  interactivePrompt: boolean;
  fileImport: boolean;
}

export interface NotificationState {
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  duration?: number;
}

export interface CanvasState {
  zoom: number;
  center: { x: number; y: number };
  isDragging: boolean;
  isConnecting: boolean;
}

export interface PropertyPanelState {
  isOpen: boolean;
  isDirty: boolean;
  errors: Record<string, string>;
}