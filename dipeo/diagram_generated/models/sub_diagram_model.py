# Auto-generated Pydantic model for sub_diagram node

from typing import *

from pydantic import *

from ..enums import *
from ..integrations import *


class SubDiagramNodeData(BaseModel):
    """Data model for Sub-Diagram node."""

    diagram_name: Optional[str] = Field(description="Name of the diagram to execute (e.g., 'workflow/process')")

    diagram_data: Optional[Dict[str, Any]] = Field(description="Inline diagram data (alternative to diagram_name)")

    input_mapping: Optional[Dict[str, Any]] = Field(description="Map node inputs to sub-diagram variables")

    output_mapping: Optional[Dict[str, Any]] = Field(description="Map sub-diagram outputs to node outputs")

    timeout: Optional[int] = Field(description="Execution timeout in seconds")

    wait_for_completion: Optional[bool] = Field(description="Whether to wait for sub-diagram completion")

    isolate_conversation: Optional[bool] = Field(description="Create isolated conversation context for sub-diagram")

    ignore_if_sub: Optional[bool] = Field(alias="ignoreIfSub", description="Skip execution if this diagram is being run as a sub-diagram")

    diagram_format: Optional[DiagramFormat] = Field(description="Format of the diagram file (yaml, json, or light)")

    batch: Optional[bool] = Field(description="Execute sub-diagram in batch mode for multiple inputs")

    batch_input_key: Optional[str] = Field(description="Key in inputs containing the array of items for batch processing")

    batch_parallel: Optional[bool] = Field(description="Execute batch items in parallel")


    class Config:
        extra = "forbid"
        validate_assignment = True
