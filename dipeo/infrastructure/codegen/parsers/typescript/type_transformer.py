"""TypeScript to Python type transformation utilities."""

from dipeo.infrastructure.codegen.ir_builders.type_system_unified import UnifiedTypeConverter

_CONVERTER = UnifiedTypeConverter()


def map_ts_type_to_python(ts_type: str) -> str:
    """Map a TypeScript type to its Python equivalent using the unified converter."""

    return _CONVERTER.ts_to_python(ts_type)
