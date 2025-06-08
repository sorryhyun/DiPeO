// apps/web/src/utils/examples/phase8-usage.ts
/**
 * Examples demonstrating the Phase 8 Quality of Life improvements
 * This file shows how to use the new factory functions, builders, and utilities
 */

import {
  // Factory functions
  createStartNode,
  createPersonJobNode,
  createConditionNode,
  createEndpointNode,
  
  // Builder
  DiagramBuilder,
  
  // Connection helpers
  connect,
  canConnect,
  findValidTargets,
  connectChain,
  
  // Handle utilities
  getInputHandle,
  getOutputHandle,
  hasInputHandle,
  hasOutputHandle,
  getHandleNamesForType
} from '@/utils';

import { NodeType } from '@/types/enums';
import { personId } from '@/types/branded';
import { createTypedActions } from '@/stores/typed-actions';
import { useDiagramStore } from '@/stores/diagramStore';

/**
 * Example 1: Creating nodes with factory functions
 */
export function factoryExample() {
  // Create a start node
  const startNode = createStartNode(
    '{"message": "Hello, World!"}',
    { x: 100, y: 100 },
    'Data Source'
  );
  
  // Create a person job node
  const analysisNode = createPersonJobNode(
    personId('analyst-001'),
    {
      firstOnlyPrompt: 'Analyze this data: {{message}}',
      defaultPrompt: 'Continue analyzing...'
    },
    {
      maxIteration: 3,
      contextCleaningRule: 'no_forget',
      position: { x: 300, y: 100 },
      label: 'Data Analyst'
    }
  );
  
  // Create a condition node
  const validationNode = createConditionNode(
    '{{result.confidence}} > 0.8',
    'simple',
    { x: 500, y: 100 },
    'Quality Check'
  );
  
  // Create endpoint nodes
  const successEndpoint = createEndpointNode(
    'save',
    'results/analysis.json',
    { x: 700, y: 50 },
    'Save Results'
  );
  
  const retryEndpoint = createEndpointNode(
    'output',
    undefined,
    { x: 700, y: 150 },
    'Need Retry'
  );
  
  return {
    startNode,
    analysisNode,
    validationNode,
    successEndpoint,
    retryEndpoint
  };
}

/**
 * Example 2: Building a complete diagram with DiagramBuilder
 */
export function builderExample() {
  const builder = new DiagramBuilder({
    name: 'Customer Support Workflow',
    description: 'Automated customer inquiry processing',
    tags: ['support', 'automation']
  });
  
  // Add AI agents (persons)
  const supportAgentId = builder.addPerson('Support Agent', {
    model: 'gpt-4.1-nano',
    service: 'openai',
    systemPrompt: 'You are a helpful customer support agent.',
    temperature: 0.7
  });
  
  const supervisorId = builder.addPerson('Supervisor', {
    model: 'gpt-4.1-nano',
    service: 'openai',
    systemPrompt: 'You are a support supervisor who reviews complex cases.',
    temperature: 0.5
  });
  
  // Add nodes
  const start = builder.addNode(NodeType.Start, {
    output: '{"inquiry": "Customer inquiry text"}',
    label: 'Receive Inquiry'
  }, { x: 100, y: 200 });
  
  const initialResponse = builder.addNode(NodeType.PersonJob, {
    personId: supportAgentId,
    firstOnlyPrompt: 'Respond to this customer inquiry: {{inquiry}}',
    defaultPrompt: 'Continue the conversation...',
    maxIteration: 5,
    contextCleaningRule: 'no_forget',
    label: 'Initial Response'
  }, { x: 300, y: 200 });
  
  const checkComplexity = builder.addNode(NodeType.Condition, {
    condition: '{{complexity}} > 3',
    conditionType: 'simple',
    label: 'Is Complex?'
  }, { x: 500, y: 200 });
  
  const escalate = builder.addNode(NodeType.PersonJob, {
    personId: supervisorId,
    firstOnlyPrompt: 'Review this complex support case: {{conversation}}',
    defaultPrompt: 'Provide guidance...',
    maxIteration: 1,
    contextCleaningRule: 'no_forget',
    label: 'Escalate to Supervisor'
  }, { x: 700, y: 100 });
  
  const resolve = builder.addNode(NodeType.Endpoint, {
    action: 'save',
    filename: 'resolved_tickets/{{ticket_id}}.json',
    label: 'Mark Resolved'
  }, { x: 700, y: 300 });
  
  // Connect nodes
  builder.connect(start.id, 'default', initialResponse.id, 'first');
  builder.connect(initialResponse.id, 'default', checkComplexity.id, 'default');
  builder.connect(checkComplexity.id, 'true', escalate.id, 'first');
  builder.connect(checkComplexity.id, 'false', resolve.id, 'default');
  builder.connect(escalate.id, 'default', resolve.id, 'default');
  
  // Validate and build
  const validation = builder.validate();
  if (!validation.valid) {
    console.error('Diagram validation failed:', validation.errors);
  }
  
  return builder.build();
}

