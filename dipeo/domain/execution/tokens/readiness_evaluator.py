"""Token readiness evaluation for node execution."""

from dipeo.diagram_generated import NodeID, NodeType
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
from dipeo.domain.execution.tokens.policies import JoinPolicyEvaluator, JoinPolicyType, TokenCounter
from dipeo.domain.execution.tokens.token_types import EdgeRef


class TokenReadinessEvaluator:
    """Evaluates whether a node is ready to execute based on token availability.

    Responsibilities:
    - Filter relevant edges based on execution state
    - Handle skippable condition nodes
    - Apply branch decision filtering
    - Evaluate join policies (all/any/k_of_n)
    """

    def __init__(
        self,
        diagram: ExecutableDiagram,
        in_edges: dict[NodeID, list[EdgeRef]],
        token_counter: TokenCounter,
        branch_decisions: dict[NodeID, str],
    ):
        """Initialize evaluator with token manager state.

        Args:
            diagram: The executable diagram
            in_edges: Map of node ID to incoming edges
            token_counter: Token counter for checking sequence state
            branch_decisions: Map of condition node ID to branch taken
        """
        self.diagram = diagram
        self._in_edges = in_edges
        self._token_counter = token_counter
        self._branch_decisions = branch_decisions
        self._policy_evaluator = JoinPolicyEvaluator(token_checker=self)

    def has_new_inputs(
        self,
        node_id: NodeID,
        epoch: int,
        join_policy: str,
        node_exec_count: int = 0,
    ) -> bool:
        """Check if a node has new inputs to process.

        Args:
            node_id: The node to check
            epoch: The epoch to check
            join_policy: The join policy type ("all", "any", etc.)
            node_exec_count: Number of times node has executed

        Returns:
            True if the node has unconsumed tokens per its join policy
        """
        edges = self._in_edges.get(node_id, [])
        if not edges:
            return True

        # Step 1: Get relevant edges (filter START edges after first execution)
        relevant_edges = self._get_relevant_edges(edges, node_exec_count)

        # Step 2: Separate active and skippable edges
        active_edges = self._separate_skippable_edges(relevant_edges)

        # Step 3: Filter by branch decisions (for condition edges)
        required_edges = self._filter_by_branch_decisions(active_edges)

        # Step 4: Evaluate join policy
        return self._evaluate_join_policy(required_edges, node_id, epoch, join_policy)

    def _get_relevant_edges(self, edges: list[EdgeRef], node_exec_count: int) -> list[EdgeRef]:
        """Filter edges, excluding START edges after first execution.

        START nodes should only provide tokens once. After a node executes once,
        incoming edges from START nodes are no longer relevant.

        Args:
            edges: All incoming edges
            node_exec_count: Number of times the node has executed

        Returns:
            Edges that should be considered for readiness
        """
        relevant_edges = []
        for edge in edges:
            source_node = self.diagram.get_node(edge.source_node_id)

            # Skip START edges if node has already executed
            if source_node and hasattr(source_node, "type") and source_node.type == NodeType.START:
                if node_exec_count > 0:
                    continue

            relevant_edges.append(edge)

        return relevant_edges

    def _separate_skippable_edges(self, edges: list[EdgeRef]) -> list[EdgeRef]:
        """Separate active edges from skippable condition edges.

        Skippable condition nodes allow execution to continue even if their
        output is not available, but only if there are other non-skippable sources.

        Args:
            edges: Relevant incoming edges

        Returns:
            Active edges that must be satisfied
        """
        active_edges = []
        skippable_edges = []

        for edge in edges:
            source_node = self.diagram.get_node(edge.source_node_id)

            # Check if source is a skippable condition
            if (
                source_node
                and hasattr(source_node, "type")
                and source_node.type == NodeType.CONDITION
            ):
                is_skippable = getattr(source_node, "skippable", False)

                if is_skippable:
                    # Count unique sources
                    unique_sources = set(e.source_node_id for e in edges)

                    # Only skip if there are other sources
                    if len(unique_sources) > 1:
                        skippable_edges.append(edge)
                        continue

            active_edges.append(edge)

        # If all edges are skippable, treat them as active
        if not active_edges and skippable_edges:
            active_edges = skippable_edges

        return active_edges

    def _filter_by_branch_decisions(self, edges: list[EdgeRef]) -> list[EdgeRef]:
        """Filter edges based on condition branch decisions.

        For edges coming from condition nodes (condtrue/condfalse), only include
        the edge matching the branch that was taken.

        Args:
            edges: Active edges

        Returns:
            Edges matching branch decisions
        """
        required_edges = []

        for edge in edges:
            # Check if this is a conditional branch edge
            if edge.source_output in ["condtrue", "condfalse"]:
                branch_decision = self._branch_decisions.get(edge.source_node_id)

                # Skip if branch doesn't match decision
                if branch_decision and branch_decision != edge.source_output:
                    continue

            required_edges.append(edge)

        return required_edges

    def _evaluate_join_policy(
        self,
        edges: list[EdgeRef],
        node_id: NodeID,
        epoch: int,
        join_policy: str,
    ) -> bool:
        """Evaluate if join policy is satisfied.

        Args:
            edges: Required edges after filtering
            node_id: The node to check
            epoch: The epoch to check
            join_policy: The join policy ("all", "any", etc.)

        Returns:
            True if join policy is satisfied
        """
        return self._policy_evaluator.is_ready(
            policy_type=join_policy,
            edges=edges,
            node_id=node_id,
            epoch=epoch,
        )

    def has_unconsumed_token(self, edge: EdgeRef, node_id: NodeID, epoch: int) -> bool:
        """Check if an edge has an unconsumed token.

        Implements TokenAvailabilityChecker protocol for JoinPolicyEvaluator.

        Args:
            edge: The edge to check
            node_id: The consuming node
            epoch: The epoch to check

        Returns:
            True if there's an unconsumed token on this edge
        """
        return self._token_counter.has_unconsumed(node_id, edge, epoch)
