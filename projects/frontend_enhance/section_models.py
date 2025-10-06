"""Pydantic models for frontend_enhance multi-section planning."""

from pydantic import BaseModel, ConfigDict, Field


class Architecture(BaseModel):
    """Application architecture and design patterns."""

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


class PromptContext(BaseModel):
    """Context to guide prompt generation for a section."""

    model_config = ConfigDict(extra="forbid")

    component_type: str = Field(
        description="Type of component: list, form, dashboard, card, modal, etc."
    )
    data_model: str | None = Field(
        default=None,
        description="Primary data model this section works with: task, user, product, etc.",
    )
    interactions: list[str] = Field(
        default_factory=list,
        description="User interactions: view, create, update, delete, filter, sort, etc.",
    )
    styling_approach: str | None = Field(
        default="tailwind", description="CSS approach: tailwind, styled-components, css-modules"
    )
    dependencies: list[str] | None = Field(
        default=None, description="Other sections this depends on, if any"
    )


class Section(BaseModel):
    """A single feature to be implemented independently."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        description="Unique kebab-case identifier (e.g., 'task-list', 'add-form')",
        pattern="^[a-z][a-z0-9-]*$",
    )
    title: str = Field(description="Human-readable title for the section")
    description: str = Field(description="Detailed description of what this section does")
    file_to_implement: str = Field(
        description="Exact file path to implement (e.g., 'src/shared/components/Button.tsx', 'src/features/dashboard/components/DashboardLayout.tsx')"
    )
    acceptance: list[str] = Field(
        min_items=2, max_items=8, description="Measurable acceptance criteria for this section"
    )
    implementation_steps: list[str] = Field(
        min_items=3,
        max_items=10,
        description="Concrete implementation steps for THIS specific file (e.g., '1. Define component props interface', '2. Implement component logic', '3. Add event handlers')",
    )
    integration_points: list[str] = Field(
        default_factory=list,
        description="How this section integrates with others (e.g., 'Emits task-updated event', 'Consumes user context', 'Provides TaskAPI service')",
    )
    prompt_context: PromptContext = Field(
        description="Context to guide code generation for this section"
    )
    priority: int | None = Field(
        default=1, ge=1, le=5, description="Priority level (1=highest, 5=lowest)"
    )


class Response(BaseModel):
    """Architecture and sections to implement."""

    model_config = ConfigDict(extra="forbid")

    architecture: Architecture = Field(
        description="Overall application architecture and how sections fit together"
    )
    sections: list[Section] = Field(
        min_items=1, max_items=10, description="List of sections to implement in parallel"
    )


EXAMPLE_RESPONSE = Response(
    architecture=Architecture(
        overview="A modular task management dashboard built with React 18+ and TypeScript. Features are split into independent sections that communicate through a centralized state store and event bus. Each section follows container/presentational pattern with clear separation of concerns.",
        patterns=[
            "Container/Presentational Components",
            "Atomic Design",
            "Domain-driven layers",
            "Event-driven communication",
        ],
        data_flow="Global state managed by Zustand, server state via React Query with optimistic updates. Components emit domain events that trigger state updates. API calls are centralized in service layers with proper error handling.",
        folder_structure="src/features/{section}/ containing components/, hooks/, services/, types/, and utils/. Shared code in src/shared/ with common components, hooks, and utilities.",
        tech_stack=[
            "Zustand",
            "React Query",
            "React Hook Form",
            "Zod",
            "Tailwind CSS",
            "React Testing Library",
        ],
    ),
    sections=[
        Section(
            id="task-list",
            title="Task List Component",
            description="Display all tasks with status indicators and actions",
            file_to_implement="src/features/tasks/components/TaskList.tsx",
            acceptance=[
                "Shows all tasks in a clean list format",
                "Each task displays title, status, and actions",
                "Supports marking tasks as complete",
                "Has delete functionality",
            ],
            implementation_steps=[
                "Define TypeScript interfaces for Task and TaskList props",
                "Create TaskItem presentational component with Tailwind styling",
                "Build TaskList container with React Query integration",
                "Add optimistic updates for task mutations",
                "Implement error boundaries and loading states",
                "Write unit tests for components and hooks",
            ],
            integration_points=[
                "Emits 'task-updated' and 'task-deleted' events",
                "Consumes TaskAPI service for data operations",
                "Updates global task count in app header",
            ],
            prompt_context=PromptContext(
                component_type="list",
                data_model="task",
                interactions=["view", "update", "delete"],
                styling_approach="tailwind",
            ),
            priority=1,
        ),
        Section(
            id="add-task",
            title="Add Task Form",
            description="Form component to create new tasks",
            file_to_implement="src/features/tasks/components/AddTaskForm.tsx",
            acceptance=[
                "Input field for task title",
                "Optional description field",
                "Submit button with loading state",
                "Form validation and error display",
            ],
            implementation_steps=[
                "Define form schema with Zod validation",
                "Create form component with React Hook Form",
                "Integrate with TaskAPI service for submission",
                "Add loading and error states",
                "Implement success feedback with toast notifications",
            ],
            integration_points=[
                "Emits 'task-created' event on successful submission",
                "Triggers task-list refetch via React Query",
                "Resets form on successful submission",
            ],
            prompt_context=PromptContext(
                component_type="form",
                data_model="task",
                interactions=["create"],
                styling_approach="tailwind",
                dependencies=["task-list"],
            ),
            priority=2,
        ),
    ],
)


if __name__ == "__main__":
    Section.model_rebuild()
    Response.model_rebuild()

    print("Example Response:")
    print(EXAMPLE_RESPONSE.model_dump_json(indent=2))
