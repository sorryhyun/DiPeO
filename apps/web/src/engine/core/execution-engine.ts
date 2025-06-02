/**
 * Core execution engine for orchestrating diagram execution.
 * 
 * This engine is environment-agnostic and can run in both browser and Node.js environments.
 * It uses dependency injection for executors, allowing different implementations for client vs server.
 */

import { 
  Diagram, 
  ExecutionOptions, 
  ExecutionResult, 
  ExecutionContext,
  ExecutionContext as TypedExecutionContext,
  ExecutionMetadata,
  ExecutionStatus,
  Node,
  NodeType,
  DiagramNode,
  DiagramArrow,
  ExecutionError,
  NodeExecutionError,
  DiagramExecutionError,
  MaxIterationsError,
  DEFAULT_MAX_ITERATIONS,
  DEFAULT_EXECUTION_TIMEOUT,
  BaseExecutorInterface,
  ExecutorResult
} from '@/shared/types/core';
import { createExecutionContext } from '../index';
import { DependencyResolver } from '../flow/dependency-resolver';
import { ExecutionPlanner } from '../flow/execution-planner';
import { SkipManager } from './skip-manager';
import { LoopController } from './loop-controller';

export interface ExecutorFactory {
  /**
   * Create an executor for a specific node type
   */
  createExecutor(nodeType: string): BaseExecutorInterface;
  
  /**
   * Check if a node type can be executed in the current environment
   */
  canExecute(nodeType: string): boolean;
  
  /**
   * Get all supported node types in this environment
   */
  getSupportedNodeTypes(): string[];
}

export interface StreamManager {
  /**
   * Emit a stream update
   */
  emit(update: any): void;
  
  /**
   * Check if streaming is enabled
   */
  isEnabled(): boolean;
}

export class ExecutionEngine {
  private dependencyResolver?: DependencyResolver;
  private executionPlanner?: ExecutionPlanner;
  private skipManager: SkipManager;
  private loopController?: LoopController;
  
  // Node type mappings between React Flow types and core execution types
  private static readonly NODE_TYPE_MAP: Record<string, string> = {
    'startNode': 'start',
    'personJobNode': 'person_job',
    'personBatchJobNode': 'person_batch_job',
    'conditionNode': 'condition',
    'dbNode': 'db',
    'jobNode': 'job',
    'endpointNode': 'endpoint'
  };
  
  constructor(
    private executorFactory: ExecutorFactory,
    private streamManager?: StreamManager
  ) {
    this.skipManager = new SkipManager();
  }

  /**
   * Normalize node types from React Flow types to core execution types
   */
  private normalizeNodeType(nodeType: string): string {
    return ExecutionEngine.NODE_TYPE_MAP[nodeType] || nodeType;
  }

  /**
   * Normalize diagram nodes to use core execution types
   */
  private normalizeDiagram(diagram: Diagram): Diagram {
    return {
      ...diagram,
      nodes: diagram.nodes.map(node => ({
        ...node,
        type: this.normalizeNodeType(node.type) as NodeType
      }))
    };
  }

  /**
   * Execute a diagram with the given options
   */
  async execute(diagram: Diagram, options: ExecutionOptions = {}): Promise<ExecutionResult> {
    const executionId = this.generateExecutionId();
    const startTime = Date.now();
    
    // Normalize node types before execution
    const normalizedDiagram = this.normalizeDiagram(diagram);
    
    // Initialize execution metadata
    const metadata: ExecutionMetadata = {
      executionId,
      startTime,
      totalCost: 0,
      nodeCount: normalizedDiagram.nodes.length,
      status: 'running'
    };

    // Emit execution started event
    this.emitStreamUpdate({
      type: 'execution_started',
      executionId,
      data: { diagram: normalizedDiagram, options },
      timestamp: new Date()
    });

    try {
      // Create execution context from normalized diagram
      const context = this.createTypedExecutionContext(normalizedDiagram, executionId, startTime);
      
      // Initialize components
      this.initializeComponents(normalizedDiagram, context, options);
      
      // Validate diagram before execution
      if (!options.skipValidation) {
        await this.validateDiagram(normalizedDiagram, context);
      }
      
      // Execute the diagram
      const finalOutputs = await this.executeNodes(normalizedDiagram, context, options);
      
      // Create successful result
      const result: ExecutionResult = {
        success: true,
        context,
        metadata: {
          ...metadata,
          endTime: Date.now(),
          status: 'completed',
          totalCost: context.totalCost
        },
        finalOutputs,
        errors: []
      };

      this.emitStreamUpdate({
        type: 'execution_completed',
        executionId,
        data: result,
        timestamp: new Date()
      });

      return result;

    } catch (error) {
      const executionError = this.handleExecutionError(error, executionId);
      
      const result: ExecutionResult = {
        success: false,
        context: this.createTypedExecutionContext(normalizedDiagram, executionId, startTime),
        metadata: {
          ...metadata,
          endTime: Date.now(),
          status: 'failed',
          totalCost: 0
        },
        finalOutputs: {},
        errors: [executionError]
      };

      this.emitStreamUpdate({
        type: 'execution_failed',
        executionId,
        data: { error: executionError },
        timestamp: new Date()
      });

      return result;
    }
  }

