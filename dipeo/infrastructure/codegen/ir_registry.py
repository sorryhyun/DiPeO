"""Registry and factory for IR builders."""

from typing import Optional

from dipeo.domain.codegen.ir_builder_port import IRBuilderPort
from dipeo.infrastructure.codegen.ir_builders.builders import (
    BackendBuilder as BackendIRBuilder,
)
from dipeo.infrastructure.codegen.ir_builders.builders import (
    FrontendBuilder as FrontendIRBuilder,
)
from dipeo.infrastructure.codegen.ir_builders.builders import (
    StrawberryBuilder as StrawberryIRBuilder,
)


class IRBuilderRegistry:
    """Registry and factory for IR builders."""

    _builders: dict[str, type[IRBuilderPort]] = {
        "backend": BackendIRBuilder,
        "frontend": FrontendIRBuilder,
        "strawberry": StrawberryIRBuilder,
    }

    @classmethod
    def get_builder(cls, builder_type: str, config_path: str | None = None) -> IRBuilderPort:
        """Get IR builder instance by type.

        Args:
            builder_type: Type of builder to get
            config_path: Optional configuration path

        Returns:
            IRBuilderPort instance

        Raises:
            ValueError: If builder type is unknown
        """
        builder_class = cls._builders.get(builder_type)
        if not builder_class:
            available = ", ".join(cls._builders.keys())
            raise ValueError(f"Unknown builder type: {builder_type}. Available: {available}")

        if builder_type == "backend":
            return builder_class()
        else:
            return builder_class(config_path)

    @classmethod
    def register_builder(cls, name: str, builder_class: type[IRBuilderPort]):
        """Register custom IR builder.

        Args:
            name: Name for the builder
            builder_class: Builder class to register
        """
        cls._builders[name] = builder_class

    @classmethod
    def list_builders(cls) -> list[str]:
        """List all available builder types.

        Returns:
            List of registered builder type names
        """
        return list(cls._builders.keys())
