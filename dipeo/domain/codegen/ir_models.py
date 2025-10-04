"""Domain models for IR types."""

from typing import Any, Optional

from pydantic import BaseModel


class NodeSpecIR(BaseModel):
    """IR for node specifications."""

    node_type: str
    class_name: str
    fields: list[dict[str, Any]]
    validation: dict[str, Any] | None = None


class InterfaceIR(BaseModel):
    """IR for TypeScript interfaces."""

    name: str
    fields: list[dict[str, Any]]
    extends: list[str] | None = None


class OperationIR(BaseModel):
    """IR for GraphQL operations."""

    name: str
    type: str  # query, mutation, subscription
    variables: list[dict[str, Any]]
    query_string: str


class BackendIR(BaseModel):
    """Complete backend IR structure."""

    node_specs: list[NodeSpecIR]
    enums: list[dict[str, Any]]
    interfaces: list[InterfaceIR]


class FrontendIR(BaseModel):
    """Complete frontend IR structure."""

    components: list[dict[str, Any]]
    schemas: list[dict[str, Any]]


class StrawberryIR(BaseModel):
    """Complete GraphQL IR structure."""

    operations: list[OperationIR]
    types: list[dict[str, Any]]
    scalars: list[dict[str, Any]]
