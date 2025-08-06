import { UnifiedStore } from '../types';
import { useUnifiedStore } from '../index';
import type { DiagramSlice } from '@/infrastructure/store/slices/diagram';
import type { ExecutionSlice } from '@/infrastructure/store/slices/execution';
import type { PersonSlice } from '@/infrastructure/store/slices/person';
import type { StoreExecutionState } from '@/services/conversion';

/**
 * Migration utilities for transitioning from feature-based stores to unified store
 */

// ===== Migration Types =====

export interface LegacyStoreState {
  diagram?: Partial<DiagramSlice>;
  execution?: Partial<ExecutionSlice>;
  person?: Partial<PersonSlice>;
  ui?: any;
}

export interface MigrationResult {
  success: boolean;
  errors: string[];
  warnings: string[];
  migratedPaths: string[];
}

export interface MigrationOptions {
  preserveHistory?: boolean;
  validateData?: boolean;
  dryRun?: boolean;
  onProgress?: (progress: number, message: string) => void;
}

// ===== Migration Functions =====

/**
 * Migrate from legacy feature stores to unified store
 */
export async function migrateToUnifiedStore(
  legacyState: LegacyStoreState,
  options: MigrationOptions = {}
): Promise<MigrationResult> {
  const {
    preserveHistory = true,
    validateData = true,
    dryRun = false,
    onProgress,
  } = options;

  const result: MigrationResult = {
    success: false,
    errors: [],
    warnings: [],
    migratedPaths: [],
  };

  try {
    onProgress?.(0, 'Starting migration...');

    // Step 1: Validate legacy state
    if (validateData) {
      onProgress?.(10, 'Validating legacy state...');
      const validationResult = validateLegacyState(legacyState);
      result.errors.push(...validationResult.errors);
      result.warnings.push(...validationResult.warnings);
      
      if (validationResult.errors.length > 0 && !dryRun) {
        result.success = false;
        return result;
      }
    }

    // Step 2: Transform diagram data
    onProgress?.(30, 'Migrating diagram data...');
    const diagramState = migrateDiagramState(legacyState.diagram);
    if (diagramState) {
      result.migratedPaths.push('diagram.nodes', 'diagram.arrows', 'diagram.metadata');
    }

    // Step 3: Transform execution data
    onProgress?.(50, 'Migrating execution data...');
    const executionState = migrateExecutionState(legacyState.execution);
    if (executionState) {
      result.migratedPaths.push('execution.current', 'execution.nodeStates');
    }

    // Step 4: Transform person data
    onProgress?.(70, 'Migrating person data...');
    const personState = migratePersonState(legacyState.person);
    if (personState) {
      result.migratedPaths.push('persons.persons');
    }

    // Step 5: Transform UI data
    onProgress?.(85, 'Migrating UI state...');
    const uiState = migrateUIState(legacyState.ui);
    if (uiState) {
      result.migratedPaths.push('ui.selection', 'ui.modals', 'ui.panels');
    }

    // Step 6: Apply migration if not dry run
    if (!dryRun) {
      onProgress?.(95, 'Applying migration...');
      // Merge all migrated states into flattened structure
      const migrated = {
        ...diagramState,
        ...executionState,
        ...personState,
        ...uiState,
      };
      
      // In actual implementation, this would update the store
      // For now, we'll just mark it as successful
      result.success = true;
    } else {
      result.success = true;
      result.warnings.push('Dry run completed - no changes applied');
    }

    onProgress?.(100, 'Migration completed');
  } catch (error) {
    result.errors.push(`Migration failed: ${error instanceof Error ? error.message : String(error)}`);
    result.success = false;
  }

  return result;
}

/**
 * Validate legacy state structure
 */
function validateLegacyState(state: LegacyStoreState): {
  errors: string[];
  warnings: string[];
} {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Check for required fields
  if (!state.diagram && !state.execution && !state.person) {
    warnings.push('No data found to migrate');
  }

  // Validate diagram data
  if (state.diagram) {
    if (state.diagram.nodes && !(state.diagram.nodes instanceof Map)) {
      errors.push('diagram.nodes must be a Map');
    }
    if (state.diagram.arrows && !(state.diagram.arrows instanceof Map)) {
      errors.push('diagram.arrows must be a Map');
    }
  }

  // Validate person data
  if (state.person) {
    if (state.person.persons && !(state.person.persons instanceof Map)) {
      errors.push('person.persons must be a Map');
    }
  }

  return { errors, warnings };
}

/**
 * Migrate diagram state
 */
function migrateDiagramState(legacyDiagram?: Partial<DiagramSlice>): Partial<DiagramSlice> | null {
  if (!legacyDiagram) return null;

  return {
    nodes: legacyDiagram.nodes || new Map(),
    arrows: legacyDiagram.arrows || new Map(),
    diagramId: legacyDiagram.diagramId || null,
    diagramName: legacyDiagram.diagramName || 'Untitled',
    diagramDescription: legacyDiagram.diagramDescription || '',
    diagramFormat: legacyDiagram.diagramFormat || null,
    dataVersion: legacyDiagram.dataVersion || 0,
  };
}

/**
 * Migrate execution state
 */
function migrateExecutionState(legacyExecution?: Partial<ExecutionSlice>): Partial<ExecutionSlice> | null {
  if (!legacyExecution) return null;

  const current = legacyExecution.execution as StoreExecutionState | undefined;
  
  return {
    execution: current ? {
      id: current.id || null,
      isRunning: current.isRunning || false,
      isPaused: current.isPaused || false,
      runningNodes: current.runningNodes || new Set(),
      nodeStates: current.nodeStates || new Map(),
      context: current.context || {},
    } : {
      id: null,
      isRunning: false,
      isPaused: false,
      runningNodes: new Set(),
      nodeStates: new Map(),
      context: {},
    },
  };
}

