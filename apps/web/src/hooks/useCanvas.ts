import { shallow } from 'zustand/shallow';
import type { NodeChange, EdgeChange, Connection } from '@xyflow/react';
import { useUnifiedStore } from '@/stores/useUnifiedStore';
import { nodeToReact } from '@/types/framework/adapters';
import type { NodeID, ArrowID, HandleID, PersonID } from '@/types/branded';
import type { NodeKind } from '@/types/primitives/enums';
import type { Vec2 } from '@/types/primitives/geometry';
import type { LLMService } from '@/types';

/**
 * Consolidated canvas hook that combines node, arrow, and person operations
 * with performance optimizations and React Flow integration
 */
export const useCanvas = () => {
  return useUnifiedStore(
    state => {
      // Convert domain nodes to React Flow format with handles
      const domainNodes = Array.from(state.nodes.values());
      const nodes = domainNodes.map(node => {
        const nodeHandles = Array.from(state.handles.values()).filter(h => h.nodeId === node.id);
        return nodeToReact(node, nodeHandles);
      });
      
      const arrows = Array.from(state.arrows.values());
      const persons = Array.from(state.persons.values());
      
      return {
        // State
        nodes,
        arrows,
        persons,
        handles: state.handles,
        isMonitorMode: state.readOnly,
        
        // Node operations
        addNode: (type: string, position: Vec2, data?: Record<string, unknown>) => 
          state.addNode(type as NodeKind, position, data),
        updateNode: state.updateNode,
        deleteNode: state.deleteNode,
        
        // Arrow operations
        addArrow: state.addArrow,
        updateArrow: state.updateArrow,
        deleteArrow: state.deleteArrow,
        
        // Person operations
        addPerson: (person: { name: string; service: string; model: string }) => 
          state.addPerson(person.name, person.service as LLMService, person.model),
        updatePerson: state.updatePerson,
        deletePerson: state.deletePerson,
        getPersonById: (id: PersonID) => state.persons.get(id),
        
        // Selection
        selectedId: state.selectedId,
        selectedType: state.selectedType,
        select: state.select,
        clearSelection: state.clearSelection,
        
        // Derived state helpers
        isNodeRunning: (id: NodeID) => state.execution.runningNodes.has(id),
        getNodeState: (id: NodeID) => state.execution.nodeStates.get(id),
        isSelected: (id: string) => state.selectedId === id,
        
        // React Flow handlers
        onNodesChange: (changes: NodeChange[]) => {
          if (state.readOnly) return;
          
          changes.forEach((change) => {
            if (change.type === 'position' && change.position && change.dragging !== false) {
              state.updateNode(change.id as NodeID, { position: change.position });
            } else if (change.type === 'remove') {
              state.deleteNode(change.id as NodeID);
            }
          });
        },
        
        onArrowsChange: (changes: EdgeChange[]) => {
          if (state.readOnly) return;
          
          changes.forEach((change) => {
            if (change.type === 'remove') {
              state.deleteArrow(change.id as ArrowID);
            }
          });
        },
        
        onConnect: (connection: Connection) => {
          if (state.readOnly) return;
          
          if (connection.source && connection.target && 
              connection.sourceHandle && connection.targetHandle) {
            state.addArrow(
              connection.sourceHandle as HandleID,
              connection.targetHandle as HandleID
            );
          }
        },
        
        // Batch operations
        transaction: state.transaction,
        
        // History
        undo: state.undo,
        redo: state.redo,
        canUndo: state.history.undoStack.length > 0,
        canRedo: state.history.redoStack.length > 0,
      };
    },
    shallow
  );
};