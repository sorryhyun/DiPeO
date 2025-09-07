"""Models for TypeScript parser results."""

from dataclasses import dataclass


@dataclass
class PropertyInfo:
    """Information about a property in an interface or class."""

    name: str
    type: str
    optional: bool
    readonly: bool
    js_doc: str | None = None


@dataclass
class InterfaceInfo:
    """Information about a TypeScript interface."""

    name: str
    properties: list[PropertyInfo]
    is_exported: bool
    extends: list[str] | None = None
    js_doc: str | None = None


@dataclass
class TypeAliasInfo:
    """Information about a TypeScript type alias."""

    name: str
    type: str
    is_exported: bool
    js_doc: str | None = None


@dataclass
class EnumMember:
    """Information about an enum member."""

    name: str
    value: str | int | None = None


@dataclass
class EnumInfo:
    """Information about a TypeScript enum."""

    name: str
    members: list[EnumMember]
    is_exported: bool
    js_doc: str | None = None


@dataclass
class ParameterInfo:
    """Information about a function or method parameter."""

    name: str
    type: str
    optional: bool
    default_value: str | None = None


@dataclass
class MethodInfo:
    """Information about a class method."""

    name: str
    parameters: list[ParameterInfo]
    return_type: str
    is_async: bool
    js_doc: str | None = None


@dataclass
class ClassInfo:
    """Information about a TypeScript class."""

    name: str
    properties: list[PropertyInfo]
    methods: list[MethodInfo]
    is_exported: bool
    extends: str | None = None
    implements: list[str] | None = None
    js_doc: str | None = None


@dataclass
class FunctionInfo:
    """Information about a TypeScript function."""

    name: str
    parameters: list[ParameterInfo]
    return_type: str
    is_async: bool
    is_exported: bool
    js_doc: str | None = None
