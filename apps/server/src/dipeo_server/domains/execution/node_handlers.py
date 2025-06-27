"""Node handlers implementing BaseNodeHandler from dipeo_core.

This module migrates from the decorator-based approach to the BaseNodeHandler architecture.
"""

import contextlib
from typing import Any

from dipeo_core import BaseNodeHandler, RuntimeContext, register_handler
from dipeo_domain.models import DomainNode
from pydantic import BaseModel, Field

from .handlers import (
    NodeOutput,
    create_node_output,
)

# Pydantic schemas for node data validation

class StartNodeData(BaseModel):
    """Schema for start node data."""
    pass


class PersonJobNodeData(BaseModel):
    """Schema for person_job node data."""
    personId: str | None = Field(None, alias="person")
    firstOnlyPrompt: str = ""
    defaultPrompt: str = ""
    forgettingMode: str | None = None
    label: str = ""
    maxIteration: int = 1


class EndpointNodeData(BaseModel):
    """Schema for endpoint node data."""
    data: Any | None = None
    saveToFile: bool = Field(False, alias="save_to_file")
    filePath: str | None = Field(None, alias="file_path")
    fileName: str | None = Field(None, alias="file_name")


class ConditionNodeData(BaseModel):
    """Schema for condition node data."""
    conditionType: str = ""


class DBNodeData(BaseModel):
    """Schema for db node data."""
    operation: str = "read"
    sourceDetails: str = ""


class NotionNodeData(BaseModel):
    """Schema for notion node data."""
    action: str = "read"
    database_id: str = ""


class UserResponseNodeData(BaseModel):
    """Schema for user_response node data."""
    prompt: str = ""
    timeout: int | None = None


class PersonBatchJobNodeData(BaseModel):
    """Schema for person_batch_job node data."""
    personIds: list[str] = Field(default_factory=list)
    prompt: str = ""
    parallelExecution: bool = True
    aggregateResults: bool = False


# Handler implementations

