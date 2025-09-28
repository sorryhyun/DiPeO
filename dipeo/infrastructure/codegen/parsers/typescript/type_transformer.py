"""TypeScript to Python type transformation utilities."""

from dipeo.infrastructure.codegen.type_system import TypeConverter

_CONVERTER = TypeConverter()


def map_ts_type_to_python(ts_type: str) -> str:
    """Map a TypeScript type to its Python equivalent using the shared converter."""

    return _CONVERTER.ts_to_python(ts_type)
