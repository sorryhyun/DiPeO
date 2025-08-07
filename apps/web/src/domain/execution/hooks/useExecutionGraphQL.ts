import {
  ExecutionUpdatesDocument,
  ExecuteDiagramDocument,
  ControlExecutionDocument,
  SendInteractiveResponseDocument,
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
  document: SendInteractiveResponseDocument,
  silent: true // Custom handling in component
});

// Subscriptions
const useExecutionUpdatesSubscription = createEntitySubscription({
  entityName: 'Execution',
  document: ExecutionUpdatesDocument,
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

  return {
    // Mutations
    executeDiagram: executeDiagramMutation,
    controlExecution: controlExecutionMutation,
    submitInteractiveResponse: submitInteractiveResponseMutation,
    
    // Subscription data
    executionUpdates: executionData?.execution_updates,
    // TODO: These subscriptions no longer exist separately - data is in executionUpdates
    nodeUpdates: undefined,
    interactivePrompts: undefined,
  };
}