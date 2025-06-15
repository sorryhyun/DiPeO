/**
 * GraphQL-based auto-save manager with incremental updates
 * Tracks individual changes and syncs them to the backend using GraphQL mutations
 */

import { debounce } from 'lodash-es';
import { shallow } from 'zustand/shallow';
import type { UnifiedStore } from '../unifiedStore.types';
import { 
  DomainNode, 
  DomainArrow, 
  DomainPerson, 
  NodeID, 
  ArrowID, 
  PersonID 
} from '@/types';
import { useUnifiedStore } from '../unifiedStore';
import { 
  CreateNodeDocument,
  UpdateNodeDocument,
  DeleteNodeDocument,
  CreateArrowDocument,
  DeleteArrowDocument,
  CreatePersonDocument,
  UpdatePersonDocument,
  DeletePersonDocument,
  type DiagramID,
  type CreateNodeMutation,
  type UpdateNodeMutation,
  type DeleteNodeMutation,
  type CreateArrowMutation,
  type DeleteArrowMutation,
  type CreatePersonMutation,
  type UpdatePersonMutation,
  type DeletePersonMutation,
  type CreateNodeMutationVariables,
  type UpdateNodeMutationVariables,
  type DeleteNodeMutationVariables,
  type CreateArrowMutationVariables,
  type DeleteArrowMutationVariables,
  type CreatePersonMutationVariables,
  type UpdatePersonMutationVariables,
  type DeletePersonMutationVariables
} from '@/__generated__/graphql';
import { logger } from '@/utils/logger';
import { toast } from 'react-hot-toast';
import { ApolloClient, NormalizedCacheObject } from '@apollo/client';

export interface AutoSaveOptions {
  debounceMs?: number;
  enabled?: boolean;
  onSave?: (success: boolean) => void;
  onError?: (error: Error) => void;
}

interface ChangeSet {
  nodes: {
    created: Map<NodeID, DomainNode>;
    updated: Map<NodeID, DomainNode>;
    deleted: Set<NodeID>;
  };
  arrows: {
    created: Map<ArrowID, DomainArrow>;
    deleted: Set<ArrowID>;
  };
  persons: {
    created: Map<PersonID, DomainPerson>;
    updated: Map<PersonID, DomainPerson>;
    deleted: Set<PersonID>;
  };
}

export class AutoSaveManagerGraphQL {
  private lastSnapshot: {
    nodes: Map<NodeID, DomainNode>;
    arrows: Map<ArrowID, DomainArrow>;
    persons: Map<PersonID, DomainPerson>;
  } | null = null;
  
  private pendingChanges: ChangeSet = {
    nodes: { created: new Map(), updated: new Map(), deleted: new Set() },
    arrows: { created: new Map(), deleted: new Set() },
    persons: { created: new Map(), updated: new Map(), deleted: new Set() }
  };
  
  private saveDebounce: ReturnType<typeof debounce>;
  private unsubscribe: (() => void) | null = null;
  private lastSaveTime: number = 0;
  private saveInProgress = false;
  private enabled: boolean;
  private currentDiagramId: DiagramID | null = null;

  constructor(
    private store: typeof useUnifiedStore,
    private apolloClient: ApolloClient<NormalizedCacheObject>,
    private options: AutoSaveOptions = {}
  ) {
    this.enabled = options.enabled ?? true;
    this.saveDebounce = debounce(
      this.performSave.bind(this),
      options.debounceMs ?? 2000
    );
  }

  /**
   * Start monitoring for changes
   */
  start(diagramId: DiagramID): void {
    if (!this.enabled) return;
    
    this.currentDiagramId = diagramId;
    
    // Take initial snapshot
    const state = this.store.getState();
    this.lastSnapshot = {
      nodes: new Map(state.nodes),
      arrows: new Map(state.arrows),
      persons: new Map(state.persons)
    };
    
    // Subscribe to diagram changes
    this.unsubscribe = this.store.subscribe(
      state => ({ 
        nodes: state.nodes, 
        arrows: state.arrows,
        persons: state.persons,
        dataVersion: state.dataVersion 
      }),
      this.handleChange.bind(this),
      { equalityFn: shallow }
    );

    logger.debug('[AutoSaveGraphQL] Started monitoring diagram:', diagramId);
  }

