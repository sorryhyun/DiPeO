"""
Pydantic models for frontend_enhance multi-section planning.
Defines structured output for Section Planner to split work into independent sections.
"""

from pydantic import BaseModel, ConfigDict, Field


class Architecture(BaseModel):
    """Overall application architecture and design patterns."""

    model_config = ConfigDict(extra="forbid")

    overview: str = Field(
        description="High-level architecture description explaining how all sections fit together"
    )
    patterns: list[str] = Field(
        min_items=2,
        max_items=8,
        description="Key architectural patterns and principles (e.g., 'Container/Presentational', 'Atomic Design', 'Domain-driven layers')",
    )
    data_flow: str = Field(
        description="How data flows through the application (state management, API calls, caching)"
    )
    folder_structure: str = Field(
        description="Detailed folder/file organization with example file paths. Be specific with actual file names, e.g.:\n"
        "src/\n"
        "  shared/\n"
        "    components/\n"
        "      Button.tsx\n"
        "      Card.tsx\n"
        "      Input.tsx\n"
        "    hooks/\n"
        "      useAuth.ts\n"
        "      useForm.ts\n"
        "  features/\n"
        "    dashboard/\n"
        "      components/\n"
        "        DashboardLayout.tsx\n"
        "        MetricCard.tsx"
    )
    tech_stack: list[str] = Field(
        description="Core technologies and their purpose (e.g., {'Zustand', 'React Query', 'React Hook Form'})"
    )


class Section(BaseModel):
    """A single file to be implemented."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        description="Unique kebab-case identifier (e.g., 'auth-provider', 'dashboard-page')",
        pattern="^[a-z][a-z0-9-]*$",
    )
    file_path: str = Field(
        description="File path where this section will be implemented (e.g., 'src/providers/AuthProvider.tsx')"
    )
    description: str = Field(
        description="Brief description of what this file does and its responsibility"
    )
    dependencies: list[str] = Field(
        default_factory=list,
        max_items=10,
        description="File paths this file imports from (besides Core Kernel which all files can use)",
    )
    exports: list[str] = Field(
        default_factory=list,
        max_items=20,
        description="What this file exports for other files to use (e.g., 'Button component', 'useAuth hook', 'formatDate function')",
    )
    priority: int | None = Field(
        default=2,
        ge=1,
        le=3,
        description="Priority: 1=foundational (providers, hooks), 2=components, 3=pages/features",
    )


class Response(BaseModel):
    """Response containing the architecture and list of sections to implement."""

    model_config = ConfigDict(extra="forbid")

    architecture: Architecture = Field(
        description="Overall application architecture and how sections fit together"
    )
    sections: list[Section] = Field(
        min_items=1,
        max_items=100,
        description="List of sections(i.e., files) to implement in parallel",
    )


# Example usage for LLM understanding
EXAMPLE_RESPONSE = Response(
    architecture=Architecture(
        overview="A healthcare portal built with React 18+ and TypeScript. All files import shared contracts from Core Kernel (@/core/*) ensuring consistency. Features are organized by domain with shared components in a common folder.",
        patterns=[
            "Container/Presentational Components",
            "Core Kernel for shared contracts",
            "Feature-based organization",
        ],
        data_flow="Auth state via Context, server state via React Query, configuration from @/app/config. Mock data in development mode.",
        folder_structure="""src/
  core/           # Core Kernel files (auto-generated)
  app/            # App configuration
  shared/         # Shared components and hooks
    components/
    hooks/
  features/       # Domain features
    appointments/
    dashboard/
  pages/          # Route pages
  providers/      # Context providers
  services/       # API and mock services""",
        tech_stack=[
            "React 18+ with TypeScript",
            "React Query for server state",
            "Context API for auth/theme",
            "Tailwind CSS",
            "Mock server for development",
        ],
    ),
    sections=[
        Section(
            id="auth-provider",
            file_path="src/providers/AuthProvider.tsx",
            description="Context provider for authentication state and user management",
            dependencies=[],
            exports=["AuthProvider", "useAuth hook"],
            priority=1,
        ),
        Section(
            id="api-client",
            file_path="src/services/apiClient.ts",
            description="Axios-based API client with token injection and error handling",
            dependencies=["src/providers/AuthProvider.tsx"],
            exports=["apiClient instance", "apiGet", "apiPost", "apiPut", "apiDelete"],
            priority=1,
        ),
        Section(
            id="dashboard-page",
            file_path="src/pages/DashboardPage.tsx",
            description="Main dashboard page showing health metrics and quick actions",
            dependencies=[
                "src/providers/AuthProvider.tsx",
                "src/shared/components/Layout.tsx",
                "src/features/dashboard/HealthDashboard.tsx",
            ],
            exports=["DashboardPage component (default)"],
            priority=3,
        ),
    ],
)


if __name__ == "__main__":
    # Rebuild models to ensure proper schema generation
    Section.model_rebuild()
    Response.model_rebuild()

    # Print example for reference
    print("Example Response:")
    print(EXAMPLE_RESPONSE.model_dump_json(indent=2))
