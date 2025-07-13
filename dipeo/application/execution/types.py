# Core execution types for DiPeO

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol, Type

from pydantic import BaseModel


class NodeHandler(Protocol):

    async def __call__(
        self,
        props: BaseModel,
        context: Any,  # ExecutionContext implementation
        inputs: Dict[str, Any],
        services: Dict[str, Any],
    ) -> Any:
        ...


ExecutionContext = Any


@dataclass
class NodeDefinition:

    type: str
    node_schema: Type[BaseModel]  # Renamed from 'schema' to avoid Pydantic conflict
    handler: NodeHandler
    requires_services: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class ExecutionOptions:

    debug: bool = False
    timeout: Optional[float] = None
    max_iterations: Optional[int] = None
    monitor: bool = False
    interactive: bool = False
    variables: Dict[str, Any] = field(default_factory=dict)

