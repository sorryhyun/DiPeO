#!/usr/bin/env python3
"""Test script to verify Claude Code conversion handles Read/Grep/Bash results correctly."""

import json
from datetime import datetime

from dipeo.domain.cc_translate.models.event import DomainEvent, EventContent, EventType, ToolInfo
from dipeo.domain.cc_translate.models.session import Session
from dipeo.domain.cc_translate.phase_coordinator import PhaseCoordinator

# Create a mock session with Read tool usage
session_data = {
    "uuid": "test-session",
    "name": "Test Session",
    "created_at": datetime.now().isoformat(),
    "updated_at": datetime.now().isoformat(),
    "project_path": "/test/project",
    "conversation": {
        "messages": [
            {
                "uuid": "msg-1",
                "type": "user",
                "content": {"text": "Read the converter.py file"},
                "timestamp": datetime.now().isoformat(),
            },
            {
                "uuid": "msg-2",
                "type": "tool_use",
                "tool_info": {
                    "name": "Read",
                    "input_params": {"file_path": "/path/to/converter.py"},
                },
                "timestamp": datetime.now().isoformat(),
            },
            {
                "uuid": "msg-3",
                "type": "tool_result",
                "tool_info": {"name": "Read", "results": [{"content": "File contents here..."}]},
                "timestamp": datetime.now().isoformat(),
            },
            {
                "uuid": "msg-4",
                "type": "assistant",
                "content": {
                    "text": "I've read the file. Here are the contents:\n\nFile contents here..."
                },
                "timestamp": datetime.now().isoformat(),
            },
            {
                "uuid": "msg-5",
                "type": "user",
                "content": {"text": "Now run ls command"},
                "timestamp": datetime.now().isoformat(),
            },
            {
                "uuid": "msg-6",
                "type": "tool_use",
                "tool_info": {"name": "Bash", "input_params": {"command": "ls -la"}},
                "timestamp": datetime.now().isoformat(),
            },
            {
                "uuid": "msg-7",
                "type": "tool_result",
                "tool_info": {
                    "name": "Bash",
                    "results": [{"content": "total 48\ndrwxr-xr-x  2 user user 4096..."}],
                },
                "timestamp": datetime.now().isoformat(),
            },
            {
                "uuid": "msg-8",
                "type": "assistant",
                "content": {
                    "text": "Here are the directory contents:\n\ntotal 48\ndrwxr-xr-x  2 user user 4096..."
                },
                "timestamp": datetime.now().isoformat(),
            },
        ]
    },
}

# Process the session
coordinator = PhaseCoordinator()
result = coordinator.process_session(session_data)

if result.success:
    print("✅ Conversion successful!")

    # Check the generated diagram
    diagram = result.diagram
    if diagram:
        print(f"\n📊 Generated diagram has {len(diagram.get('nodes', []))} nodes")

        # Look for problematic nodes
        for node in diagram.get("nodes", []):
            if node.get("type") == "person_job":
                props = node.get("props", {})
                prompt = props.get("default_prompt", "")

                # Check if file contents or command output appears in prompts
                if "File contents here" in prompt or "drwxr-xr-x" in prompt:
                    print("\n⚠️  Found tool output in person_job prompt!")
                    print(f"   Node: {node.get('label')}")
                    print(f"   Prompt preview: {prompt[:100]}...")
                else:
                    print(f"\n✅ Node '{node.get('label')}' looks correct")

        # Save the diagram for inspection
        with open("/tmp/test_diagram.yaml", "w") as f:
            import yaml

            yaml.dump(diagram, f, default_flow_style=False)
        print("\n💾 Diagram saved to /tmp/test_diagram.yaml")
else:
    print("❌ Conversion failed!")
    print(f"Errors: {result.errors}")

print("\n🔍 Debug output from conversion should appear above")
