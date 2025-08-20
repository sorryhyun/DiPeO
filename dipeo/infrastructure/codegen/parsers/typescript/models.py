"""Models for TypeScript parser results."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union


@dataclass
class PropertyInfo:
    """Information about a property in an interface or class."""
    name: str
    type: str
    optional: bool
    readonly: bool
    jsDoc: Optional[str] = None


@dataclass
class InterfaceInfo:
    """Information about a TypeScript interface."""
    name: str
    properties: List[PropertyInfo]
    isExported: bool
    extends: Optional[List[str]] = None
    jsDoc: Optional[str] = None


@dataclass
class TypeAliasInfo:
    """Information about a TypeScript type alias."""
    name: str
    type: str
    isExported: bool
    jsDoc: Optional[str] = None


@dataclass
class EnumMember:
    """Information about an enum member."""
    name: str
    value: Optional[Union[str, int]] = None


@dataclass
class EnumInfo:
    """Information about a TypeScript enum."""
    name: str
    members: List[EnumMember]
    isExported: bool
    jsDoc: Optional[str] = None


@dataclass
class ParameterInfo:
    """Information about a function or method parameter."""
    name: str
    type: str
    optional: bool
    defaultValue: Optional[str] = None


@dataclass
class MethodInfo:
    """Information about a class method."""
    name: str
    parameters: List[ParameterInfo]
    returnType: str
    isAsync: bool
    jsDoc: Optional[str] = None


@dataclass
class ClassInfo:
    """Information about a TypeScript class."""
    name: str
    properties: List[PropertyInfo]
    methods: List[MethodInfo]
    isExported: bool
    extends: Optional[str] = None
    implements: Optional[List[str]] = None
    jsDoc: Optional[str] = None


@dataclass
class FunctionInfo:
    """Information about a TypeScript function."""
    name: str
    parameters: List[ParameterInfo]
    returnType: str
    isAsync: bool
    isExported: bool
    jsDoc: Optional[str] = None