import {
  ExecutionUpdatesDocument,
  NodeUpdatesDocument,
  InteractivePromptsDocument,
  ExecuteDiagramDocument,
  ControlExecutionDocument,
  SubmitInteractiveResponseDocument,
} from '@/__generated__/graphql';
import { createEntityMutation, createEntitySubscription } from '@/lib/graphql/hooks';

export interface UseExecutionGraphQLProps {
  executionId: string | null;
  skip?: boolean;
}

/**
 * Create individual hooks for each operation
 * Following the pattern from successfully refactored files
 */
// Mutations
const useExecuteDiagramMutation = createEntityMutation({
  entityName: 'Execution',
  document: ExecuteDiagramDocument,
  silent: true // Custom handling in component
});

const useControlExecutionMutation = createEntityMutation({
  entityName: 'Execution',
  document: ControlExecutionDocument,
  silent: true // Custom handling in component
});

const useSubmitInteractiveResponseMutation = createEntityMutation({
  entityName: 'Execution',
  document: SubmitInteractiveResponseDocument,
  silent: true // Custom handling in component
});

// Subscriptions
const useExecutionUpdatesSubscription = createEntitySubscription({
  entityName: 'Execution',
  document: ExecutionUpdatesDocument,
  silent: true
});

const useNodeUpdatesSubscription = createEntitySubscription({
  entityName: 'Execution',
  document: NodeUpdatesDocument,
  silent: true
});

const useInteractivePromptsSubscription = createEntitySubscription({
  entityName: 'Execution',
  document: InteractivePromptsDocument,
  silent: true
});

export function useExecutionGraphQL({ executionId, skip = false }: UseExecutionGraphQLProps) {
  // Mutations - using factory-generated hooks
  const [executeDiagramMutation] = useExecuteDiagramMutation();
  const [controlExecutionMutation] = useControlExecutionMutation();
  const [submitInteractiveResponseMutation] = useSubmitInteractiveResponseMutation();

  // Subscriptions - using factory-generated hooks
  const { data: executionData } = useExecutionUpdatesSubscription(
    { executionId: executionId! },
    { skip: skip || !executionId }
  );

  const { data: nodeData } = useNodeUpdatesSubscription(
    { executionId: executionId! },
    { skip: skip || !executionId }
  );

  const { data: promptData } = useInteractivePromptsSubscription(
    { executionId: executionId! },
    { skip: skip || !executionId }
  );

  return {
    // Mutations
    executeDiagram: executeDiagramMutation,
    controlExecution: controlExecutionMutation,
    submitInteractiveResponse: submitInteractiveResponseMutation,
    
    // Subscription data
    executionUpdates: executionData?.execution_updates,
    nodeUpdates: nodeData?.node_updates,
    interactivePrompts: promptData?.interactive_prompts,
  };
}