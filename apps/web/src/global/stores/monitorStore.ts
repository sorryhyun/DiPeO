import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { DiagramNode, Arrow, PersonDefinition, ApiKey, DiagramState } from '@/shared/types';
import { sanitizeDiagram } from "@/features/serialization/utils/diagramSanitizer";

export interface MonitorState {
  // Monitor storage for external diagrams (not persisted)
  monitorNodes: DiagramNode[];
  monitorArrows: Arrow[];
  monitorPersons: PersonDefinition[];
  monitorApiKeys: ApiKey[];
  isMonitorMode: boolean;
  
  // Monitor-specific methods
  loadMonitorDiagram: (state: DiagramState) => void;
  clearMonitorDiagram: () => void;
  setMonitorMode: (enabled: boolean) => void;
  exportMonitorDiagram: () => DiagramState;
}

export const useMonitorStore = create<MonitorState>()(
  devtools(
    subscribeWithSelector(
      (set, get) => ({
        monitorNodes: [],
        monitorArrows: [],
        monitorPersons: [],
        monitorApiKeys: [],
        isMonitorMode: false,
        
        loadMonitorDiagram: (state: DiagramState) => {
          const sanitized = sanitizeDiagram(state);
          const nodes = (sanitized.nodes || []) as DiagramNode[];
          
          // Process arrows to set proper content type based on source node
          const arrows = ((sanitized.arrows || []) as Arrow[]).map(arrow => {
            const sourceNode = nodes.find(n => n.id === arrow.source);
            const isFromStartNode = sourceNode?.data.type === 'start';
            const isFromConditionBranch = arrow.sourceHandle === 'true' || arrow.sourceHandle === 'false';
            
            if (arrow.data) {
              if (isFromStartNode) {
                return {
                  ...arrow,
                  data: {
                    ...arrow.data,
                    contentType: 'empty' as const
                  }
                };
              } else if (isFromConditionBranch) {
                return {
                  ...arrow,
                  data: {
                    ...arrow.data,
                    contentType: 'generic' as const
                  }
                };
              }
            }
            return arrow;
          });
          
          set({
            monitorNodes: nodes,
            monitorArrows: arrows,
            monitorPersons: sanitized.persons || [],
            monitorApiKeys: sanitized.apiKeys || [],
            isMonitorMode: true
          });
        },
        
        clearMonitorDiagram: () => {
          set({
            monitorNodes: [],
            monitorArrows: [],
            monitorPersons: [],
            monitorApiKeys: [],
            isMonitorMode: false
          });
        },
        
        setMonitorMode: (enabled: boolean) => {
          set({ isMonitorMode: enabled });
        },
        
        exportMonitorDiagram: (): DiagramState => {
          const { monitorNodes, monitorArrows, monitorPersons, monitorApiKeys } = get();
          const sanitized = sanitizeDiagram({
            nodes: monitorNodes,
            arrows: monitorArrows,
            persons: monitorPersons,
            apiKeys: monitorApiKeys
          });
          return sanitized;
        },
      })
    )
  )
);