/**
 * Example 3: Using connection helpers
 */
export function connectionHelpersExample() {
  const nodes = factoryExample();
  
  // Check if connection is valid
  const canConnectStartToAnalysis = canConnect(
    { node: nodes.startNode, handle: 'default' },
    { node: nodes.analysisNode, handle: 'first' }
  );
  console.log('Can connect start to analysis:', canConnectStartToAnalysis);
  
  // Create a connection
  const connection = connect(
    { node: nodes.startNode, handle: 'default' },
    { node: nodes.analysisNode, handle: 'first' },
    { animated: true, label: 'Data Flow' }
  );
  
  // Find valid targets for a source
  const validTargets = findValidTargets(
    nodes.analysisNode,
    'default',
    [nodes.validationNode, nodes.successEndpoint]
  );
  console.log('Valid targets from analysis node:', validTargets);
  
  // Connect a chain of nodes
  const chainConnections = connectChain([
    nodes.startNode,
    nodes.analysisNode,
    nodes.validationNode
  ], [
    { from: 'default', to: 'first' },
    { from: 'default', to: 'default' }
  ]);
  
  return { connection, validTargets, chainConnections };
}

/**
 * Example 4: Using handle utilities
 */
export function handleUtilitiesExample() {
  const { analysisNode, validationNode } = factoryExample();
  
  // Get specific handles
  const firstInput = getInputHandle(analysisNode, 'first');
  const defaultOutput = getOutputHandle(analysisNode, 'default');
  
  console.log('First input handle:', firstInput);
  console.log('Default output handle:', defaultOutput);
  
  // Check if handles exist
  const hasFirst = hasInputHandle(analysisNode, 'first');
  const hasSecond = hasInputHandle(analysisNode, 'second'); // false
  
  console.log('Has first input:', hasFirst);
  console.log('Has second input:', hasSecond);
  
  // Get handle names for a node type
  const personJobHandles = getHandleNamesForType(NodeType.PersonJob);
  console.log('PersonJob handles:', personJobHandles);
  
  const conditionHandles = getHandleNamesForType(NodeType.Condition);
  console.log('Condition handles:', conditionHandles);
  
  return {
    firstInput,
    defaultOutput,
    personJobHandles,
    conditionHandles
  };
}

/**
 * Example 5: Using typed store actions
 */
export function typedStoreActionsExample() {
  const store = useDiagramStore();
  const actions = createTypedActions(store);
  
  // Add a person
  const agentId = actions.addPerson('Research Assistant', {
    model: 'gpt-4.1-nano',
    service: 'openai',
    systemPrompt: 'You are a research assistant.',
    temperature: 0.3
  });
  
  // Add nodes with type safety
  const startId = actions.addStartNode(
    '{"topic": "AI Safety"}',
    { x: 100, y: 100 },
    'Research Topic'
  );
  
  const researchId = actions.addPersonJobNode(
    agentId,
    'Research this topic: {{topic}}',
    'Continue researching...',
    {
      maxIteration: 10,
      contextCleaningRule: 'no_forget',
      position: { x: 300, y: 100 },
      label: 'Research Phase'
    }
  );
  
  // Connect nodes with type safety
  const connectionId = actions.connectNodes(
    startId,
    'default',
    researchId,
    'first',
    { animated: true }
  );
  
  // Update node data with type safety
  actions.updateNodeData(researchId, {
    maxIteration: 15,
    label: 'Extended Research Phase'
  });
  
  // Validate the diagram
  const validation = actions.validateDiagram();
  console.log('Diagram validation:', validation);
  
  return {
    agentId,
    startId,
    researchId,
    connectionId,
    validation
  };
}

