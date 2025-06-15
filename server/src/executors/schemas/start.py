"""Schema for Start node type."""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, Union
import json

from .base import BaseNodeProps


class StartNodeProps(BaseNodeProps):
    """Properties for Start node type."""
    
    data: Optional[Union[str, Dict[str, Any], list]] = Field(
        None, 
        description="Initial data to provide to the workflow"
    )
    
    @validator('data', pre=True)
    def parse_data(cls, v):
        """Parse data if it's a JSON string."""
        if isinstance(v, str):
            try:
                # Try to parse as JSON
                return json.loads(v)
            except json.JSONDecodeError:
                # Keep as string if not valid JSON
                return v
        return v
    
    def get_output(self) -> Any:
        """Get the output data for this start node."""
        return self.data if self.data is not None else {}