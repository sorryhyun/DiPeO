"""Models for TypeScript parser results."""

from dataclasses import dataclass


@dataclass
class PropertyInfo:
    name: str
    type: str
    optional: bool
    readonly: bool
    js_doc: str | None = None


@dataclass
class InterfaceInfo:
    name: str
    properties: list[PropertyInfo]
    is_exported: bool
    extends: list[str] | None = None
    js_doc: str | None = None


@dataclass
class TypeAliasInfo:
    name: str
    type: str
    is_exported: bool
    js_doc: str | None = None


@dataclass
class EnumMember:
    name: str
    value: str | int | None = None


@dataclass
class EnumInfo:
    name: str
    members: list[EnumMember]
    is_exported: bool
    js_doc: str | None = None


@dataclass
class ParameterInfo:
    name: str
    type: str
    optional: bool
    default_value: str | None = None


@dataclass
class MethodInfo:
    name: str
    parameters: list[ParameterInfo]
    return_type: str
    is_async: bool
    js_doc: str | None = None


@dataclass
class ClassInfo:
    name: str
    properties: list[PropertyInfo]
    methods: list[MethodInfo]
    is_exported: bool
    extends: str | None = None
    implements: list[str] | None = None
    js_doc: str | None = None


@dataclass
class FunctionInfo:
    name: str
    parameters: list[ParameterInfo]
    return_type: str
    is_async: bool
    is_exported: bool
    js_doc: str | None = None
