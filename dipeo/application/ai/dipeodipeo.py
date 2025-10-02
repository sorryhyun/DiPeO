"""AI-powered diagram generation from natural language."""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from dipeo.config import BASE_DIR
from dipeo.config.base_logger import get_module_logger
from dipeo.infrastructure.llm_adapters.unified import UnifiedLLMClient

logger = get_module_logger(__name__)


@dataclass
class DiagramGenerationResult:
    """Result of diagram generation."""

    success: bool
    diagram_path: Optional[str] = None
    diagram_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class DiPeOAIGenerator:
    """Generates DiPeO diagrams from natural language requests."""

    def __init__(self):
        """Initialize the AI generator."""
        self.llm_client = UnifiedLLMClient()
        self.output_dir = BASE_DIR / "projects" / "dipeo_ai" / "generated"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_diagram_from_request(
        self,
        request: str,
        timeout: int = 90,
    ) -> DiagramGenerationResult:
        """Generate a diagram from a natural language request."""
        try:
            # Create prompt for LLM
            prompt = self._create_generation_prompt(request)

            # Call LLM to generate diagram
            response = await self.llm_client.generate_async(
                prompt=prompt,
                max_tokens=4000,
                temperature=0.7,
            )

            # Parse the generated diagram
            diagram_data = self._parse_diagram_response(response)

            if not diagram_data:
                return DiagramGenerationResult(
                    success=False,
                    error_message="Failed to parse generated diagram",
                )

            # Save the diagram
            diagram_name = self._generate_diagram_name(request)
            diagram_path = self.output_dir / f"{diagram_name}.light.yml"

            with open(diagram_path, "w") as f:
                yaml.dump(diagram_data, f, default_flow_style=False, sort_keys=False)

            logger.info(f"Generated diagram saved to {diagram_path}")

            return DiagramGenerationResult(
                success=True,
                diagram_path=str(diagram_path),
                diagram_data=diagram_data,
            )

        except Exception as e:
            logger.error(f"Failed to generate diagram: {e}")
            return DiagramGenerationResult(
                success=False,
                error_message=str(e),
            )

    def _create_generation_prompt(self, request: str) -> str:
        """Create the prompt for diagram generation."""
        return f"""Generate a DiPeO diagram in Light YAML format for the following request:

{request}

Requirements:
1. Use the Light YAML format with nodes and edges
2. Each node should have an id, type, and data fields
3. Common node types: person_job, api_job, condition, sub_diagram
4. Edges connect nodes with source and target ids
5. Include appropriate data fields for each node type

Please output only the YAML diagram content, no explanations.

Example format:
nodes:
  - id: start
    type: person_job
    data:
      prompt: "Starting the workflow"
  - id: process
    type: api_job
    data:
      endpoint: "/api/process"
      method: "POST"
edges:
  - source: start
    target: process
"""

    def _parse_diagram_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse the diagram from LLM response."""
        try:
            # Try to extract YAML from response
            # Look for YAML block or direct YAML content
            if "```yaml" in response:
                yaml_content = response.split("```yaml")[1].split("```")[0]
            elif "```" in response:
                yaml_content = response.split("```")[1].split("```")[0]
            else:
                yaml_content = response

            return yaml.safe_load(yaml_content)
        except Exception as e:
            logger.error(f"Failed to parse diagram response: {e}")
            return None

    def _generate_diagram_name(self, request: str) -> str:
        """Generate a name for the diagram based on the request."""
        # Simple name generation - take first few words
        words = request.lower().split()[:5]
        name = "_".join(word for word in words if word.isalnum())
        return name or "generated_diagram"