@register_handler
class StartNodeHandler(BaseNodeHandler):
    """Handler for start nodes."""

    @property
    def node_type(self) -> str:
        return "start"

    @property
    def schema(self) -> type[BaseModel]:
        return StartNodeData

    @property
    def description(self) -> str:
        return "Kick-off node: no input, always succeeds"

    async def execute(
        self,
        props: StartNodeData,
        context: RuntimeContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute start node."""
        return create_node_output({"default": ""}, {"message": "Execution started"})


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
        return ["conversation_service", "llm_service"]

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
        conversation_service = services["conversation_service"]
        llm_service = services["llm_service"]

        # Create a DomainNode for compatibility with existing service
        node = DomainNode(
            id=context.current_node_id,
            type="person_job",
            data=props.model_dump(exclude_unset=True),
        )

        # Get diagram from context
        diagram = services.get("diagram")

        # Delegate to conversation service
        result = await conversation_service.execute_person_job(
            node=node,
            execution_id=context.execution_id,
            exec_count=context.get_node_execution_count(context.current_node_id),
            inputs=inputs,
            diagram=diagram,
            llm_service=llm_service,
        )

        # Handle token usage accumulation if needed
        if result.get("token_usage") and "token_service" in services:
            token_service = services["token_service"]
            token_service.add_token_usage(context.current_node_id, result["token_usage"])

        return create_node_output(result["output_values"], result["metadata"])


@register_handler
class EndpointNodeHandler(BaseNodeHandler):
    """Handler for endpoint nodes."""

    @property
    def node_type(self) -> str:
        return "endpoint"

    @property
    def schema(self) -> type[BaseModel]:
        return EndpointNodeData

    @property
    def requires_services(self) -> list[str]:
        return ["file_service"]

    @property
    def description(self) -> str:
        return "Endpoint node – pass through data and optionally save to file"

    async def execute(
        self,
        props: EndpointNodeData,
        context: RuntimeContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute endpoint node."""
        file_service = services["file_service"]

        if props.data is not None:
            result_data = props.data
        else:
            result_data = inputs if inputs else {}

        if props.saveToFile:
            file_path = props.filePath or props.fileName

            if file_path:
                try:
                    if isinstance(result_data, dict) and "default" in result_data:
                        content = str(result_data["default"])
                    else:
                        content = str(result_data)

                    await file_service.write(file_path, content)

                    return create_node_output(
                        {"default": result_data}, {"saved_to": file_path}
                    )
                except Exception as exc:
                    return create_node_output(
                        {"default": result_data}, {"save_error": str(exc)}
                    )

        return create_node_output({"default": result_data})


@register_handler
class ConditionNodeHandler(BaseNodeHandler):
    """Handler for condition nodes."""

    @property
    def node_type(self) -> str:
        return "condition"

    @property
    def schema(self) -> type[BaseModel]:
        return ConditionNodeData

    @property
    def description(self) -> str:
        return "Condition node: currently supports detect_max_iterations"

    async def execute(
        self,
        props: ConditionNodeData,
        context: RuntimeContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute condition node."""
        if props.conditionType != "detect_max_iterations":
            return create_node_output({"False": None}, {"condition_result": False})

        # Get diagram to check upstream nodes
        diagram = services.get("diagram")
        if not diagram:
            return create_node_output({"False": None}, {"condition_result": False})

        # True only if all upstream person_job nodes reached their max_iterations
        result = True
        for edge in context.edges:
            if edge.get("target", "").startswith(context.current_node_id):
                src_node_id = edge.get("source", "").split(":")[0]
                src_node = next((n for n in diagram.nodes if n.id == src_node_id), None)
                if src_node and src_node.type == "person_job":
                    exec_count = context.get_node_execution_count(src_node_id)
                    max_iter = int((src_node.data or {}).get("maxIteration", 1))
                    if exec_count < max_iter:
                        result = False
                        break

        # Forward inputs with branch key for backward compatibility
        branch_key = "True" if result else "False"
        value: dict[str, Any] = {**inputs}
        value[branch_key] = inputs

        if "default" not in value and inputs:
            if "conversation" in inputs:
                value["default"] = inputs["conversation"]
            else:
                first_key = next(iter(inputs.keys()), None)
                if first_key:
                    value["default"] = inputs[first_key]

        return create_node_output(value, {"condition_result": result})


@register_handler
class DBNodeHandler(BaseNodeHandler):
    """Handler for db nodes."""

    @property
    def node_type(self) -> str:
        return "db"

    @property
    def schema(self) -> type[BaseModel]:
        return DBNodeData

    @property
    def requires_services(self) -> list[str]:
        return ["file_service"]

    @property
    def description(self) -> str:
        return "File-based DB node supporting read, write and append operations"

    async def execute(
        self,
        props: DBNodeData,
        context: RuntimeContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute db node."""
        file_service = services["file_service"]

        # Get single input value
        input_val = None
        if inputs:
            # Get first non-empty value
            for _key, val in inputs.items():
                if val is not None:
                    input_val = val
                    break

        try:
            if props.operation == "read":
                if hasattr(file_service, "aread"):
                    result = await file_service.aread(props.sourceDetails)
                else:
                    result = file_service.read(props.sourceDetails)
            elif props.operation == "write":
                await file_service.write(props.sourceDetails, str(input_val))
                result = f"Saved to {props.sourceDetails}"
            elif props.operation == "append":
                existing = ""
                if hasattr(file_service, "aread"):
                    with contextlib.suppress(Exception):
                        existing = await file_service.aread(props.sourceDetails)
                await file_service.write(props.sourceDetails, existing + str(input_val))
                result = f"Appended to {props.sourceDetails}"
            else:
                result = "Unknown operation"
        except Exception as exc:
            result = f"Error: {exc}"

        return create_node_output({"default": result, "topic": result})


@register_handler
class NotionNodeHandler(BaseNodeHandler):
    """Handler for notion nodes."""

    @property
    def node_type(self) -> str:
        return "notion"

    @property
    def schema(self) -> type[BaseModel]:
        return NotionNodeData

    @property
    def requires_services(self) -> list[str]:
        return ["notion_service"]

    @property
    def description(self) -> str:
        return "Wrapper around notion_service.execute_action"

    async def execute(
        self,
        props: NotionNodeData,
        context: RuntimeContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute notion node."""
        notion_service = services["notion_service"]

        result = await notion_service.execute_action(
            action=props.action,
            database_id=props.database_id,
            data=inputs,
        )
        return create_node_output({"default": result})


@register_handler
class UserResponseNodeHandler(BaseNodeHandler):
    """Handler for user_response nodes."""

    @property
    def node_type(self) -> str:
        return "user_response"

    @property
    def schema(self) -> type[BaseModel]:
        return UserResponseNodeData

    @property
    def description(self) -> str:
        return "Interactive node that prompts for user input"

    async def execute(
        self,
        props: UserResponseNodeData,
        context: RuntimeContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute user_response node."""
        # Check if we have an interactive handler
        exec_context = services.get("execution_context")
        if exec_context and hasattr(exec_context, "interactive_handler") and exec_context.interactive_handler:
            # Prepare the message with inputs if available
            message = props.prompt
            if inputs:
                input_str = str(inputs.get("default", inputs))
                message = f"{message}\n\nContext: {input_str}"

            # Call the interactive handler
            response = await exec_context.interactive_handler({
                "type": "user_input_required",
                "node_id": context.current_node_id,
                "prompt": message,
                "timeout": props.timeout,
            })

            return create_node_output({"default": response, "user_response": response})
        # If no interactive handler, return empty response
        return create_node_output(
            {"default": "", "user_response": ""},
            {"warning": "No interactive handler available"}
        )


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
        return ["conversation_service", "llm_service"]

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
        conversation_service = services["conversation_service"]
        llm_service = services["llm_service"]
        diagram = services.get("diagram")

        # Prepare prompt with inputs
        prompt = props.prompt
        if inputs:
            input_str = str(inputs.get("default", inputs))
            prompt = f"{prompt}\n\nInput: {input_str}"

        results = {}
        metadata = {"person_count": len(props.personIds)}

        if props.parallelExecution:
            # Execute in parallel
            import asyncio
            tasks = []
            for person_id in props.personIds:
                # Create a person_job node for each person
                node = DomainNode(
                    id=f"{context.current_node_id}_{person_id}",
                    type="person_job",
                    data={
                        "personId": person_id,
                        "defaultPrompt": prompt,
                        "maxIteration": 1,
                    },
                )
                task = conversation_service.execute_person_job(
                    node=node,
                    execution_id=context.execution_id,
                    exec_count=1,
                    inputs={"default": prompt},
                    diagram=diagram,
                    llm_service=llm_service,
                )
                tasks.append(task)

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            for person_id, response in zip(props.personIds, responses, strict=False):
                if isinstance(response, Exception):
                    results[person_id] = {"error": str(response)}
                else:
                    results[person_id] = response.get("output_values", {}).get("default", "")
        else:
            # Execute sequentially
            for person_id in props.personIds:
                node = DomainNode(
                    id=f"{context.current_node_id}_{person_id}",
                    type="person_job",
                    data={
                        "personId": person_id,
                        "defaultPrompt": prompt,
                        "maxIteration": 1,
                    },
                )
                try:
                    response = await conversation_service.execute_person_job(
                        node=node,
                        execution_id=context.execution_id,
                        exec_count=1,
                        inputs={"default": prompt},
                        diagram=diagram,
                        llm_service=llm_service,
                    )
                    results[person_id] = response.get("output_values", {}).get("default", "")
                except Exception as e:
                    results[person_id] = {"error": str(e)}

        # Aggregate results if requested
        if props.aggregateResults:
            aggregated = "\n\n".join([
                f"Person {pid}: {result}"
                for pid, result in results.items()
            ])
            return create_node_output({"default": aggregated, "results": results}, metadata)
        return create_node_output({"default": results, "results": results}, metadata)


# The handlers are now auto-registered using @register_handler decorator
# This function is kept for backward compatibility but is now a no-op
def register_all_handlers(registry):
    """Legacy function - handlers are now auto-registered."""
    # Handlers are automatically registered via @register_handler decorator
    pass
