"""Generator for person_job nodes (LLM calls)."""

from typing import Any

from dipeo.diagram_generated.domain_models import DomainDiagram
from dipeo.domain.diagram.compilation.generators.base import BaseNodeGenerator
from dipeo.domain.diagram.compilation.utils import interpolate_prompt


class PersonJobNodeGenerator(BaseNodeGenerator):
    """Generator for person_job nodes (LLM API calls)."""

    def generate(self, node: Any, diagram: DomainDiagram) -> None:
        """Generate code for person_job node (LLM calls).

        Args:
            node: The person_job node
            diagram: The full diagram
        """
        label = self._get_node_label(node, "Person Job")
        person_id = (
            node.data.get("person") if hasattr(node, "data") else getattr(node, "person", None)
        )
        indent = self.context.get_indent()

        person = next((p for p in diagram.persons if p.id == person_id), None)
        if not person:
            self._add_comment(f"{label} - ERROR: Person config not found")
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

        if "openai" in service or "gpt" in model.lower():
            self._setup_openai_client()
            client_var = "openai_client"
        elif "anthropic" in service or "claude" in model.lower():
            self._setup_anthropic_client()
            client_var = "anthropic_client"
        else:
            self._add_comment(f"{label} - Unsupported service: {service}")
            return

        self.context.add_import("import os")

        prompt = (
            node.data.get("default_prompt", "")
            if hasattr(node, "data")
            else getattr(node, "default_prompt", "")
        )
        if not prompt:
            prompt = (
                node.data.get("resolved_prompt", "")
                if hasattr(node, "data")
                else getattr(node, "resolved_prompt", "")
            )

        # Handle prompt interpolation ({{variable}} patterns)
        prompt = interpolate_prompt(prompt, node, diagram, self.context.node_outputs)

        self._add_comment(label)

        # Generate LLM call
        uses_interpolation = "{" in prompt and "}" in prompt

        if "openai" in service or "gpt" in model.lower():
            self._generate_openai_call(client_var, model, prompt, uses_interpolation, node)
        elif "anthropic" in service or "claude" in model.lower():
            self._generate_anthropic_call(client_var, model, prompt, uses_interpolation, node)

        self._add_blank_line()

    def _setup_openai_client(self) -> None:
        """Setup OpenAI client if not already initialized."""
        self.context.add_import("from openai import AsyncOpenAI")
        client_var = "openai_client"
        # Check if client already initialized
        if not any(client_var in line for line in self.context.init_code):
            self.context.add_init_code(
                f'    {client_var} = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))'
            )

    def _setup_anthropic_client(self) -> None:
        """Setup Anthropic client if not already initialized."""
        self.context.add_import("from anthropic import AsyncAnthropic")
        client_var = "anthropic_client"
        # Check if client already initialized
        if not any(client_var in line for line in self.context.init_code):
            self.context.add_init_code(
                f'    {client_var} = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))'
            )

    def _generate_openai_call(
        self,
        client_var: str,
        model: str,
        prompt: str,
        uses_interpolation: bool,
        node: Any,
    ) -> None:
        """Generate OpenAI API call code.

        Args:
            client_var: Name of the client variable
            model: Model name
            prompt: Prompt text
            uses_interpolation: Whether the prompt uses f-string interpolation
            node: The node being generated
        """
        indent = self.context.get_indent()
        self.context.add_main_code(
            f"{indent}response = await {client_var}.chat.completions.create("
        )
        self.context.add_main_code(f'{indent}    model="{model}",')
        self.context.add_main_code(f"{indent}    messages=[")
        if uses_interpolation:
            self.context.add_main_code(
                f'{indent}        {{"role": "user", "content": f{prompt!r}}}'
            )
        else:
            self.context.add_main_code(f'{indent}        {{"role": "user", "content": {prompt!r}}}')
        self.context.add_main_code(f"{indent}    ]")
        self.context.add_main_code(f"{indent})")

        var_name = self._get_node_var_name(node)
        self.context.add_main_code(f"{indent}{var_name} = response.choices[0].message.content")
        self.context.set_node_output(node.id, var_name)

    def _generate_anthropic_call(
        self,
        client_var: str,
        model: str,
        prompt: str,
        uses_interpolation: bool,
        node: Any,
    ) -> None:
        """Generate Anthropic API call code.

        Args:
            client_var: Name of the client variable
            model: Model name
            prompt: Prompt text
            uses_interpolation: Whether the prompt uses f-string interpolation
            node: The node being generated
        """
        indent = self.context.get_indent()
        self.context.add_main_code(f"{indent}response = await {client_var}.messages.create(")
        self.context.add_main_code(f'{indent}    model="{model}",')
        self.context.add_main_code(f"{indent}    max_tokens=1024,")
        self.context.add_main_code(f"{indent}    messages=[")
        if uses_interpolation:
            self.context.add_main_code(
                f'{indent}        {{"role": "user", "content": f{prompt!r}}}'
            )
        else:
            self.context.add_main_code(f'{indent}        {{"role": "user", "content": {prompt!r}}}')
        self.context.add_main_code(f"{indent}    ]")
        self.context.add_main_code(f"{indent})")

        var_name = self._get_node_var_name(node)
        self.context.add_main_code(f"{indent}{var_name} = response.content[0].text")
        self.context.set_node_output(node.id, var_name)
