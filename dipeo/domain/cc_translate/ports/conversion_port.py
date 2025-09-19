"""Protocol for conversion operations in domain layer."""

from dataclasses import dataclass
from typing import Generic, Optional, Protocol, TypeVar

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


@dataclass
class ConversionResult(Generic[TOutput]):
    """Result of a conversion operation."""

    success: bool
    output: Optional[TOutput]
    errors: list[str]
    warnings: list[str]
    metrics: dict[str, any]


class ConverterPort(Protocol[TInput, TOutput]):
    """Abstract interface for conversion operations."""

    async def convert(self, input_data: TInput) -> ConversionResult[TOutput]:
        """Convert input to output format."""
        ...

    def validate_input(self, input_data: TInput) -> bool:
        """Validate input data before conversion."""
        ...

    def get_supported_formats(self) -> list[str]:
        """Get list of supported conversion formats."""
        ...


class PreprocessorPort(Protocol[TInput]):
    """Abstract interface for preprocessing operations."""

    async def process(self, input_data: TInput) -> TInput:
        """Process and transform input data."""
        ...

    def validate(self, input_data: TInput) -> bool:
        """Validate input data."""
        ...


class PostProcessorPort(Protocol[TOutput]):
    """Abstract interface for post-processing operations."""

    async def process(self, output_data: TOutput) -> TOutput:
        """Process and optimize output data."""
        ...

    def validate(self, output_data: TOutput) -> bool:
        """Validate output data."""
        ...


class PipelinePort(Protocol[TInput, TOutput]):
    """Abstract interface for conversion pipelines."""

    async def execute(self, input_data: TInput) -> ConversionResult[TOutput]:
        """Execute the full conversion pipeline."""
        ...

    def add_preprocessor(self, processor: PreprocessorPort) -> None:
        """Add a preprocessor to the pipeline."""
        ...

    def add_postprocessor(self, processor: PostProcessorPort) -> None:
        """Add a post-processor to the pipeline."""
        ...

    def get_pipeline_stages(self) -> list[str]:
        """Get list of pipeline stages."""
        ...
