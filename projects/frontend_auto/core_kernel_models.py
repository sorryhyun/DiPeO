"""
Pydantic models for Core Kernel specifications.
Defines structured output for Core Kernel Architect to generate specifications for foundational contracts.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class CoreFile(BaseModel):
    """Specification for a single core kernel file."""
    model_config = ConfigDict(extra='forbid')
    
    file_path: str = Field(
        description="File path relative to src/ (e.g., 'core/contracts.ts', 'app/config.ts')"
    )
    purpose: str = Field(
        description="Brief description of what this file provides to the application"
    )
    exports: List[str] = Field(
        description="List of key exports from this file (types, functions, classes, constants)"
    )
    content: str = Field(
        description="Detailed specification of what should be in this file - types to define, functions to implement, patterns to follow, example usage"
    )


class CoreKernelResponse(BaseModel):
    """Response containing specifications for all core kernel files."""
    model_config = ConfigDict(extra='forbid')
    
    overview: str = Field(
        description="Brief explanation of how the core kernel provides foundation for all sections"
    )
    files: List[CoreFile] = Field(
        min_items=1,
        max_items=8,
        description="Specifications for core kernel files that establish shared contracts and utilities"
    )
    usage_guidelines: List[str] = Field(
        min_items=1,
        max_items=10,
        description="Key guidelines for sections using the core kernel (e.g., 'Import types from @/core/contracts', 'Use hooks.register() for extensions')"
    )


# Example for LLM understanding
EXAMPLE_RESPONSE = CoreKernelResponse(
    overview="Core kernel provides shared contracts, dependency injection, event bus, and configuration that all sections import from @/core/*. This ensures consistency and eliminates guesswork about types and patterns.",
    files=[
        CoreFile(
            file_path="core/contracts.ts",
            purpose="Domain types and API contracts used throughout the application",
            exports=["User", "Patient", "Appointment", "ApiResult", "ApiError"],
            content="""Define the following TypeScript interfaces and types:

1. User interface with:
   - id: string (unique identifier)
   - email: string
   - role: union type of 'patient' | 'doctor' | 'nurse' 
   - name: string
   - avatar?: optional string URL

2. Patient interface extending User with:
   - medicalRecordNumber: string
   - dateOfBirth: string (ISO format)
   - insuranceProvider?: optional string

3. Doctor interface extending User with:
   - specialization: string
   - licenseNumber: string

4. Appointment interface with:
   - id, patientId, doctorId: string
   - dateTime: string (ISO format)
   - status: 'scheduled' | 'completed' | 'cancelled'
   - reason: string
   - notes?: optional string

5. ApiResult<T> discriminated union type:
   - Success case: { success: true; data: T }
   - Error case: { success: false; error: ApiError }

6. ApiError interface with code, message, and optional details

Use strict TypeScript with no 'any' types. Export all as named exports."""
        ),
        CoreFile(
            file_path="core/hooks.ts",
            purpose="Hook registry for extension points throughout the app",
            exports=["HookPoint", "HookContext", "HookRegistry", "hooks"],
            content="""Create a flexible hook system for extension points:

1. HookPoint union type with these hook names:
   - 'beforeApiRequest', 'afterApiResponse'
   - 'onLogin', 'onLogout'  
   - 'onRouteChange'

2. HookContext interface containing:
   - config object (from app config)
   - user object (current user, optional)
   - Any other app-wide context needed

3. Generic Hook type signature

4. HookRegistry class with:
   - register() method to add hooks
   - run() method to execute hooks for a point
   - Support for async and sync handlers
   - Type-safe hook point names

5. Export singleton 'hooks' instance

Pattern: Allow any part of app to register hooks and run them at key points."""
        ),
        CoreFile(
            file_path="app/config.ts",
            purpose="Materialized configuration from JSON config file",
            exports=["config", "isDevelopment", "shouldUseMockData"],
            content="""Materialize the JSON configuration into TypeScript constants:

1. Export 'config' const object matching the JSON structure with:
   - appType, framework from config
   - developmentMode settings (all fields)
   - features array
   - Any other config fields
   - Use 'as const' for type narrowing

2. Computed boolean flags:
   - isDevelopment: check NODE_ENV
   - shouldUseMockData: combine isDevelopment with config setting
   - Feature flags based on features array

3. Mock data arrays (if development mode enabled):
   - mockUsers array from config
   - Any other mock data specified

Make all exports strongly typed. Config should be the source of truth for app settings."""
        )
    ],
    usage_guidelines=[
        "Import all domain types from @/core/contracts instead of defining locally",
        "Use hooks.register() to add custom behavior at extension points",
        "Reference config from @/app/config for feature flags and settings",
        "Never import from relative paths when a @/core/* export exists",
        "Use the event bus for decoupled communication between features"
    ]
)


if __name__ == "__main__":
    # Rebuild models to ensure proper schema generation
    CoreFile.model_rebuild()
    CoreKernelResponse.model_rebuild()
    
    # Print example for reference
    print("Example Core Kernel Response:")
    print(EXAMPLE_RESPONSE.model_dump_json(indent=2))