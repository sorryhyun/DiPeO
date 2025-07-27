# Auto-generated Pydantic model for sub_diagram node

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field




class SubDiagramNodeData(BaseModel):
    """Data model for Sub-Diagram node."""
    diagram_name: Optional[str] = Field(description="Name of the diagram to execute (e.g., 'workflow/process')")
    diagram_data: Optional[Dict[str, Any]] = Field(description="Inline diagram data (alternative to diagram_name)")
    input_mapping: Optional[Dict[str, Any]] = Field(description="Map node inputs to sub-diagram variables")
    output_mapping: Optional[Dict[str, Any]] = Field(description="Map sub-diagram outputs to node outputs")
    timeout: Optional[float] = Field(description="Execution timeout in seconds")
    wait_for_completion: Optional[bool] = Field(description="Whether to wait for sub-diagram completion")
    isolate_conversation: Optional[bool] = Field(description="Create isolated conversation context for sub-diagram")
    ignoreIfSub: Optional[bool] = Field(description="Skip execution if this diagram is being run as a sub-diagram")

    class Config:
        extra = "forbid"
        validate_assignment = True