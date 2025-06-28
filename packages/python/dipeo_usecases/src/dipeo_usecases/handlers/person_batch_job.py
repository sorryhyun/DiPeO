"""Person batch job node handler - executes prompts across multiple persons."""

import asyncio
from typing import Any

from dipeo_core import BaseNodeHandler, RuntimeContext, register_handler
from dipeo_core.execution import create_node_output
from dipeo_domain.models import DomainNode, NodeOutput, PersonJobNodeData
from pydantic import BaseModel

# PersonBatchJobNodeData is a type alias for PersonJobNodeData in TypeScript
# but not generated in Python, so we create it here
PersonBatchJobNodeData = PersonJobNodeData


@register_handler
class PersonBatchJobNodeHandler(BaseNodeHandler):
    """Handler for person_batch_job nodes."""

    @property
    def node_type(self) -> str:
        return "person_batch_job"

    @property
    def schema(self) -> type[BaseModel]:
        return PersonBatchJobNodeData

    @property
    def requires_services(self) -> list[str]:
        return ["conversation", "diagram_storage"]

    @property
    def description(self) -> str:
        return "Execute prompts across multiple persons in batch"

    async def execute(
        self,
        props: PersonBatchJobNodeData,
        context: RuntimeContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute person_batch_job node."""
        # Only use domain service
        conversation = services["conversation"]
        diagram_storage = services["diagram_storage"]

        # Get the diagram to look up persons
        diagram = await diagram_storage.get_diagram(context.diagram_id)

        # Prepare prompt with inputs
        prompt = props.prompt
        if inputs:
            input_str = str(inputs.get("default", inputs))
            prompt = f"{prompt}\n\nInput: {input_str}"

        results = {}
        metadata = {"person_count": len(props.personIds)}

        if props.parallelExecution:
            # Execute in parallel
            tasks = []
            for person_id in props.personIds:
                # Find the person in the diagram
                person = next((p for p in diagram.persons if p.id == person_id), None)
                if not person:
                    continue

                # Create a person_job node for each person
                node = DomainNode(
                    id=f"{context.current_node_id}_{person_id}",
                    type="person_job",
                    data={
                        "person": person.model_dump(),
                        "prompt": prompt,
                    },
                )
                task = conversation.execute_person_job(
                    node=node,
                    execution_id=context.execution_id,
                    inputs={"default": prompt},
                )
                tasks.append(task)

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Match responses to person IDs
            person_ids_with_tasks = [
                pid
                for pid in props.personIds
                if any(p.id == pid for p in diagram.persons)
            ]

            for person_id, response in zip(
                person_ids_with_tasks, responses, strict=False
            ):
                if isinstance(response, Exception):
                    results[person_id] = {"error": str(response)}
                else:
                    # NodeOutput has data attribute
                    results[person_id] = response.data
        else:
            # Execute sequentially
            for person_id in props.personIds:
                # Find the person in the diagram
                person = next((p for p in diagram.persons if p.id == person_id), None)
                if not person:
                    results[person_id] = {"error": f"Person {person_id} not found"}
                    continue

                node = DomainNode(
                    id=f"{context.current_node_id}_{person_id}",
                    type="person_job",
                    data={
                        "person": person.model_dump(),
                        "prompt": prompt,
                    },
                )
                try:
                    response = await conversation.execute_person_job(
                        node=node,
                        execution_id=context.execution_id,
                        inputs={"default": prompt},
                    )
                    # NodeOutput has data attribute
                    results[person_id] = response.data
                except Exception as e:
                    results[person_id] = {"error": str(e)}

        # Aggregate results if requested
        if props.aggregateResults:
            aggregated = "\n\n".join(
                [f"Person {pid}: {result}" for pid, result in results.items()]
            )
            return create_node_output(
                {"default": aggregated, "results": results}, metadata
            )
        return create_node_output({"default": results, "results": results}, metadata)
