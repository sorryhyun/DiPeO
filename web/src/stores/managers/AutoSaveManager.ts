/**
 * Smart auto-save manager with structural change detection
 * Only saves when meaningful changes occur, not on every state update
 */

import { debounce } from 'lodash-es';
import { shallow } from 'zustand/shallow';
import type { UnifiedStore } from '../unifiedStore.types';
import { DomainNode, DomainArrow, NodeID, ArrowID } from '@/types';
import { useUnifiedStore } from '../unifiedStore';
// DEPRECATED: Use AutoSaveManagerGraphQL instead
// This REST-based version saves the entire diagram at once
// The GraphQL version uses granular mutations for better performance
import { api } from '@/utils/api';
import { logger } from '@/utils/logger';
import { toast } from 'react-hot-toast';

export interface AutoSaveOptions {
  debounceMs?: number;
  enabled?: boolean;
  onSave?: (success: boolean) => void;
  onError?: (error: Error) => void;
}

interface StructuralHash {
  nodeCount: number;
  arrowCount: number;
  nodeIds: string[];
  connections: string[];
  nodeTypes: Record<string, number>;
  checksum: string;
}

export class AutoSaveManager {
  private lastHash: string = '';
  private saveDebounce: ReturnType<typeof debounce>;
  private unsubscribe: (() => void) | null = null;
  private lastSaveTime: number = 0;
  private saveInProgress = false;
  private enabled: boolean;
  private currentDiagramId: string | null = null;

  constructor(
    private store: typeof useUnifiedStore,
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
  start(diagramId: string): void {
    if (!this.enabled) return;
    
    this.currentDiagramId = diagramId;
    this.lastHash = this.computeStructuralHash();
    
    // Subscribe to diagram changes
    this.unsubscribe = this.store.subscribe(
      state => ({ 
        nodes: state.nodes, 
        arrows: state.arrows,
        dataVersion: state.dataVersion 
      }),
      this.handleChange.bind(this),
      { equalityFn: shallow }
    );

    logger.debug('[AutoSave] Started monitoring diagram:', diagramId);
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
    if (this.hasStructuralChanges()) {
      this.performSave();
    }

    this.currentDiagramId = null;
    logger.debug('[AutoSave] Stopped monitoring');
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
    if (!this.enabled || this.saveInProgress) return;

    if (this.hasStructuralChanges()) {
      const hash = this.computeStructuralHash();
      this.lastHash = hash;
      this.saveDebounce();
    }
  }

  /**
   * Check if structural changes occurred
   */
  private hasStructuralChanges(): boolean {
    const currentHash = this.computeStructuralHash();
    return currentHash !== this.lastHash;
  }

  /**
   * Compute structural hash of the diagram
   * This captures meaningful changes while ignoring cosmetic ones
   */
  private computeStructuralHash(): string {
    const state = this.store.getState();
    
    const structural: StructuralHash = {
      nodeCount: state.nodes.size,
      arrowCount: state.arrows.size,
      nodeIds: Array.from(state.nodes.keys()).sort(),
      connections: Array.from(state.arrows.values())
        .map((arrow: DomainArrow) => `${arrow.source}->${arrow.target}`)
        .sort(),
      nodeTypes: this.getNodeTypeCounts(state.nodes),
      checksum: this.computeDataChecksum(state.nodes, state.arrows)
    };

    // Create stable hash from structural data
    return JSON.stringify(structural);
  }

  /**
   * Get count of each node type
   */
  private getNodeTypeCounts(nodes: Map<NodeID, DomainNode>): Record<string, number> {
    const counts: Record<string, number> = {};
    
    nodes.forEach(node => {
      counts[node.type] = (counts[node.type] || 0) + 1;
    });
    
    return counts;
  }

  /**
   * Compute checksum of node and arrow data
   * Focuses on significant data changes
   */
  private computeDataChecksum(
    nodes: Map<NodeID, DomainNode>,
    arrows: Map<ArrowID, DomainArrow>
  ): string {
    const significantData = {
      nodes: Array.from(nodes.values()).map(node => ({
        id: node.id,
        type: node.type,
        // Include significant data fields based on node type
        data: this.getSignificantNodeData(node)
      })),
      arrows: Array.from(arrows.values()).map(arrow => ({
        id: arrow.id,
        source: arrow.source,
        target: arrow.target
      }))
    };

    // Simple hash using JSON stringify
    // In production, use a proper hash function like SHA-256
    return this.simpleHash(JSON.stringify(significantData));
  }

  /**
   * Extract significant data from node based on type
   */
  private getSignificantNodeData(node: DomainNode): any {
    const data = node.data as any;
    
    switch (node.type) {
      case 'person_job':
        return {
          personId: data.personId,
          prompt: data.prompt,
          saveResponse: data.saveResponse
        };
      
      case 'condition':
        return {
          variable: data.variable,
          conditions: data.conditions
        };
      
      case 'db':
        return {
          operation: data.operation,
          collection: data.collection,
          data: data.data
        };
      
      case 'start':
        return {
          data: data.data
        };
      
      default:
        // For other types, include all data except UI-specific fields
        const { position, selected, dragging, ...significantData } = data;
        return significantData;
    }
  }

  /**
   * Simple hash function for demo purposes
   */
  private simpleHash(str: string): string {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return hash.toString(36);
  }

  /**
   * Perform the actual save
   */
  private async performSave(): Promise<boolean> {
    if (!this.currentDiagramId || this.saveInProgress) {
      return false;
    }

    const timeSinceLastSave = Date.now() - this.lastSaveTime;
    if (timeSinceLastSave < 1000) {
      // Prevent saves more frequent than once per second
      return false;
    }

    this.saveInProgress = true;

    try {
      const state = this.store.getState();
      
      // Prepare save data
      const diagram = {
        id: this.currentDiagramId,
        nodes: Object.fromEntries(state.nodes),
        arrows: Object.fromEntries(state.arrows),
        persons: Object.fromEntries(state.persons),
        metadata: {
          lastModified: new Date().toISOString(),
          autoSaved: true
        }
      };

      // Save to backend
      await api.diagrams.save({ 
        diagram, 
        filename: `diagram-${this.currentDiagramId}.json` 
      });
      
      this.lastSaveTime = Date.now();
      logger.debug('[AutoSave] Saved successfully');
      
      // Notify success
      if (this.options.onSave) {
        this.options.onSave(true);
      }

      return true;
    } catch (error) {
      logger.error('[AutoSave] Save failed:', error);
      
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
      hasUnsavedChanges: this.hasStructuralChanges(),
      saveInProgress: this.saveInProgress
    };
  }
}