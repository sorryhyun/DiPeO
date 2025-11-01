"""Diagram query and listing functionality."""

import json
import re
from pathlib import Path

from dipeo.application.bootstrap import Container
from dipeo.application.registry.keys import STATE_STORE
from dipeo.config import STATE_DB_PATH
from dipeo.config.base_logger import get_module_logger
from dipeo.infrastructure.storage.message_store import MessageStore

logger = get_module_logger(__name__)


class DiagramQuery:
    """Handles diagram querying and listing operations."""

    def __init__(self, container: Container):
        self.container = container
        self.registry = container.registry

    async def get_results_data(self, session_id: str, verbose: bool = False) -> dict:
        """Get execution results data as a dictionary.

        Args:
            session_id: Execution/session ID (format: exec_[32-char-hex])
            verbose: If True, include detailed output with full conversation and metadata

        Returns:
            Dictionary with results data or error information
        """
        try:
            if not re.match(r"^exec_[0-9a-f]{32}$", session_id):
                return {
                    "error": f"Invalid session_id format: {session_id}",
                    "expected_format": "exec_[32-char-hex]",
                }

            state_store = self.registry.resolve(STATE_STORE)
            result = await state_store.get_execution(session_id)

            if not result:
                return {"error": f"Execution not found: {session_id}", "session_id": session_id}

            response = {
                "session_id": session_id,
                "status": result.status.value
                if hasattr(result.status, "value")
                else str(result.status),
            }

            if hasattr(result, "diagram_id") and result.diagram_id:
                response["diagram_id"] = result.diagram_id

            if hasattr(result, "error") and result.error:
                response["error"] = result.error

            if verbose:
                if hasattr(result, "executed_nodes") and result.executed_nodes:
                    response["executed_nodes"] = result.executed_nodes

                if hasattr(result, "node_outputs") and result.node_outputs:
                    response["node_outputs"] = self._extract_node_outputs(result.node_outputs)

                if hasattr(result, "started_at") and result.started_at:
                    response["started_at"] = (
                        result.started_at.isoformat()
                        if hasattr(result.started_at, "isoformat")
                        else str(result.started_at)
                    )
                if hasattr(result, "ended_at") and result.ended_at:
                    response["ended_at"] = (
                        result.ended_at.isoformat()
                        if hasattr(result.ended_at, "isoformat")
                        else str(result.ended_at)
                    )

                try:
                    message_store = MessageStore(STATE_DB_PATH)
                    await message_store.initialize()
                    messages = await message_store.get_execution_messages(session_id)
                    if messages:
                        response["conversation"] = self._format_conversation(messages)
                except Exception as e:
                    logger.debug(f"Could not retrieve messages: {e}")
            else:
                if hasattr(result, "executed_nodes") and result.executed_nodes:
                    response["executed_nodes_count"] = len(result.executed_nodes)

                if hasattr(result, "node_outputs") and result.node_outputs:
                    outputs = self._extract_node_outputs(result.node_outputs)
                    final_output = None
                    if hasattr(result, "executed_nodes") and result.executed_nodes:
                        for node_id in reversed(result.executed_nodes):
                            if node_id in outputs and node_id.startswith("endpoint"):
                                final_output = outputs[node_id]
                                break
                        if not final_output and result.executed_nodes:
                            last_node = result.executed_nodes[-1]
                            final_output = outputs.get(last_node)

                    if final_output:
                        response["final_output"] = final_output

                try:
                    message_store = MessageStore(STATE_DB_PATH)
                    await message_store.initialize()
                    messages = await message_store.get_execution_messages(session_id)
                    if messages:
                        response["messages_count"] = len(messages)
                        last_msg = messages[-1]
                        formatted = self._format_conversation([last_msg])
                        if formatted:
                            response["last_message"] = formatted[0]
                except Exception as e:
                    logger.debug(f"Could not retrieve messages: {e}")

            if hasattr(result, "llm_usage") and result.llm_usage:
                response["llm_usage"] = {
                    "input_tokens": result.llm_usage.input
                    if hasattr(result.llm_usage, "input")
                    else 0,
                    "output_tokens": result.llm_usage.output
                    if hasattr(result.llm_usage, "output")
                    else 0,
                    "total_tokens": result.llm_usage.total
                    if hasattr(result.llm_usage, "total")
                    else 0,
                }

            return response

        except Exception as e:
            logger.error(f"Failed to query execution results: {e}")
            return {"error": f"Failed to query execution: {e!s}", "session_id": session_id}

    async def show_results(self, session_id: str, verbose: bool = False) -> bool:
        """Query execution status and results by session_id.

        Args:
            session_id: Execution/session ID (format: exec_[32-char-hex])
            verbose: If True, show detailed output with full conversation and metadata

        Returns:
            True if query succeeded, False otherwise
        """
        response = await self.get_results_data(session_id, verbose)
        print(json.dumps(response, indent=2))
        return "error" not in response or response.get("error") is None

    async def list_diagrams(
        self, output_json: bool = False, format_filter: str | None = None
    ) -> bool:
        """List available diagrams in projects/ and examples/simple_diagrams/."""
        try:
            from dipeo.config import BASE_DIR

            diagrams = []

            scan_dirs = [
                BASE_DIR / "projects",
                BASE_DIR / "examples" / "simple_diagrams",
            ]

            for base_dir in scan_dirs:
                if not base_dir.exists():
                    continue

                for ext in [".light.yaml", ".light.yml", ".yaml", ".yml", ".json"]:
                    for diagram_file in base_dir.rglob(f"*{ext}"):
                        if ".light." in diagram_file.name:
                            detected_format = "light"
                        elif diagram_file.suffix == ".json":
                            detected_format = "native"
                        else:
                            detected_format = "readable"

                        if format_filter and detected_format != format_filter:
                            continue

                        node_count = None
                        description = None
                        try:
                            import yaml

                            with open(diagram_file, encoding="utf-8") as f:
                                if diagram_file.suffix == ".json":
                                    data = json.load(f)
                                else:
                                    data = yaml.safe_load(f)

                                if isinstance(data, dict):
                                    if "nodes" in data:
                                        node_count = len(data["nodes"])

                                    if "metadata" in data and isinstance(data["metadata"], dict):
                                        description = data["metadata"].get("description")
                        except Exception:
                            pass

                        diagrams.append(
                            {
                                "name": diagram_file.stem,
                                "path": str(diagram_file.relative_to(BASE_DIR)),
                                "format": detected_format,
                                "nodes": node_count,
                                "description": description,
                            }
                        )

            diagrams.sort(key=lambda d: d["path"])

            if output_json:
                print(json.dumps({"diagrams": diagrams}, indent=2))
            else:
                if not diagrams:
                    print("No diagrams found in projects/ or examples/simple_diagrams/")
                    return True

                print(f"Found {len(diagrams)} diagram(s):\n")
                for d in diagrams:
                    print(f"  {d['name']}")
                    print(f"    Path:   {d['path']}")
                    print(f"    Format: {d['format']}")
                    if d["nodes"] is not None:
                        print(f"    Nodes:  {d['nodes']}")
                    if d["description"]:
                        print(f"    Desc:   {d['description']}")
                    print()

            return True

        except Exception as e:
            logger.error(f"Failed to list diagrams: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _extract_node_outputs(self, node_outputs: dict) -> dict:
        """Extract meaningful content from node outputs.

        Args:
            node_outputs: Raw node outputs with envelopes

        Returns:
            Dict mapping node IDs to extracted content
        """
        extracted = {}
        for node_id, output in node_outputs.items():
            try:
                if isinstance(output, dict):
                    if "body" in output:
                        extracted[node_id] = output["body"]
                    elif "content" in output:
                        extracted[node_id] = output["content"]
                    else:
                        extracted[node_id] = output
                else:
                    extracted[node_id] = str(output)
            except Exception:
                extracted[node_id] = str(output)
        return extracted

    def _format_conversation(self, messages: list[dict]) -> list[dict]:
        """Format conversation messages for display.

        Args:
            messages: List of message dicts with id, node_id, person_id, content, token_count, timestamp

        Returns:
            List of formatted message dicts
        """
        formatted = []
        for msg in messages:
            content = msg.get("content", {})
            role = "unknown"
            text = ""

            if isinstance(content, dict):
                role = content.get("role", "unknown")
                if "content" in content:
                    text = content["content"]
                elif "text" in content:
                    text = content["text"]
                else:
                    text = str(content)
            else:
                text = str(content)

            formatted.append(
                {
                    "role": role,
                    "content": text,
                    "node_id": msg.get("node_id"),
                    "timestamp": msg.get("timestamp"),
                }
            )

        return formatted
