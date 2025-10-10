"""Convert DiPeO diagrams to standalone Python scripts."""

import json
from pathlib import Path
from typing import Any

from dipeo.diagram_generated.domain_models import DomainDiagram
from dipeo.diagram_generated.unified_nodes import (
    CodeJobNode,
    ConditionNode,
    DbNode,
    EndpointNode,
    PersonJobNode,
    StartNode,
    SubDiagramNode,
)


class PythonExporter:
    """Exports DiPeO diagrams to standalone Python scripts.

    Supports simplified export focusing on:
    - LLM calls (person_job nodes)
    - DB read/write (db nodes)
    - Code execution (code_job nodes)
    - Control flow (condition, start, endpoint)

    Does not include DB state management or monitor logic.
    """

    def __init__(self):
        self.imports = set()
        self.init_code = []
        self.main_code = []
        self.node_outputs = {}
        self.visited_nodes = set()

    def export(self, diagram: DomainDiagram, output_path: str) -> bool:
        """Export diagram to Python script.

        Args:
            diagram: The domain diagram to export
            output_path: Path to write the Python script

        Returns:
            True if export successful, False otherwise
        """
        try:
            # Reset state
            self.imports = {"import asyncio"}
            self.init_code = []
            self.main_code = []
            self.node_outputs = {}
            self.visited_nodes = set()

            # Find start node
            start_nodes = [n for n in diagram.nodes if n.type == "start"]
            if not start_nodes:
                print("❌ No start node found in diagram")
                return False

            # Build node execution order
            execution_order = self._build_execution_order(diagram, start_nodes[0])

            # Generate code for each node
            for node in execution_order:
                self._generate_node_code(node, diagram)

            # Build final script
            script = self._build_script(diagram)

            # Write to file
            Path(output_path).write_text(script)
            print(f"✅ Exported diagram to {output_path}")
            return True

        except Exception as e:
            print(f"❌ Export failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _build_execution_order(self, diagram: DomainDiagram, start_node) -> list:
        """Build execution order by following arrows from start node."""
        order = []
        to_visit = [start_node]
        visited = set()

        while to_visit:
            node = to_visit.pop(0)
            if node.id in visited:
                continue

            visited.add(node.id)
            order.append(node)

            # Find outgoing arrows
            outgoing = [a for a in diagram.arrows if a.source == node.id]
            for arrow in outgoing:
                target_node = next((n for n in diagram.nodes if n.id == arrow.target), None)
                if target_node and target_node.id not in visited:
                    to_visit.append(target_node)

        return order

    def _generate_node_code(self, node, diagram: DomainDiagram):
        """Generate code for a specific node."""
        node_type = node.type

        if node_type == "start":
            self._generate_start_code(node)
        elif node_type == "code_job":
            self._generate_code_job(node)
        elif node_type == "person_job":
            self._generate_person_job(node, diagram)
        elif node_type == "condition":
            self._generate_condition(node, diagram)
        elif node_type == "endpoint":
            self._generate_endpoint(node)
        elif node_type == "db":
            self._generate_db(node)
        elif node_type == "sub_diagram":
            self._generate_sub_diagram(node, diagram)
        else:
            self.main_code.append(f"    # TODO: Unsupported node type: {node_type}")

    def _generate_start_code(self, node):
        """Generate code for start node."""
        label = getattr(node, "label", "Start")
        self.main_code.append(f"    # {label}")
        self.main_code.append('    print("Starting execution...")')
        self.main_code.append("")

    def _generate_code_job(self, node: CodeJobNode):
        """Generate code for code_job node."""
        label = getattr(node, "label", "Code Job")
        code = node.code or ""

        self.main_code.append(f"    # {label}")

        # Add code lines with proper indentation
        for line in code.split("\n"):
            if line.strip():
                self.main_code.append(f"    {line}")

        self.main_code.append("")

    def _generate_person_job(self, node: PersonJobNode, diagram: DomainDiagram):
        """Generate code for person_job node (LLM calls)."""
        label = getattr(node, "label", "Person Job")
        person_id = node.person

        # Find person config
        person = next((p for p in diagram.persons if p.id == person_id), None)
        if not person:
            self.main_code.append(f"    # {label} - ERROR: Person config not found")
            return

        service = person.service.lower() if hasattr(person.service, 'lower') else str(person.service).lower()
        model = person.model

        # Add appropriate imports
        if "openai" in service or "gpt" in model.lower():
            self.imports.add("from openai import AsyncOpenAI")
            client_var = "openai_client"
            if client_var not in [line.split("=")[0].strip() for line in self.init_code]:
                self.init_code.append(f'    {client_var} = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))')
        elif "anthropic" in service or "claude" in model.lower():
            self.imports.add("from anthropic import AsyncAnthropic")
            client_var = "anthropic_client"
            if client_var not in [line.split("=")[0].strip() for line in self.init_code]:
                self.init_code.append(f'    {client_var} = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))')
        else:
            self.main_code.append(f"    # {label} - Unsupported service: {service}")
            return

        self.imports.add("import os")

        # Get prompt
        prompt = getattr(node, "default_prompt", "")
        if not prompt:
            prompt = getattr(node, "resolved_prompt", "")

        self.main_code.append(f"    # {label}")

        # Generate LLM call
        if "openai" in service or "gpt" in model.lower():
            self.main_code.append(f"    response = await {client_var}.chat.completions.create(")
            self.main_code.append(f'        model="{model}",')
            self.main_code.append(f"        messages=[")
            self.main_code.append(f'            {{"role": "user", "content": {repr(prompt)}}}')
            self.main_code.append(f"        ]")
            self.main_code.append(f"    )")
            var_name = self._node_var_name(node)
            self.main_code.append(f"    {var_name} = response.choices[0].message.content")
        elif "anthropic" in service or "claude" in model.lower():
            self.main_code.append(f"    response = await {client_var}.messages.create(")
            self.main_code.append(f'        model="{model}",')
            self.main_code.append(f'        max_tokens=1024,')
            self.main_code.append(f"        messages=[")
            self.main_code.append(f'            {{"role": "user", "content": {repr(prompt)}}}')
            self.main_code.append(f"        ]")
            self.main_code.append(f"    )")
            var_name = self._node_var_name(node)
            self.main_code.append(f"    {var_name} = response.content[0].text")

        self.main_code.append("")
        self.node_outputs[node.id] = var_name

    def _generate_condition(self, node: ConditionNode, diagram: DomainDiagram):
        """Generate code for condition node."""
        label = getattr(node, "label", "Condition")
        condition_type = node.condition_type

        self.main_code.append(f"    # {label}")

        if condition_type == "custom":
            expression = node.expression or "True"
            self.main_code.append(f"    if {expression}:")

            # Find condtrue and condfalse paths
            condtrue_arrows = [a for a in diagram.arrows if a.source == f"{node.id}_condtrue"]
            condfalse_arrows = [a for a in diagram.arrows if a.source == f"{node.id}_condfalse"]

            if condtrue_arrows:
                self.main_code.append(f"        # condtrue path")
                self.main_code.append(f"        pass  # Continue to next node")

            if condfalse_arrows:
                self.main_code.append(f"    else:")
                self.main_code.append(f"        # condfalse path")
                self.main_code.append(f"        pass  # Loop back or alternative path")
        else:
            self.main_code.append(f"    # TODO: Condition type '{condition_type}' not yet supported")

        self.main_code.append("")

    def _generate_endpoint(self, node: EndpointNode):
        """Generate code for endpoint node."""
        label = getattr(node, "label", "Endpoint")
        save_to_file = getattr(node, "save_to_file", False)
        file_path = getattr(node, "file_path", "output.txt")

        self.main_code.append(f"    # {label}")

        if save_to_file:
            self.imports.add("from pathlib import Path")
            self.main_code.append(f"    # Save result to file")
            self.main_code.append(f'    output_path = Path("{file_path}")')
            self.main_code.append(f"    output_path.parent.mkdir(parents=True, exist_ok=True)")

            # Find what to save (last node output or 'result' variable)
            if self.node_outputs:
                last_output = list(self.node_outputs.values())[-1]
                self.main_code.append(f"    output_path.write_text(str({last_output}))")
            else:
                self.main_code.append(f"    output_path.write_text(str(result))")

            self.main_code.append(f'    print(f"✅ Saved output to {{output_path}}")')
        else:
            self.main_code.append(f"    # Output endpoint")
            if self.node_outputs:
                last_output = list(self.node_outputs.values())[-1]
                self.main_code.append(f'    print(f"✅ Result: {{{last_output}}}")')

        self.main_code.append("")

    def _generate_db(self, node: DbNode):
        """Generate code for db node (file operations)."""
        label = getattr(node, "label", "DB")
        operation = node.operation
        file_paths = node.file if isinstance(node.file, list) else [node.file]

        self.main_code.append(f"    # {label}")
        self.imports.add("from pathlib import Path")

        if operation == "read":
            for file_path in file_paths:
                var_name = self._node_var_name(node)
                self.main_code.append(f'    {var_name} = Path("{file_path}").read_text()')
                self.node_outputs[node.id] = var_name
        elif operation == "write":
            for file_path in file_paths:
                # Determine what to write
                if self.node_outputs:
                    last_output = list(self.node_outputs.values())[-1]
                    content_var = last_output
                else:
                    content_var = "content"

                self.main_code.append(f'    db_path = Path("{file_path}")')
                self.main_code.append(f"    db_path.parent.mkdir(parents=True, exist_ok=True)")
                self.main_code.append(f"    db_path.write_text(str({content_var}))")
        elif operation == "append":
            for file_path in file_paths:
                if self.node_outputs:
                    last_output = list(self.node_outputs.values())[-1]
                    content_var = last_output
                else:
                    content_var = "content"

                self.main_code.append(f'    with open("{file_path}", "a") as f:')
                self.main_code.append(f"        f.write(str({content_var}))")

        self.main_code.append("")

    def _generate_sub_diagram(self, node: SubDiagramNode, diagram: DomainDiagram):
        """Generate code for sub_diagram node.

        Supports:
        - Named diagrams (diagram_name) → Import from separate module
        - Inline diagrams (diagram_data) → Generate as local function
        - Batch mode → Loop over inputs
        """
        label = getattr(node, "label", "Sub-Diagram")
        diagram_name = node.diagram_name
        diagram_data = node.diagram_data
        batch_mode = node.batch

        self.main_code.append(f"    # {label}")

        # Handle batch mode
        if batch_mode:
            batch_input_key = node.batch_input_key or "items"
            self.main_code.append(f"    # Batch mode: processing multiple items")
            self.main_code.append(f"    batch_results = []")
            self.main_code.append(f"    for item in inputs.get('{batch_input_key}', []):")
            indent = "    "
        else:
            indent = ""

        # Named diagram: Generate import and call
        if diagram_name:
            # Convert diagram name to module name (e.g., "codegen/node_ui" → "codegen_node_ui")
            module_name = diagram_name.replace("/", "_").replace("-", "_")
            function_name = f"run_{module_name}"

            # Add import
            self.imports.add(f"from {module_name} import main as {function_name}")

            # Prepare inputs
            input_mapping = node.input_mapping or {}
            if input_mapping:
                self.main_code.append(f"{indent}    # Map inputs for sub-diagram")
                self.main_code.append(f"{indent}    sub_inputs = {{")
                for target_key, source_key in input_mapping.items():
                    self.main_code.append(f"{indent}        '{target_key}': {source_key},")
                self.main_code.append(f"{indent}    }}")
            else:
                self.main_code.append(f"{indent}    sub_inputs = {{}}")

            # Call sub-diagram
            var_name = self._node_var_name(node)
            self.main_code.append(f"{indent}    {var_name} = await {function_name}(**sub_inputs)")

            # Handle output mapping
            output_mapping = node.output_mapping or {}
            if output_mapping:
                self.main_code.append(f"{indent}    # Map outputs from sub-diagram")
                for source_key, target_key in output_mapping.items():
                    self.main_code.append(f"{indent}    {target_key} = {var_name}.get('{source_key}')")

            if batch_mode:
                self.main_code.append(f"        batch_results.append({var_name})")
                self.node_outputs[node.id] = "batch_results"
            else:
                self.node_outputs[node.id] = var_name

        # Inline diagram: Generate as function call
        elif diagram_data:
            self.main_code.append(f"{indent}    # TODO: Inline sub-diagram not yet fully supported")
            self.main_code.append(f"{indent}    # You can manually convert the inline diagram to a function")
            self.main_code.append(f"{indent}    # Diagram data: {json.dumps(diagram_data, indent=2)}")
            var_name = self._node_var_name(node)
            self.main_code.append(f"{indent}    {var_name} = {{}}")
            self.node_outputs[node.id] = var_name

        else:
            self.main_code.append(f"{indent}    # ERROR: No diagram_name or diagram_data specified")

        if batch_mode:
            self.main_code.append(f"    print(f'Batch processing complete: {{len(batch_results)}} items')")

        self.main_code.append("")

    def _node_var_name(self, node) -> str:
        """Generate a variable name for a node's output."""
        label = getattr(node, "label", "node")
        # Clean label to make valid Python variable name
        var_name = label.lower().replace(" ", "_").replace("~", "_")
        var_name = "".join(c if c.isalnum() or c == "_" else "_" for c in var_name)
        return var_name + "_output"

    def _build_script(self, diagram: DomainDiagram) -> str:
        """Build the final Python script."""
        lines = []

        # Header comment
        lines.append('#!/usr/bin/env python3')
        lines.append('"""')
        lines.append('Generated by DiPeO Diagram-to-Python Exporter')
        lines.append('This is a standalone Python script that can be run without DiPeO.')
        lines.append('')
        lines.append('To run: python <script>.py')
        lines.append('"""')
        lines.append('')

        # Imports
        lines.extend(sorted(self.imports))
        lines.append('')
        lines.append('')

        # Main function
        lines.append('async def main():')
        lines.append('    """Main execution function."""')

        # Initialization code
        if self.init_code:
            lines.append('')
            lines.append('    # Initialize clients')
            lines.extend(self.init_code)

        lines.append('')

        # Main execution code
        lines.extend(self.main_code)

        lines.append('    print("✅ Execution complete")')
        lines.append('')
        lines.append('')

        # Entry point
        lines.append('if __name__ == "__main__":')
        lines.append('    asyncio.run(main())')
        lines.append('')

        return "\n".join(lines)
