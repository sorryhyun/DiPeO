import { useState, useCallback } from 'react';
import { useExecutionStore } from '@/core/stores/executionStore';
import { getApiUrl, API_ENDPOINTS } from '@/shared/utils/apiConfig';
import type { Node } from '@/shared/types';

interface DiagramData {
  nodes: Node[];
  arrows: any[];
  persons?: any[];
  apiKeys?: any[];
}

interface PartitionedNodes {
  clientNodes: Node[];
  serverNodes: Node[];
}

interface ExecutionResult {
  context: Record<string, any>;
  total_cost?: number;
  execution_id?: string;
}

export function useHybridExecution() {
  const [isExecuting, setIsExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { 
    setCurrentRunningNode,
    clearRunningNodes,
    addRunningNode,
    removeRunningNode
  } = useExecutionStore();
  
  // Partition nodes based on execution environment
  const partitionNodes = useCallback((nodes: Node[]): PartitionedNodes => {
    const clientSafeTypes = new Set(['startNode', 'conditionNode', 'jobNode']);
    const serverOnlyTypes = new Set(['personJobNode', 'personBatchJobNode', 'dbNode', 'endpointNode']);
    
    const clientNodes: Node[] = [];
    const serverNodes: Node[] = [];
    
    nodes.forEach(node => {
      if (clientSafeTypes.has(node.type || '')) {
        clientNodes.push(node);
      } else if (serverOnlyTypes.has(node.type || '')) {
        serverNodes.push(node);
      }
    });
    
    return { clientNodes, serverNodes };
  }, []);
  
  // Execute nodes locally in the browser
  const executeLocally = useCallback(async (
    nodes: Node[], 
    diagram: DiagramData
  ): Promise<Partial<ExecutionResult>> => {
    try {
      // For now, just simulate local execution
      console.log('Executing locally:', nodes.length, 'nodes');
      
      // Simulate node execution
      for (const node of nodes) {
        addRunningNode(node.id);
        setCurrentRunningNode(node.id);
        
        // Simulate processing time
        await new Promise(resolve => setTimeout(resolve, 100));
        
        removeRunningNode(node.id);
      }
      
      setCurrentRunningNode(null);
      
      return {
        context: { localExecution: true }
      };
    } catch (err) {
      console.error('Local execution error:', err);
      throw err;
    }
  }, [addRunningNode, removeRunningNode, setCurrentRunningNode]);
  
  // Execute nodes on the server
  const executeRemotely = useCallback(async (
    nodes: Node[],
    diagram: DiagramData,
    sessionId: string
  ): Promise<ExecutionResult> => {
    try {
      // For now, use existing API endpoint
      const response = await fetch(getApiUrl(API_ENDPOINTS.RUN_DIAGRAM), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...diagram,
          nodes
        })
      });
      
      if (!response.ok) {
        throw new Error('Remote execution failed');
      }
      
      // This is a placeholder - real implementation would handle streaming
      return {
        context: { remoteExecution: true },
        execution_id: sessionId
      };
    } catch (err) {
      console.error('Remote execution error:', err);
      throw err;
    }
  }, []);
  
  // Merge results from client and server execution
  const mergeResults = useCallback((
    clientResults: Partial<ExecutionResult>,
    serverResults: ExecutionResult
  ): ExecutionResult => {
    return {
      context: {
        ...clientResults.context,
        ...serverResults.context
      },
      total_cost: (clientResults.total_cost || 0) + (serverResults.total_cost || 0),
      execution_id: serverResults.execution_id || clientResults.execution_id
    };
  }, []);
  
  // Main hybrid execution function
  const executeHybrid = useCallback(async (diagram: DiagramData) => {
    setIsExecuting(true);
    setError(null);
    clearRunningNodes();
    
    try {
      // Generate session ID
      const sessionId = `hybrid-${Date.now()}`;
      
      // Partition nodes
      const { clientNodes, serverNodes } = partitionNodes(diagram.nodes);
      
      console.log(`Executing ${clientNodes.length} nodes locally, ${serverNodes.length} nodes on server`);
      
      // Execute in parallel when possible
      const promises: Promise<any>[] = [];
      
      // Execute client nodes if any
      if (clientNodes.length > 0) {
        promises.push(executeLocally(clientNodes, diagram));
      }
      
      // Execute server nodes if any
      if (serverNodes.length > 0) {
        promises.push(executeRemotely(serverNodes, diagram, sessionId));
      }
      
      // Wait for all executions
      const results = await Promise.all(promises);
      
      // Merge results
      const clientResults = clientNodes.length > 0 ? results[0] : { context: {} };
      const serverResults = serverNodes.length > 0 
        ? (clientNodes.length > 0 ? results[1] : results[0])
        : { context: {} };
      
      const finalResult = mergeResults(clientResults, serverResults);
      
      return finalResult;
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setIsExecuting(false);
      setCurrentRunningNode(null);
    }
  }, [
    partitionNodes,
    executeLocally,
    executeRemotely,
    mergeResults,
    clearRunningNodes,
    setCurrentRunningNode
  ]);
  
  return {
    executeHybrid,
    isExecuting,
    error,
    partitionNodes
  };
}