  /**
   * Initialize all execution components
   */
  private initializeComponents(
    diagram: Diagram, 
    context: TypedExecutionContext, 
    options: ExecutionOptions
  ): void {
    // Create legacy context for existing components
    const legacyContext = createExecutionContext(
      diagram.nodes.map(n => ({ ...n, data: n.data as any })) as DiagramNode[],
      diagram.arrows as DiagramArrow[]
    );
    
    this.dependencyResolver = new DependencyResolver(legacyContext);
    this.executionPlanner = new ExecutionPlanner(legacyContext, this.dependencyResolver);
    
    // Initialize loop controller if needed
    const cycles = this.dependencyResolver.detectCycles();
    if (cycles.length > 0) {
      const loopNodes = cycles.flat();
      this.loopController = new LoopController(
        options.maxIterations || DEFAULT_MAX_ITERATIONS,
        loopNodes
      );
    }
    
    // Clear skip manager for fresh execution
    this.skipManager.clear();
  }

  /**
   * Validate the diagram before execution
   */
  private async validateDiagram(diagram: Diagram, context: TypedExecutionContext): Promise<void> {
    if (!this.dependencyResolver) {
      throw new DiagramExecutionError('Dependency resolver not initialized');
    }

    // Check for cycles
    const cycles = this.dependencyResolver.detectCycles();
    if (cycles.length > 0) {
      console.warn(`Diagram contains ${cycles.length} cycle(s). Loop controller will manage execution.`);
    }

    // Validate start nodes
    const startNodes = this.dependencyResolver.validateStartNodes();
    if (startNodes.length === 0) {
      throw new DiagramExecutionError('No start nodes found in diagram');
    }

    // Validate node types are supported
    for (const node of diagram.nodes) {
      if (!this.executorFactory.canExecute(node.type)) {
        throw new DiagramExecutionError(
          `Unsupported node type: ${node.type}`,
          { nodeId: node.id, nodeType: node.type }
        );
      }
    }
  }

