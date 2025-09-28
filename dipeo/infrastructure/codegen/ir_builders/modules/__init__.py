"""Reusable step modules for IR builders."""

from dipeo.infrastructure.codegen.ir_builders.modules.domain_models import (
    ExtractConversionsStep,
    ExtractDomainModelsStep,
    ExtractEnumsStep,
    ExtractIntegrationsStep,
)
from dipeo.infrastructure.codegen.ir_builders.modules.graphql_operations import (
    BuildOperationStringsStep,
    ExtractGraphQLOperationsStep,
    GroupOperationsByEntityStep,
)
from dipeo.infrastructure.codegen.ir_builders.modules.node_specs import (
    BuildCategoryMetadataStep,
    BuildNodeFactoryStep,
    ExtractNodeSpecsStep,
)
from dipeo.infrastructure.codegen.ir_builders.modules.ui_configs import (
    BuildNodeRegistryStep,
    ExtractNodeConfigsStep,
    GenerateFieldConfigsStep,
    GenerateTypeScriptModelsStep,
)

__all__ = [
    "BuildCategoryMetadataStep",
    "BuildNodeFactoryStep",
    "BuildNodeRegistryStep",
    "BuildOperationStringsStep",
    "ExtractConversionsStep",
    # Domain models
    "ExtractDomainModelsStep",
    "ExtractEnumsStep",
    # GraphQL operations
    "ExtractGraphQLOperationsStep",
    "ExtractIntegrationsStep",
    # UI configs
    "ExtractNodeConfigsStep",
    # Node specs
    "ExtractNodeSpecsStep",
    "GenerateFieldConfigsStep",
    "GenerateTypeScriptModelsStep",
    "GroupOperationsByEntityStep",
]
