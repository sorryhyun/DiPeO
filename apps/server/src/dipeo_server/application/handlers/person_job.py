"""Person job node handler - handles conversational AI job execution."""

from typing import Any

from dipeo_core import BaseNodeHandler, RuntimeContext, register_handler
from dipeo_domain.models import DomainDiagram, DomainNode, NodeOutput, PersonJobNodeData
from pydantic import BaseModel


@register_handler
class PersonJobNodeHandler(BaseNodeHandler):
    """Handler for person_job nodes."""

    @property
    def node_type(self) -> str:
        return "person_job"

    @property
    def schema(self) -> type[BaseModel]:
        return PersonJobNodeData

    @property
    def requires_services(self) -> list[str]:
        return ["conversation"]

    @property
    def description(self) -> str:
        return "Handle conversational person_job node using domain service"

    async def execute(
        self,
        props: PersonJobNodeData,
        context: RuntimeContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute person_job node."""
        # Only use domain service
        conversation = services["conversation"]

        node = DomainNode(
            id=context.current_node_id,
            type="person_job",
            data=props.model_dump(exclude_unset=True),
        )

        # Get execution count and diagram from context
        exec_count = context.get_node_execution_count(context.current_node_id) + 1

        # Get diagram from services if available
        diagram = services.get("diagram")
        if not diagram:
            # Create minimal diagram with node
            diagram = DomainDiagram(nodes=[node], arrows=[], persons=[])

        return await conversation.execute_person_job(
            node=node,
            execution_id=context.execution_id,
            exec_count=exec_count,
            inputs=inputs,
            diagram=diagram,
        )