/**
 * Example 6: Complex workflow with all features
 */
export function complexWorkflowExample() {
  const builder = new DiagramBuilder({
    name: 'Content Generation Pipeline',
    description: 'Multi-stage content creation with quality checks'
  });
  
  // Add multiple AI agents
  const writerId = builder.addPerson('Writer', {
    model: 'gpt-4.1-nano',
    service: 'openai',
    systemPrompt: 'You are a creative content writer.',
    temperature: 0.9
  });
  
  const editorId = builder.addPerson('Editor', {
    model: 'gpt-4.1-nano',
    service: 'openai',
    systemPrompt: 'You are a meticulous editor.',
    temperature: 0.3
  });
  
  const reviewerId = builder.addPerson('Reviewer', {
    model: 'gpt-4.1-nano',
    service: 'openai',
    systemPrompt: 'You are a quality reviewer.',
    temperature: 0.5
  });
  
  // Build the workflow
  const start = builder.addNode(NodeType.Start, {
    output: '{"topic": "AI Ethics", "style": "academic"}',
    label: 'Content Brief'
  });
  
  const draft = builder.addNode(NodeType.PersonJob, {
    personId: writerId,
    firstOnlyPrompt: 'Write an article about {{topic}} in {{style}} style',
    defaultPrompt: 'Continue writing...',
    maxIteration: 5,
    contextCleaningRule: 'no_forget'
  }, { x: 200, y: 100 });
  
  const edit = builder.addNode(NodeType.PersonJob, {
    personId: editorId,
    firstOnlyPrompt: 'Edit this article for clarity and grammar: {{article}}',
    defaultPrompt: 'Continue editing...',
    maxIteration: 3,
    contextCleaningRule: 'no_forget'
  }, { x: 400, y: 100 });
  
  const qualityCheck = builder.addNode(NodeType.Condition, {
    condition: '{{quality_score}} >= 8',
    conditionType: 'simple',
    label: 'Quality Pass?'
  }, { x: 600, y: 100 });
  
  const review = builder.addNode(NodeType.PersonJob, {
    personId: reviewerId,
    firstOnlyPrompt: 'Review and suggest improvements: {{edited_article}}',
    defaultPrompt: 'Provide more feedback...',
    maxIteration: 2,
    contextCleaningRule: 'upon_request'
  }, { x: 800, y: 50 });
  
  const publish = builder.addNode(NodeType.Endpoint, {
    action: 'save',
    filename: 'published/{{article_id}}.md',
    label: 'Publish Article'
  }, { x: 800, y: 150 });
  
  // Create the flow (using any to avoid complex type inference)
  builder.connect(start.id, 'default' as any, draft.id, 'first' as any);
  builder.connect(draft.id, 'default' as any, edit.id, 'first' as any);
  builder.connect(edit.id, 'default' as any, qualityCheck.id, 'default' as any);
  builder.connect(qualityCheck.id, 'false' as any, review.id, 'first' as any);
  builder.connect(qualityCheck.id, 'true' as any, publish.id, 'default' as any);
  builder.connect(review.id, 'default' as any, edit.id, 'default' as any, {
    label: 'Revise'
  });
  
  const diagram = builder.build();
  console.log('Complex workflow created:', diagram);
  
  return diagram;
}

// Export all examples
export const Phase8Examples = {
  factory: factoryExample,
  builder: builderExample,
  connectionHelpers: connectionHelpersExample,
  handleUtilities: handleUtilitiesExample,
  typedStoreActions: typedStoreActionsExample,
  complexWorkflow: complexWorkflowExample
};