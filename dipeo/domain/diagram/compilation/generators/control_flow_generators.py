"""Generator for control flow nodes (condition)."""

from typing import Any

from dipeo.diagram_generated.domain_models import DomainDiagram
from dipeo.domain.diagram.compilation.generators.base import BaseNodeGenerator


class ConditionNodeGenerator(BaseNodeGenerator):
    """Generator for condition nodes (if/else logic)."""

    def generate(self, node: Any, diagram: DomainDiagram) -> None:
        """Generate code for condition node.

        Args:
            node: The condition node
            diagram: The full diagram
        """
        label = self._get_node_label(node, "Condition")
        condition_type = (
            node.data.get("condition_type")
            if hasattr(node, "data")
            else getattr(node, "condition_type", None)
        )

        self.context.add_main_code(f"    # {label}")

        if condition_type == "custom":
            expression = (
                node.data.get("expression", "True")
                if hasattr(node, "data")
                else getattr(node, "expression", "True")
            )
            self.context.add_main_code(f"    if {expression}:")

            condtrue_arrows = [a for a in diagram.arrows if a.source == f"{node.id}_condtrue"]
            condfalse_arrows = [a for a in diagram.arrows if a.source == f"{node.id}_condfalse"]

            if condtrue_arrows:
                self.context.add_main_code("        # condtrue path")
                self.context.add_main_code("        pass  # Continue to next node")

            if condfalse_arrows:
                self.context.add_main_code("    else:")
                self.context.add_main_code("        # condfalse path")
                self.context.add_main_code("        pass  # Loop back or alternative path")

        elif condition_type == "llm_decision":
            self._generate_llm_decision(node, diagram, label)
        else:
            self.context.add_main_code(
                f"    # TODO: Condition type '{condition_type}' not yet supported"
            )

        self._add_blank_line()

    def _generate_llm_decision(self, node: Any, diagram: DomainDiagram, label: str) -> None:
        """Generate code for LLM-based decision node.

        Args:
            node: The condition node
            diagram: The full diagram
            label: The node label
        """
        person_id = (
            node.data.get("person") if hasattr(node, "data") else getattr(node, "person", None)
        )
        judge_by = (
            node.data.get("judge_by", "")
            if hasattr(node, "data")
            else getattr(node, "judge_by", "")
        )

        person = next((p for p in diagram.persons if p.id == person_id), None)
        if not person:
            self.context.add_main_code(f"    # ERROR: Person config '{person_id}' not found")
            return

        # Handle both LLMService enum and string values
        if hasattr(person, "llm_config"):
            service = (
                person.llm_config.service.value
                if hasattr(person.llm_config.service, "value")
                else str(person.llm_config.service)
            )
            model = person.llm_config.model
        else:
            service = (
                person.service.value if hasattr(person.service, "value") else str(person.service)
            )
            model = person.model

        service = service.lower()

        # Setup appropriate client
        if "openai" in service or "gpt" in model.lower():
            self.context.add_import("from openai import AsyncOpenAI")
            self.context.add_import("import os")
            client_var = "openai_client"
            if not any(client_var in line for line in self.context.init_code):
                self.context.add_init_code(
                    f'    {client_var} = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))'
                )
        elif "anthropic" in service or "claude" in model.lower():
            self.context.add_import("from anthropic import AsyncAnthropic")
            self.context.add_import("import os")
            client_var = "anthropic_client"
            if not any(client_var in line for line in self.context.init_code):
                self.context.add_init_code(
                    f'    {client_var} = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))'
                )
        else:
            self.context.add_main_code(f"    # ERROR: Unsupported service '{service}'")
            return

        # Generate LLM decision call
        decision_prompt = f"{judge_by}\n\nRespond with only 'true' or 'false'."
        var_name = self._get_node_var_name(node) + "_decision"

        if "openai" in service or "gpt" in model.lower():
            self.context.add_main_code(f"    response = await {client_var}.chat.completions.create(")
            self.context.add_main_code(f'        model="{model}",')
            self.context.add_main_code(f"        messages=[")
            self.context.add_main_code(f'            {{"role": "user", "content": {decision_prompt!r}}}')
            self.context.add_main_code(f"        ]")
            self.context.add_main_code(f"    )")
            self.context.add_main_code(
                f"    {var_name} = response.choices[0].message.content.strip().lower() == 'true'"
            )
        elif "anthropic" in service or "claude" in model.lower():
            self.context.add_main_code(f"    response = await {client_var}.messages.create(")
            self.context.add_main_code(f'        model="{model}",')
            self.context.add_main_code(f"        max_tokens=10,")
            self.context.add_main_code(f"        messages=[")
            self.context.add_main_code(f'            {{"role": "user", "content": {decision_prompt!r}}}')
            self.context.add_main_code(f"        ]")
            self.context.add_main_code(f"    )")
            self.context.add_main_code(
                f"    {var_name} = response.content[0].text.strip().lower() == 'true'"
            )

        # Generate conditional logic based on decision
        self.context.add_main_code(f"    if {var_name}:")
        self.context.add_main_code("        # condtrue path")
        self.context.add_main_code("        pass  # Continue to next node")

        condfalse_arrows = [a for a in diagram.arrows if a.source == f"{node.id}_condfalse"]
        if condfalse_arrows:
            self.context.add_main_code("    else:")
            self.context.add_main_code("        # condfalse path")
            self.context.add_main_code("        pass  # Loop back or alternative path")