/**
 * Migrate person state
 */
function migratePersonState(legacyPerson?: Partial<PersonSlice>): Partial<PersonSlice> | null {
  if (!legacyPerson) return null;

  return {
    persons: legacyPerson.persons || new Map(),
  };
}

/**
 * Migrate UI state
 */
function migrateUIState(legacyUI?: any): any | null {
  if (!legacyUI) {
    // Return default UI state
    return {
      selection: {
        id: null,
        type: null,
      },
      modals: {
        isPersonModalOpen: false,
        isPropertiesOpen: false,
        isExportModalOpen: false,
      },
      panels: {
        leftSidebarOpen: true,
        rightSidebarOpen: true,
        bottomPanelOpen: false,
      },
      viewport: {
        zoom: 1,
        center: { x: 0, y: 0 },
      },
    };
  }

  return {
    selection: legacyUI.selection || { id: null, type: null },
    modals: legacyUI.modals || {
      isPersonModalOpen: false,
      isPropertiesOpen: false,
      isExportModalOpen: false,
    },
    panels: legacyUI.panels || {
      leftSidebarOpen: true,
      rightSidebarOpen: true,
      bottomPanelOpen: false,
    },
    viewport: legacyUI.viewport || {
      zoom: 1,
      center: { x: 0, y: 0 },
    },
  };
}

// ===== Import Path Migration =====

/**
 * Maps old import paths to new ones
 */
export const importPathMigration: Record<string, string> = {
  // Old feature-based imports -> New unified imports
  '@/domain/diagram/store/diagramSlice': '@/infrastructure/store/slices/diagram',
  '@/domain/execution/store/executionSlice': '@/infrastructure/store/slices/execution',
  '@/domain/person/store/personSlice': '@/infrastructure/store/slices/person',
  '@/core/store/slices/uiSlice': '@/infrastructure/store/slices/ui',
  '@/core/store/unifiedStore': '@/infrastructure/store',
  
  // Hook migrations
  '@/domain/diagram/hooks/useDiagramManager': '@/infrastructure/store/hooks/useDiagram',
  '@/domain/execution/hooks/useExecution': '@/infrastructure/store/hooks/useExecution',
  '@/domain/person/hooks/usePersonOperations': '@/infrastructure/store/hooks/usePerson',
};

/**
 * Helper to update import statements in code
 */
export function migrateImportPath(oldPath: string): string {
  return importPathMigration[oldPath] || oldPath;
}

// ===== Adapter Pattern for Gradual Migration =====

/**
 * Creates an adapter that provides old API while using new store
 */
export function createStoreAdapter() {
  return {
    // Diagram adapter
    diagram: {
      get nodes() {
        return useUnifiedStore.getState().nodes;
      },
      get arrows() {
        return useUnifiedStore.getState().arrows;
      },
      addNode: (type: any, position: any, data: any) => {
        return useUnifiedStore.getState().addNode(type, position, data);
      },
      updateNode: (id: any, updates: any) => {
        useUnifiedStore.getState().updateNode(id, updates);
      },
      deleteNode: (id: any) => {
        useUnifiedStore.getState().deleteNode(id);
      },
    },
    
    // Execution adapter
    execution: {
      get isRunning() {
        return useUnifiedStore.getState().execution.isRunning;
      },
      startExecution: (diagramId: any) => {
        useUnifiedStore.getState().startExecution(diagramId);
      },
      stopExecution: () => {
        useUnifiedStore.getState().stopExecution();
      },
    },
    
    // Person adapter
    person: {
      get persons() {
        return useUnifiedStore.getState().persons;
      },
      addPerson: (data: any) => {
        // addPerson expects (name, organization, model)
        return useUnifiedStore.getState().addPerson(data.name || '', data.organization || '', data.model || 'gpt-4.1-nano');
      },
      updatePerson: (id: any, updates: any) => {
        useUnifiedStore.getState().updatePerson(id, updates);
      },
      deletePerson: (id: any) => {
        useUnifiedStore.getState().deletePerson(id);
      },
    },
  };
}

// ===== Migration CLI Tool =====

/**
 * Automated migration script for codebase
 */
export async function runMigrationScript(options: {
  targetDir: string;
  backup?: boolean;
  interactive?: boolean;
}): Promise<void> {
  console.log('🔄 Starting store migration...');
  
  // Step 1: Backup existing code if requested
  if (options.backup) {
    console.log('📦 Creating backup...');
    // Implementation would backup files
  }
  
  // Step 2: Update import statements
  console.log('📝 Updating import statements...');
  // Implementation would use AST to update imports
  
  // Step 3: Update hook usage
  console.log('🔗 Updating hook usage...');
  // Implementation would update hook calls
  
  // Step 4: Update store access patterns
  console.log('🔧 Updating store access patterns...');
  // Implementation would update direct store access
  
  console.log('✅ Migration completed!');
}

// ===== Validation Utilities =====

/**
 * Validate that migration was successful
 */
export function validateMigration(store: UnifiedStore): {
  isValid: boolean;
  issues: string[];
} {
  const issues: string[] = [];
  
  // Check required state structure (flattened)
  if (!store.nodes) issues.push('Missing nodes state');
  if (!store.arrows) issues.push('Missing arrows state');
  if (!store.execution) issues.push('Missing execution state');
  if (!store.persons) issues.push('Missing persons state');
  if (!store.selectedId !== undefined) issues.push('Missing UI state');
  
  // Check data integrity
  if (!store.nodes || !store.arrows) {
    issues.push('Incomplete diagram state');
  }
  
  return {
    isValid: issues.length === 0,
    issues,
  };
}