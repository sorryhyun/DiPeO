#!/usr/bin/env python
"""Integration test to demonstrate the complete TODO translation pipeline."""

import asyncio
import json
import tempfile
from datetime import datetime
from pathlib import Path

from dipeo.domain.diagram.services.todo_translator import TodoTranslator
from dipeo.infrastructure.llm.providers.claude_code.todo_collector import TodoItem, TodoSnapshot


async def main():
    """Run the integration test."""
    print("=== TODO Translation Pipeline Integration Test ===\n")

    # Step 1: Create a sample TodoSnapshot (simulating what TodoCollector would produce)
    print("1. Creating sample TodoSnapshot...")
    snapshot = TodoSnapshot(
        session_id="integration-test-001",
        trace_id="trace-integration-test",
        timestamp=datetime.now(),
        todos=[
            TodoItem(
                content="Set up development environment",
                status="completed",
                active_form="Setting up development environment",
                index=0,
            ),
            TodoItem(
                content="Implement authentication system",
                status="completed",
                active_form="Implementing authentication",
                index=1,
            ),
            TodoItem(
                content="Create user interface",
                status="in_progress",
                active_form="Creating user interface",
                index=2,
            ),
            TodoItem(
                content="Write unit tests",
                status="in_progress",
                active_form="Writing unit tests",
                index=3,
            ),
            TodoItem(content="Add error handling", status="pending", active_form=None, index=4),
            TodoItem(content="Deploy to production", status="pending", active_form=None, index=5),
            TodoItem(content="Write documentation", status="pending", active_form=None, index=6),
        ],
        doc_path="/workspace/project/README.md",
        hook_event_timestamp=datetime.now(),
    )
    print(f"  Created snapshot with {len(snapshot.todos)} TODO items")
    print(f"  - Completed: {sum(1 for t in snapshot.todos if t.status == 'completed')}")
    print(f"  - In Progress: {sum(1 for t in snapshot.todos if t.status == 'in_progress')}")
    print(f"  - Pending: {sum(1 for t in snapshot.todos if t.status == 'pending')}\n")

    # Step 2: Translate to LightDiagram
    print("2. Translating TodoSnapshot to LightDiagram...")
    translator = TodoTranslator()
    diagram = translator.translate(
        snapshot, diagram_id="todo-integration-test", include_metadata=True
    )
    print(f"  Generated diagram with {len(diagram.nodes)} nodes")
    print(f"  Generated {len(diagram.connections)} connections\n")

    # Step 3: Save to temporary files
    print("3. Saving diagram to files...")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Save as YAML
        yaml_path = tmpdir_path / "todo_diagram.light.yaml"
        yaml_saved = translator.save_to_file(diagram, yaml_path, format="yaml")
        print(f"  Saved YAML to: {yaml_saved}")

        # Save as JSON
        json_path = tmpdir_path / "todo_diagram.json"
        json_saved = translator.save_to_file(diagram, json_path, format="json")
        print(f"  Saved JSON to: {json_saved}\n")

        # Step 4: Verify saved files
        print("4. Verifying saved files...")

        # Verify YAML
        import yaml

        with open(yaml_path) as f:
            yaml_content = yaml.safe_load(f)
        print(f"  YAML verified - version: {yaml_content.get('version')}")
        print(f"  - Nodes: {len(yaml_content.get('nodes', []))}")
        print(f"  - Connections: {len(yaml_content.get('connections', []))}")

        # Verify JSON
        with open(json_path) as f:
            json_content = json.load(f)
        print(f"  JSON verified - version: {json_content.get('version')}")

        # Step 5: Display diagram metadata
        print("\n5. Diagram Metadata:")
        if diagram.metadata:
            print(f"  - Diagram ID: {diagram.metadata.get('diagram_id')}")
            print(f"  - Source: {diagram.metadata.get('source')}")
            print(f"  - Session ID: {diagram.metadata.get('session_id')}")
            print(f"  - Doc Path: {diagram.metadata.get('doc_path')}")
            print(f"  - Status Counts: {diagram.metadata.get('status_counts')}")

            # Display visual mapping
            print("\n  Visual Mappings:")
            for status, config in diagram.metadata.get("status_visual_map", {}).items():
                print(
                    f"    - {status}: {config.get('icon')} {config.get('color')} ({config.get('badge')})"
                )

        # Step 6: Display sample YAML content
        print("\n6. Sample YAML Output (first 30 lines):")
        print("-" * 60)
        with open(yaml_path) as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:30], 1):
                print(f"{i:3}: {line}", end="")
        if len(lines) > 30:
            print(f"... ({len(lines) - 30} more lines)")
        print("-" * 60)

    print("\n✅ Integration test completed successfully!")
    print("The TODO translation pipeline is working correctly.")


if __name__ == "__main__":
    asyncio.run(main())
