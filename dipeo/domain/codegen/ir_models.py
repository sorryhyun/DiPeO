"""Domain models for IR types."""

from typing import Any

from pydantic import BaseModel


class NodeSpecIR(BaseModel):
    node_type: str
    class_name: str
    fields: list[dict[str, Any]]
    validation: dict[str, Any] | None = None


class InterfaceIR(BaseModel):
    name: str
    fields: list[dict[str, Any]]
    extends: list[str] | None = None


class OperationIR(BaseModel):
    name: str
    type: str
    variables: list[dict[str, Any]]
    query_string: str


class BackendIR(BaseModel):
    node_specs: list[NodeSpecIR]
    enums: list[dict[str, Any]]
    interfaces: list[InterfaceIR]


class FrontendIR(BaseModel):
    components: list[dict[str, Any]]
    schemas: list[dict[str, Any]]


class StrawberryIR(BaseModel):
    operations: list[OperationIR]
    types: list[dict[str, Any]]
    scalars: list[dict[str, Any]]
