"""
Execution domain models
"""
from typing import Any, Dict, Optional, List
from pydantic import BaseModel

class NodeResult(BaseModel):
    """Result from executing a single node"""
    node_id: str
    status: str
    output: Optional[Any] = None
    error: Optional[str] = None
    
class ExecutionResult(BaseModel):
    """Result from executing a full diagram"""
    execution_id: str
    status: str
    results: List[NodeResult] = []
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}