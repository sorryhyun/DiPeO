"""GraphQL queries for CLI commands.

This module contains all GraphQL queries and mutations used by the CLI,
loaded from separate query files or defined as constants.
"""

from pathlib import Path


class GraphQLQueries:
    """Container for GraphQL queries used by the CLI."""

    # Mutations
    EXECUTE_DIAGRAM = """
        mutation ExecuteDiagram($diagramId: ID, $diagramData: JSON, $variables: JSON, $useUnifiedMonitoring: Boolean) {
            execute_diagram(input: {
                diagram_id: $diagramId,
                diagram_data: $diagramData,
                variables: $variables,
                use_unified_monitoring: $useUnifiedMonitoring
            }) {
                success
                execution_id
                error
            }
        }
    """

    REGISTER_CLI_SESSION = """
        mutation RegisterCliSession($executionId: String!, $diagramName: String!, $diagramFormat: String!, $diagramData: JSON, $diagramPath: String) {
            register_cli_session(input: {
                execution_id: $executionId,
                diagram_name: $diagramName,
                diagram_format: $diagramFormat,
                diagram_data: $diagramData,
                diagram_path: $diagramPath
            }) {
                success
                error
            }
        }
    """

    UNREGISTER_CLI_SESSION = """
        mutation UnregisterCliSession($executionId: String!) {
            unregister_cli_session(input: { execution_id: $executionId }) {
                success
            }
        }
    """

    # Queries
    GET_EXECUTION_RESULT = """
        query GetExecutionResult($id: ID!) {
            execution(id: $id) {
                status
                node_outputs
                error
            }
        }
    """

    GET_EXECUTION_METRICS = """
        query GetExecutionMetrics($id: ID!) {
            execution(id: $id) {
                status
                metrics
                token_usage {
                    input
                    output
                    cached
                    total
                }
                node_states
                error
            }
        }
    """

    EXECUTION_METRICS_DETAILED = """
        query ExecutionMetrics($executionId: ID!) {
            execution(id: $executionId) {
                id
                status
                diagramId
                startedAt
                endedAt
                durationSeconds
                nodeStates
                tokenUsage {
                    input
                    output
                    cached
                    total
                }
                metrics
                error
            }
        }
    """

    EXECUTION_HISTORY = """
        query ExecutionHistory($diagramId: ID!, $includeMetrics: Boolean!) {
            executionHistory(diagramId: $diagramId, limit: 10, includeMetrics: $includeMetrics) {
                id
                status
                startedAt
                endedAt
                durationSeconds
                tokenUsage {
                    input
                    output
                    cached
                    total
                }
                metrics @include(if: $includeMetrics)
            }
        }
    """

    LATEST_EXECUTION = """
        query LatestExecution {
            executions(limit: 1) {
                id
                status
                diagramId
                startedAt
                endedAt
                durationSeconds
                nodeStates
                tokenUsage {
                    input
                    output
                    cached
                    total
                }
                metrics
            }
        }
    """

    @classmethod
    def load_from_file(cls, query_name: str, queries_dir: Path | None = None) -> str:
        """Load a GraphQL query from a file.

        Args:
            query_name: Name of the query file (without .graphql extension)
            queries_dir: Directory containing query files (defaults to ./queries)

        Returns:
            The GraphQL query string
        """
        if queries_dir is None:
            queries_dir = Path(__file__).parent / "queries"

        query_file = queries_dir / f"{query_name}.graphql"

        if query_file.exists():
            return query_file.read_text()

        # Fallback to class attribute if file doesn't exist
        return getattr(cls, query_name.upper(), None)

    @classmethod
    def get_all_queries(cls) -> dict[str, str]:
        """Get all available queries as a dictionary."""
        return {
            "execute_diagram": cls.EXECUTE_DIAGRAM,
            "register_cli_session": cls.REGISTER_CLI_SESSION,
            "unregister_cli_session": cls.UNREGISTER_CLI_SESSION,
            "get_execution_result": cls.GET_EXECUTION_RESULT,
            "get_execution_metrics": cls.GET_EXECUTION_METRICS,
            "execution_metrics_detailed": cls.EXECUTION_METRICS_DETAILED,
            "execution_history": cls.EXECUTION_HISTORY,
            "latest_execution": cls.LATEST_EXECUTION,
        }