  /**
   * Execute all nodes in the diagram
   */
  private async executeNodes(
    diagram: Diagram,
    context: TypedExecutionContext, 
    options: ExecutionOptions
  ): Promise<Record<string, any>> {
    if (!this.dependencyResolver || !this.executionPlanner) {
      throw new DiagramExecutionError('Execution components not initialized');
    }

    const startTime = Date.now();
    const timeout = options.timeout || DEFAULT_EXECUTION_TIMEOUT;
    const maxIterations = options.maxIterations || DEFAULT_MAX_ITERATIONS;
    
    const executedNodes = new Set<string>();
    const pendingNodes = new Set<string>();
    let currentIteration = 0;

    // Get start nodes
    const startNodes = this.dependencyResolver.validateStartNodes();
    pendingNodes.clear();
    startNodes.forEach(nodeId => pendingNodes.add(nodeId));

    while (pendingNodes.size > 0 && currentIteration < maxIterations) {
      // Check timeout
      if (Date.now() - startTime > timeout) {
        throw new DiagramExecutionError('Execution timeout exceeded');
      }

      currentIteration++;
      const nodesToExecute = Array.from(pendingNodes);
      pendingNodes.clear();
      let nodesExecutedThisIteration = 0;

      // Execute nodes in this iteration
      for (const nodeId of nodesToExecute) {
        try {
          const currentNode = diagram.nodes.find(n => n.id === nodeId);
          console.log(`[DEBUG] Attempting to execute node ${nodeId} (type: ${currentNode?.type})`);
          
          // Check if node should be skipped
          if (this.skipManager.isSkipped(nodeId)) {
            console.log(`Skipping node ${nodeId}: ${this.skipManager.getSkipReason(nodeId)}`);
            continue;
          }

          // Check if node has reached max iterations
          if (currentNode) {
            const executionCount = context.nodeExecutionCounts[nodeId] || 0;
            const maxIterations = currentNode.data.iterationCount || currentNode.data.maxIterations;
            
            if (maxIterations && this.skipManager.shouldSkip(nodeId, executionCount, maxIterations)) {
              console.log(`Skipping node ${nodeId}: max iterations (${maxIterations}) reached`);
              
              // For skipped nodes, we still need to process their outgoing connections
              // This ensures the flow continues even when nodes are skipped
              // IMPORTANT: During skipping, the forget rule does not apply - all inputs are counted
              // regardless of whether they came from first-only or default handles
              const nextNodes = this.dependencyResolver.getNextNodes(nodeId, context.conditionValues);
              nextNodes.forEach(nextNodeId => {
                if (!executedNodes.has(nextNodeId) && !pendingNodes.has(nextNodeId)) {
                  pendingNodes.add(nextNodeId);
                }
              });
              
              // Mark the node as having been executed (for dependency checking)
              // even though it was skipped
              executedNodes.add(nodeId);
              
              continue;
            }
          }

          // Check dependencies
          const [dependenciesMet, validArrows] = this.dependencyResolver.checkDependenciesMet(
            nodeId, 
            executedNodes, 
            context.conditionValues
          );

          console.log(`[DEBUG] Dependencies met for ${nodeId}: ${dependenciesMet}, executed nodes: [${Array.from(executedNodes).join(', ')}]`);

          if (!dependenciesMet) {
            // Re-add to pending if dependencies not met
            console.log(`[DEBUG] Re-adding ${nodeId} to pending due to unmet dependencies`);
            pendingNodes.add(nodeId);
            continue;
          }

          // Check if this is a PersonJob or Job node executing with first-only for the first time
          if (currentNode && (currentNode.type === 'person_job' || currentNode.type === 'job')) {
            const hasFirstOnlyInput = validArrows.some(arrow => 
              arrow.targetHandle?.endsWith('-input-first') || arrow.data?.handleMode === 'first_only'
            );
            
            if (hasFirstOnlyInput && !context.firstOnlyConsumed[nodeId]) {
              // Mark first-only as consumed for this node
              context.firstOnlyConsumed[nodeId] = true;
            }
          }

          // Execute the node
          await this.executeNode(nodeId, diagram, context, options);
          executedNodes.add(nodeId);
          nodesExecutedThisIteration++;
          console.log(`[DEBUG] Node ${nodeId} executed successfully`);

          // Get next nodes to execute
          const nextNodes = this.dependencyResolver.getNextNodes(nodeId, context.conditionValues);
          console.log(`[DEBUG] Next nodes from ${nodeId}: [${nextNodes.join(', ')}]`);
          nextNodes.forEach(nextNodeId => {
            if (!executedNodes.has(nextNodeId) && !pendingNodes.has(nextNodeId)) {
              pendingNodes.add(nextNodeId);
              console.log(`[DEBUG] Added ${nextNodeId} to pending nodes`);
            }
          });

        } catch (error) {
          // Handle node execution error
          const nodeError = error instanceof NodeExecutionError 
            ? error 
            : new NodeExecutionError(
                `Error executing node ${nodeId}: ${error instanceof Error ? error.message : String(error)}`,
                nodeId,
                diagram.nodes.find(n => n.id === nodeId)?.type || 'start',
                { originalError: error }
              );

          context.errors[nodeId] = nodeError.message;
          
          // Decide whether to continue or stop execution
          if (options.debugMode) {
            console.error(`Node execution failed: ${nodeError.message}`, nodeError);
            // In debug mode, continue with other nodes
            executedNodes.add(nodeId); // Mark as executed to prevent retry
          } else {
            throw nodeError;
          }
        }
      }

      // If no progress was made and we still have pending nodes, there might be a dependency issue
      if (pendingNodes.size > 0 && nodesExecutedThisIteration === 0) {
        const pendingArray = Array.from(pendingNodes);
        throw new DiagramExecutionError(
          `Execution deadlock detected. Pending nodes: ${pendingArray.join(', ')}`,
          { pendingNodes: pendingArray, currentIteration }
        );
      }
    }

    if (currentIteration >= maxIterations) {
      throw new MaxIterationsError(
        `Maximum iterations (${maxIterations}) exceeded`,
        { currentIteration, pendingNodes: Array.from(pendingNodes) }
      );
    }

    return context.nodeOutputs;
  }