  /**
   * Stop monitoring
   */
  stop(): void {
    if (this.unsubscribe) {
      this.unsubscribe();
      this.unsubscribe = null;
    }
    
    // Cancel pending save
    this.saveDebounce.cancel();
    
    // Perform final save if needed
    if (this.hasPendingChanges()) {
      this.performSave();
    }

    this.currentDiagramId = null;
    this.lastSnapshot = null;
    logger.debug('[AutoSaveGraphQL] Stopped monitoring');
  }

  /**
   * Enable/disable auto-save
   */
  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
    if (!enabled) {
      this.saveDebounce.cancel();
    }
  }

  /**
   * Force immediate save
   */
  async saveNow(): Promise<boolean> {
    this.saveDebounce.cancel();
    return this.performSave();
  }

  /**
   * Handle state changes
   */
  private handleChange(): void {
    if (!this.enabled || this.saveInProgress || !this.lastSnapshot) return;

    const state = this.store.getState();
    const changes = this.detectChanges(state);
    
    if (this.hasChanges(changes)) {
      // Merge changes into pending
      this.mergeChanges(changes);
      this.saveDebounce();
    }
  }

  /**
   * Detect changes between current state and last snapshot
   */
  private detectChanges(state: ReturnType<typeof this.store.getState>): ChangeSet {
    const changes: ChangeSet = {
      nodes: { created: new Map(), updated: new Map(), deleted: new Set() },
      arrows: { created: new Map(), deleted: new Set() },
      persons: { created: new Map(), updated: new Map(), deleted: new Set() }
    };

    if (!this.lastSnapshot) return changes;

    // Detect node changes
    state.nodes.forEach((node, id) => {
      const lastNode = this.lastSnapshot!.nodes.get(id);
      if (!lastNode) {
        changes.nodes.created.set(id, node);
      } else if (JSON.stringify(node) !== JSON.stringify(lastNode)) {
        changes.nodes.updated.set(id, node);
      }
    });
    
    this.lastSnapshot.nodes.forEach((_, id) => {
      if (!state.nodes.has(id)) {
        changes.nodes.deleted.add(id);
      }
    });

    // Detect arrow changes (arrows can only be created or deleted)
    state.arrows.forEach((arrow, id) => {
      if (!this.lastSnapshot!.arrows.has(id)) {
        changes.arrows.created.set(id, arrow);
      }
    });
    
    this.lastSnapshot.arrows.forEach((_, id) => {
      if (!state.arrows.has(id)) {
        changes.arrows.deleted.add(id);
      }
    });

    // Detect person changes
    state.persons.forEach((person, id) => {
      const lastPerson = this.lastSnapshot!.persons.get(id);
      if (!lastPerson) {
        changes.persons.created.set(id, person);
      } else if (JSON.stringify(person) !== JSON.stringify(lastPerson)) {
        changes.persons.updated.set(id, person);
      }
    });
    
    this.lastSnapshot.persons.forEach((_, id) => {
      if (!state.persons.has(id)) {
        changes.persons.deleted.add(id);
      }
    });

    return changes;
  }

  /**
   * Check if there are any changes
   */
  private hasChanges(changes: ChangeSet): boolean {
    return (
      changes.nodes.created.size > 0 ||
      changes.nodes.updated.size > 0 ||
      changes.nodes.deleted.size > 0 ||
      changes.arrows.created.size > 0 ||
      changes.arrows.deleted.size > 0 ||
      changes.persons.created.size > 0 ||
      changes.persons.updated.size > 0 ||
      changes.persons.deleted.size > 0
    );
  }

  /**
   * Check if there are pending changes
   */
  private hasPendingChanges(): boolean {
    return this.hasChanges(this.pendingChanges);
  }

  /**
   * Merge new changes into pending changes
   */
  private mergeChanges(newChanges: ChangeSet): void {
    // Merge node changes
    newChanges.nodes.created.forEach((node, id) => {
      this.pendingChanges.nodes.created.set(id, node);
      this.pendingChanges.nodes.updated.delete(id); // If created, remove from updated
    });
    
    newChanges.nodes.updated.forEach((node, id) => {
      if (!this.pendingChanges.nodes.created.has(id)) {
        this.pendingChanges.nodes.updated.set(id, node);
      } else {
        // If node was created in pending, update the created version
        this.pendingChanges.nodes.created.set(id, node);
      }
    });
    
    newChanges.nodes.deleted.forEach(id => {
      if (this.pendingChanges.nodes.created.has(id)) {
        // If node was created and then deleted, just remove from created
        this.pendingChanges.nodes.created.delete(id);
      } else {
        this.pendingChanges.nodes.deleted.add(id);
        this.pendingChanges.nodes.updated.delete(id);
      }
    });

    // Merge arrow changes
    newChanges.arrows.created.forEach((arrow, id) => {
      this.pendingChanges.arrows.created.set(id, arrow);
    });
    
    newChanges.arrows.deleted.forEach(id => {
      if (this.pendingChanges.arrows.created.has(id)) {
        this.pendingChanges.arrows.created.delete(id);
      } else {
        this.pendingChanges.arrows.deleted.add(id);
      }
    });

    // Merge person changes
    newChanges.persons.created.forEach((person, id) => {
      this.pendingChanges.persons.created.set(id, person);
      this.pendingChanges.persons.updated.delete(id);
    });
    
    newChanges.persons.updated.forEach((person, id) => {
      if (!this.pendingChanges.persons.created.has(id)) {
        this.pendingChanges.persons.updated.set(id, person);
      } else {
        this.pendingChanges.persons.created.set(id, person);
      }
    });
    
    newChanges.persons.deleted.forEach(id => {
      if (this.pendingChanges.persons.created.has(id)) {
        this.pendingChanges.persons.created.delete(id);
      } else {
        this.pendingChanges.persons.deleted.add(id);
        this.pendingChanges.persons.updated.delete(id);
      }
    });
  }

  /**
   * Perform the actual save using GraphQL mutations
   */
  private async performSave(): Promise<boolean> {
    if (!this.currentDiagramId || this.saveInProgress || !this.hasPendingChanges()) {
      return false;
    }

    const timeSinceLastSave = Date.now() - this.lastSaveTime;
    if (timeSinceLastSave < 1000) {
      // Prevent saves more frequent than once per second
      return false;
    }

    this.saveInProgress = true;
    const changes = { ...this.pendingChanges };
    
    // Clear pending changes
    this.pendingChanges = {
      nodes: { created: new Map(), updated: new Map(), deleted: new Set() },
      arrows: { created: new Map(), deleted: new Set() },
      persons: { created: new Map(), updated: new Map(), deleted: new Set() }
    };

    try {
      const mutations: Promise<any>[] = [];

      // Delete operations first (to handle dependency order)
      changes.arrows.deleted.forEach(id => {
        mutations.push(
          this.apolloClient.mutate<DeleteArrowMutation, DeleteArrowMutationVariables>({
            mutation: DeleteArrowDocument,
            variables: { id }
          })
        );
      });

      changes.nodes.deleted.forEach(id => {
        mutations.push(
          this.apolloClient.mutate<DeleteNodeMutation, DeleteNodeMutationVariables>({
            mutation: DeleteNodeDocument,
            variables: { id }
          })
        );
      });

      changes.persons.deleted.forEach(id => {
        mutations.push(
          this.apolloClient.mutate<DeletePersonMutation, DeletePersonMutationVariables>({
            mutation: DeletePersonDocument,
            variables: { id }
          })
        );
      });

      // Create and update operations
      changes.persons.created.forEach(person => {
        mutations.push(
          this.apolloClient.mutate<CreatePersonMutation, CreatePersonMutationVariables>({
            mutation: CreatePersonDocument,
            variables: {
              diagramId: this.currentDiagramId!,
              input: {
                label: person.label,
                service: person.service,
                model: person.model,
                apiKeyId: person.apiKeyId,
                systemPrompt: person.systemPrompt,
                forgettingMode: person.forgettingMode
              }
            }
          })
        );
      });

      changes.persons.updated.forEach(person => {
        mutations.push(
          this.apolloClient.mutate<UpdatePersonMutation, UpdatePersonMutationVariables>({
            mutation: UpdatePersonDocument,
            variables: {
              input: {
                id: person.id,
                label: person.label,
                service: person.service,
                model: person.model,
                apiKeyId: person.apiKeyId,
                systemPrompt: person.systemPrompt,
                forgettingMode: person.forgettingMode
              }
            }
          })
        );
      });

      changes.nodes.created.forEach(node => {
        mutations.push(
          this.apolloClient.mutate<CreateNodeMutation, CreateNodeMutationVariables>({
            mutation: CreateNodeDocument,
            variables: {
              diagramId: this.currentDiagramId!,
              input: {
                type: node.type,
                displayName: node.displayName,
                position: node.position,
                data: node.data
              }
            }
          })
        );
      });

      changes.nodes.updated.forEach(node => {
        mutations.push(
          this.apolloClient.mutate<UpdateNodeMutation, UpdateNodeMutationVariables>({
            mutation: UpdateNodeDocument,
            variables: {
              input: {
                id: node.id,
                displayName: node.displayName,
                position: node.position,
                data: node.data
              }
            }
          })
        );
      });

      changes.arrows.created.forEach(arrow => {
        mutations.push(
          this.apolloClient.mutate<CreateArrowMutation, CreateArrowMutationVariables>({
            mutation: CreateArrowDocument,
            variables: {
              diagramId: this.currentDiagramId!,
              input: {
                source: arrow.source,
                target: arrow.target,
                data: arrow.data
              }
            }
          })
        );
      });

      // Execute all mutations
      await Promise.all(mutations);
      
      // Update snapshot after successful save
      const state = this.store.getState();
      this.lastSnapshot = {
        nodes: new Map(state.nodes),
        arrows: new Map(state.arrows),
        persons: new Map(state.persons)
      };
      
      this.lastSaveTime = Date.now();
      logger.debug('[AutoSaveGraphQL] Saved successfully', {
        nodes: {
          created: changes.nodes.created.size,
          updated: changes.nodes.updated.size,
          deleted: changes.nodes.deleted.size
        },
        arrows: {
          created: changes.arrows.created.size,
          deleted: changes.arrows.deleted.size
        },
        persons: {
          created: changes.persons.created.size,
          updated: changes.persons.updated.size,
          deleted: changes.persons.deleted.size
        }
      });
      
      // Notify success
      if (this.options.onSave) {
        this.options.onSave(true);
      }

      return true;
    } catch (error) {
      logger.error('[AutoSaveGraphQL] Save failed:', error);
      
      // Re-add failed changes back to pending
      this.mergeChanges(changes);
      
      // Notify error
      if (this.options.onError) {
        this.options.onError(error as Error);
      } else {
        toast.error('Auto-save failed. Your changes may not be saved.');
      }

      return false;
    } finally {
      this.saveInProgress = false;
    }
  }

  /**
   * Get auto-save status
   */
  getStatus(): {
    enabled: boolean;
    lastSaveTime: number;
    hasUnsavedChanges: boolean;
    saveInProgress: boolean;
  } {
    return {
      enabled: this.enabled,
      lastSaveTime: this.lastSaveTime,
      hasUnsavedChanges: this.hasPendingChanges(),
      saveInProgress: this.saveInProgress
    };
  }
}