"""Translator for converting Claude Code sessions into DiPeO diagrams."""

import difflib
from typing import Any, Optional

from dipeo.infrastructure.claude_code import ClaudeCodeSession, ConversationTurn, SessionEvent


class ClaudeCodeTranslator:
    """Translates Claude Code sessions into DiPeO light format diagrams."""

    def __init__(self) -> None:
        """Initialize the translator."""
        self.node_counter = 0
        self.nodes: list[dict[str, Any]] = []
        self.connections: list[dict[str, Any]] = []
        self.node_map: dict[str, str] = {}  # Maps event UUID to node label
        self.persons: dict[str, dict[str, Any]] = {}  # AI agent definitions
        self.last_tool_name: Optional[str] = None  # Track the last tool used

    def translate(self, session: ClaudeCodeSession) -> dict[str, Any]:
        """
        Translate a Claude Code session into a light format diagram.

        Args:
            session: Parsed Claude Code session

        Returns:
            Light format diagram dictionary
        """
        self.node_counter = 0
        self.nodes = []
        self.connections = []  # Changed from edges to connections
        self.node_map = {}
        self.persons = {}  # Track AI agents
        self.last_tool_name = None  # Reset tool tracking

        # Create start node
        start_node_label = self._create_start_node(session)

        # Process conversation flow
        conversation_flow = session.get_conversation_flow()
        prev_node_label = start_node_label

        for turn in conversation_flow:
            # Create nodes for this conversation turn
            turn_node_labels = self._process_conversation_turn(turn)

            # Connect to previous node
            if turn_node_labels and prev_node_label:
                self._add_connection(prev_node_label, turn_node_labels[0])

            # Connect nodes within the turn
            for i in range(len(turn_node_labels) - 1):
                self._add_connection(turn_node_labels[i], turn_node_labels[i + 1])

            # Update previous node for next iteration
            if turn_node_labels:
                prev_node_label = turn_node_labels[-1]

        # Build light format diagram
        diagram = self._build_light_diagram()

        return diagram

    def _create_start_node(self, session: ClaudeCodeSession) -> str:
        """Create the start node for the diagram."""
        label = "Start"

        # Extract first user message as the start trigger
        first_user_message = ""
        for event in session.events:
            if event.type == "user":
                if "content" in event.message:
                    first_user_message = self._extract_text_content(event.message["content"])
                    break

        node = {
            "label": label,
            "type": "start",
            "position": {"x": 100, "y": 100},
            "props": {
                "trigger_mode": "manual",
                "custom_data": {
                    "session_id": session.session_id
                    if hasattr(session, "session_id")
                    else "unknown",
                    "initial_prompt": first_user_message[:200]
                    if first_user_message
                    else "Claude Code Session",
                },
            },
        }

        self.nodes.append(node)
        return label

    def _process_conversation_turn(self, turn: ConversationTurn) -> list[str]:
        """Process a conversation turn and create corresponding nodes."""
        node_labels = []

        # Skip user event if this turn has tool events (user event is just showing tool results)
        if turn.user_event and not turn.tool_events:
            user_node_label = self._create_user_node(turn.user_event)
            # Only add the user node if it has meaningful content
            if user_node_label:
                node_labels.append(user_node_label)

        # Process assistant response and tool events
        if turn.assistant_event:
            # Check if there are tool events in this turn
            if turn.tool_events:
                # Create tool nodes for each tool use
                for tool_event in turn.tool_events:
                    tool_node_labels = self._create_tool_nodes(tool_event)
                    node_labels.extend(tool_node_labels)
            else:
                # Create person job node for AI response
                assistant_node_label = self._create_assistant_node(turn.assistant_event)
                node_labels.append(assistant_node_label)

        return node_labels

    def _create_user_node(self, event: SessionEvent) -> str | None:
        """Create a node for user input, or None if no meaningful input."""
        # Skip tool results in user messages - they flow through connections
        content = self._extract_text_content(
            event.message.get("content", ""), skip_read_results=True
        )

        # Skip creating node if content is empty or just whitespace after filtering tool results
        if not content or not content.strip():
            return None

        label = f"User Input {self.node_counter + 1}"
        self.node_counter += 1

        # Register user person if not exists
        if "user" not in self.persons:
            self.persons["user"] = {
                "service": "openai",
                "model": "user",
                "api_key_id": "USER_INPUT",
            }

        node = {
            "label": label,
            "type": "person_job",
            "position": {
                "x": 300 + (self.node_counter * 50) % 800,
                "y": 100 + (self.node_counter // 10) * 150,
            },
            "props": {
                "person": "user",
                "default_prompt": content,
                "max_iteration": 1,
            },
        }

        self.nodes.append(node)
        self.node_map[event.uuid] = label
        return label

    def _create_assistant_node(self, event: SessionEvent) -> str:
        """Create a node for AI assistant response."""
        label = f"Claude Response {self.node_counter + 1}"
        self.node_counter += 1

        # Skip Read tool results in assistant responses - they flow through db node connections
        content = self._extract_text_content(
            event.message.get("content", ""), skip_read_results=True
        )

        # Register Claude person if not exists
        if "claude_code" not in self.persons:
            self.persons["claude_code"] = {
                "service": "anthropic",
                "model": "claude-code",
                "api_key_id": "APIKEY_CLAUDE",
                "system_prompt": "You are Claude Code, an AI assistant helping with software development.",
            }

        node = {
            "label": label,
            "type": "person_job",
            "position": {
                "x": 300 + (self.node_counter * 50) % 800,
                "y": 100 + (self.node_counter // 10) * 150,
            },
            "props": {
                "person": "claude_code",
                "default_prompt": f"Process and respond: {content[:200]}",
                "max_iteration": 1,
            },
        }

        self.nodes.append(node)
        self.node_map[event.uuid] = label
        return label

    def _create_tool_nodes(self, event: SessionEvent) -> list[str]:
        """Create nodes for tool usage."""
        node_labels = []

        tool_name = event.tool_name
        tool_input = event.tool_input or {}

        # Track the tool being used
        self.last_tool_name = tool_name

        # Map tool to appropriate node type
        node_label = None
        if tool_name:
            if tool_name == "Read":
                node_label = self._create_read_node(tool_input)
            elif tool_name == "Write":
                node_label = self._create_write_node(tool_input)
            elif tool_name in ["Edit", "MultiEdit"]:
                node_label = self._create_edit_node(tool_name, tool_input)
            elif tool_name == "Bash":
                node_label = self._create_bash_node(tool_input)
            elif tool_name == "TodoWrite":
                node_label = self._create_todo_node(tool_input)
            elif tool_name in ["Glob", "Grep"]:
                node_label = self._create_search_node(tool_name, tool_input)
            else:
                # Generic API node for other tools
                node_label = self._create_generic_tool_node(tool_name, tool_input)

        if node_label:
            node_labels.append(node_label)
            self.node_map[event.uuid] = node_label

        return node_labels

    def _create_read_node(self, tool_input: dict[str, Any]) -> str:
        """Create a DB node for file read operation."""
        label = f"Read File {self.node_counter + 1}"
        self.node_counter += 1

        file_path = tool_input.get("file_path", "unknown")

        node = {
            "label": label,
            "type": "db",
            "position": {
                "x": 300 + (self.node_counter * 50) % 800,
                "y": 100 + (self.node_counter // 10) * 150,
            },
            "props": {"operation": "read", "sub_type": "file", "file": file_path},
        }

        self.nodes.append(node)
        return label

    def _create_write_node(self, tool_input: dict[str, Any]) -> str:
        """Create a DB node for file write operation."""
        label = f"Write File {self.node_counter + 1}"
        self.node_counter += 1

        file_path = tool_input.get("file_path", "unknown")
        content = tool_input.get("content", "")

        node = {
            "label": label,
            "type": "db",
            "position": {
                "x": 300 + (self.node_counter * 50) % 800,
                "y": 100 + (self.node_counter // 10) * 150,
            },
            "props": {
                "operation": "write",
                "sub_type": "file",
                "file": file_path,
                "content": content[:1000],  # Store some content for context
            },
        }

        self.nodes.append(node)
        return label

    def _create_edit_node(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        """Create a diff_patch node for file edit operation."""
        label = f"{tool_name} File {self.node_counter + 1}"
        self.node_counter += 1

        file_path = tool_input.get("file_path", "unknown")

        # Generate unified diff from old_string and new_string
        if tool_name == "Edit":
            old_string = tool_input.get("old_string", "")
            new_string = tool_input.get("new_string", "")
            diff_content = self._generate_unified_diff(file_path, old_string, new_string)
        elif tool_name == "MultiEdit":
            # For MultiEdit, combine all edits into a single diff
            edits = tool_input.get("edits", [])
            diff_content = self._generate_multiedit_diff(file_path, edits)
        else:
            # Fallback for unknown edit types
            diff_content = "# Unable to generate diff"

        node = {
            "label": label,
            "type": "diff_patch",
            "position": {
                "x": 300 + (self.node_counter * 50) % 800,
                "y": 100 + (self.node_counter // 10) * 150,
            },
            "props": {
                "target_path": file_path,
                "diff": diff_content,
                "format": "unified",
                "backup": True,
                "validate": True,
            },
        }

        self.nodes.append(node)
        return label

    def _create_bash_node(self, tool_input: dict[str, Any]) -> str:
        """Create a code_job node for bash command execution."""
        label = f"Bash Command {self.node_counter + 1}"
        self.node_counter += 1

        command = tool_input.get("command", "")
        description = tool_input.get("description", "Execute command")

        node = {
            "label": label,
            "type": "code_job",
            "position": {
                "x": 300 + (self.node_counter * 50) % 800,
                "y": 100 + (self.node_counter // 10) * 150,
            },
            "props": {
                "language": "bash",
                "code": command,
                "timeout": tool_input.get("timeout", 120000),
                "description": description,
            },
        }

        self.nodes.append(node)
        return label

    def _create_todo_node(self, tool_input: dict[str, Any]) -> str:
        """Create a DB node for TodoWrite operation."""
        label = f"Update TODO {self.node_counter + 1}"
        self.node_counter += 1

        todos = tool_input.get("todos", [])

        node = {
            "label": label,
            "type": "db",
            "position": {
                "x": 300 + (self.node_counter * 50) % 800,
                "y": 100 + (self.node_counter // 10) * 150,
            },
            "props": {
                "operation": "write",
                "sub_type": "memory",
                "query": "UPDATE TODO LIST",
                "data": {"todos": todos},
            },
        }

        self.nodes.append(node)
        return label

    def _create_search_node(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        """Create a code_job node for search operations."""
        label = f"{tool_name} Search {self.node_counter + 1}"
        self.node_counter += 1

        pattern = tool_input.get("pattern", "") or tool_input.get("query", "")

        node = {
            "label": label,
            "type": "code_job",
            "position": {
                "x": 300 + (self.node_counter * 50) % 800,
                "y": 100 + (self.node_counter // 10) * 150,
            },
            "props": {
                "language": "python",
                "code": f"# {tool_name} search\npattern = '{pattern}'\n# Search parameters: {tool_input}",
                "tool": tool_name,
            },
        }

        self.nodes.append(node)
        return label

    def _create_generic_tool_node(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        """Create a generic API node for unknown tools."""
        label = f"{tool_name} {self.node_counter + 1}"
        self.node_counter += 1

        node = {
            "label": label,
            "type": "api_job",
            "position": {
                "x": 300 + (self.node_counter * 50) % 800,
                "y": 100 + (self.node_counter // 10) * 150,
            },
            "props": {
                "endpoint": f"/tools/{tool_name}",
                "method": "POST",
                "body": tool_input,
                "timeout": 30,
            },
        }

        self.nodes.append(node)
        return label

    def _add_connection(
        self, source: str, target: str, content_type: str = "raw_text", label: str = ""
    ) -> None:
        """Add a connection between two nodes in light format."""
        connection = {"from": source, "to": target, "content_type": content_type}
        if label:
            connection["label"] = label
        self.connections.append(connection)

    def _build_light_diagram(self) -> dict[str, Any]:
        """Build the light format diagram structure."""
        # Build the light format diagram
        diagram = {"version": "light"}

        # Add nodes
        if self.nodes:
            diagram["nodes"] = self.nodes

        # Add connections
        if self.connections:
            diagram["connections"] = self.connections

        # Add persons section if we have AI agents
        if self.persons:
            diagram["persons"] = self.persons

        return diagram

    def _extract_text_content(self, content: Any, skip_read_results: bool = False) -> str:
        """Extract text content from various content formats.

        Args:
            content: The content to extract text from
            skip_read_results: If True, skip tool_result content from Read operations
        """
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                    elif item.get("type") == "tool_result":
                        # Skip tool results for execution/operation tools when processing user input
                        tools_to_skip = {
                            "Read",
                            "Bash",
                            "Write",
                            "Edit",
                            "MultiEdit",
                            "Glob",
                            "Grep",
                        }
                        if skip_read_results and self.last_tool_name in tools_to_skip:
                            pass  # Skip these tool results in user input nodes
                        else:
                            # Include other tool results (like WebFetch, Task, etc.) in the content
                            result_content = item.get("content", "")
                            if result_content:
                                text_parts.append(result_content)
                    elif "content" in item:
                        text_parts.append(
                            self._extract_text_content(item["content"], skip_read_results)
                        )
                elif isinstance(item, str):
                    text_parts.append(item)
            return " ".join(text_parts)

        if isinstance(content, dict):
            if "text" in content:
                return str(content["text"])
            if "content" in content:
                return self._extract_text_content(content["content"], skip_read_results)

        return str(content)

    def _generate_unified_diff(self, file_path: str, old_content: str, new_content: str) -> str:
        """Generate a unified diff from old and new content strings."""
        # Split content into lines for difflib (without keeping line endings)
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()

        # Generate unified diff
        diff_lines = list(
            difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=file_path,
                tofile=file_path,
                n=3,  # Context lines
            )
        )

        # Join the diff lines
        if diff_lines:
            return "\n".join(diff_lines)
        else:
            # No differences found
            return f"# No differences found in {file_path}"

    def _generate_multiedit_diff(self, file_path: str, edits: list[dict[str, Any]]) -> str:
        """Generate a unified diff from multiple edit operations."""
        if not edits:
            return f"# No edits provided for {file_path}"

        # For MultiEdit, we need to apply edits sequentially
        # Since we don't have the original file content, we'll create individual diffs
        # and combine them with comments

        diff_sections = []
        diff_sections.append(f"# MultiEdit diff for {file_path}")
        diff_sections.append(f"# Total edits: {len(edits)}")
        diff_sections.append("")

        for i, edit in enumerate(edits, 1):
            old_string = edit.get("old_string", "")
            new_string = edit.get("new_string", "")

            diff_sections.append(f"# Edit {i}/{len(edits)}")

            # Generate diff for this specific edit
            edit_diff = self._generate_unified_diff(file_path, old_string, new_string)
            diff_sections.append(edit_diff)
            diff_sections.append("")  # Add blank line between edits

        return "\n".join(diff_sections)