  /**
   * Execute a single node
   */
  private async executeNode(
    nodeId: string,
    diagram: Diagram,
    context: TypedExecutionContext,
    options: ExecutionOptions
  ): Promise<void> {
    const node = diagram.nodes.find(n => n.id === nodeId);
    if (!node) {
      throw new NodeExecutionError(
        `Node ${nodeId} not found in diagram`,
        nodeId,
        'start' as any
      );
    }

    // Emit node started event
    this.emitStreamUpdate({
      type: 'node_started',
      executionId: context.executionId,
      nodeId,
      data: { node },
      timestamp: new Date()
    });

    try {
      // Get executor for this node type
      const executor = this.executorFactory.createExecutor(node.type);
      
      // Validate inputs
      const validation = await executor.validateInputs(node, context);
      if (!validation.isValid) {
        throw new NodeExecutionError(
          `Input validation failed: ${validation.errors.join(', ')}`,
          nodeId,
          node.type,
          { validationErrors: validation.errors }
        );
      }

      // Execute the node
      const result = await executor.execute(node, context, options);
      
      // Update context with results
      context.nodeOutputs[nodeId] = result.output;
      context.totalCost += result.cost;
      context.nodeExecutionCounts[nodeId] = (context.nodeExecutionCounts[nodeId] || 0) + 1;
      context.executionOrder.push(nodeId);

      // Handle condition node results
      if (node.type === 'condition' && typeof result.output === 'boolean') {
        context.conditionValues[nodeId] = result.output;
      }

      // Emit node completed event
      this.emitStreamUpdate({
        type: 'node_completed',
        executionId: context.executionId,
        nodeId,
        data: { result },
        timestamp: new Date()
      });

    } catch (error) {
      // Emit node failed event
      this.emitStreamUpdate({
        type: 'node_failed',
        executionId: context.executionId,
        nodeId,
        data: { error: error instanceof Error ? error.message : String(error) },
        timestamp: new Date()
      });

      throw error;
    }
  }

  /**
   * Create a typed execution context from a diagram
   */
  private createTypedExecutionContext(
    diagram: Diagram, 
    executionId: string, 
    startTime: number
  ): TypedExecutionContext {
    // Create nodes by ID map
    const nodesById: Record<string, any> = {};
    const incomingArrows: Record<string, any[]> = {};
    const outgoingArrows: Record<string, any[]> = {};

    // Initialize maps
    for (const node of diagram.nodes) {
      nodesById[node.id] = node;
      incomingArrows[node.id] = [];
      outgoingArrows[node.id] = [];
    }

    // Populate arrow maps
    for (const arrow of diagram.arrows) {
      if (arrow.source && arrow.target) {
        const sourceArrows = outgoingArrows[arrow.source] || [];
        const targetArrows = incomingArrows[arrow.target] || [];
        
        outgoingArrows[arrow.source] = [...sourceArrows, arrow];
        incomingArrows[arrow.target] = [...targetArrows, arrow];
      }
    }

    return {
      executionId,
      nodeOutputs: {},
      nodeExecutionCounts: {},
      totalCost: 0,
      startTime,
      errors: {},
      executionOrder: [],
      conditionValues: {},
      firstOnlyConsumed: {},
      diagram: null,
      nodesById,
      outgoingArrows,
      incomingArrows
    };
  }

  /**
   * Handle and standardize execution errors
   */
  private handleExecutionError(error: any, executionId: string): ExecutionError {
    if (error instanceof NodeExecutionError || error instanceof DiagramExecutionError) {
      return {
        nodeId: error instanceof NodeExecutionError ? error.nodeId : undefined,
        nodeType: error instanceof NodeExecutionError ? error.nodeType : undefined,
        message: error.message,
        details: error.details,
        timestamp: new Date(),
        stack: error.stack
      };
    }

    return {
      message: error.message || 'Unknown execution error',
      details: { originalError: error },
      timestamp: new Date(),
      stack: error.stack
    };
  }

  /**
   * Emit a stream update if streaming is enabled
   */
  private emitStreamUpdate(update: any): void {
    if (this.streamManager && this.streamManager.isEnabled()) {
      this.streamManager.emit(update);
    }
  }

  /**
   * Generate a unique execution ID
   */
  private generateExecutionId(): string {
    return `exec_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get the current execution status
   */
  getStatus(): ExecutionStatus {
    // This could be enhanced to track actual execution state
    return 'pending';
  }

  /**
   * Stop the current execution
   */
  async stop(): Promise<void> {
    // Implementation for stopping execution
    // This could involve setting a stop flag that is checked during execution loops
    console.log('Execution stop requested');
  }
}