"""
Pydantic models for frontend_enhance multi-section planning.
Defines structured output for Section Planner to split work into independent sections.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class PromptContext(BaseModel):
    """Context information to guide prompt generation for a section."""
    model_config = ConfigDict(extra='forbid')
    
    component_type: str = Field(
        description="Type of component: list, form, dashboard, card, modal, etc."
    )
    data_model: Optional[str] = Field(
        default=None,
        description="Primary data model this section works with: task, user, product, etc."
    )
    interactions: List[str] = Field(
        default_factory=list,
        description="User interactions: view, create, update, delete, filter, sort, etc."
    )
    styling_approach: Optional[str] = Field(
        default="tailwind",
        description="CSS approach: tailwind, styled-components, css-modules"
    )
    dependencies: Optional[List[str]] = Field(
        default=None,
        description="Other sections this depends on, if any"
    )


class Section(BaseModel):
    """A single section/feature to be implemented independently."""
    model_config = ConfigDict(extra='forbid')
    
    id: str = Field(
        description="Unique kebab-case identifier (e.g., 'task-list', 'add-form')",
        pattern="^[a-z][a-z0-9-]*$"
    )
    title: str = Field(
        description="Human-readable title for the section"
    )
    description: str = Field(
        description="Detailed description of what this section does"
    )
    acceptance: List[str] = Field(
        min_items=2,
        max_items=8,
        description="Measurable acceptance criteria for this section"
    )
    prompt_context: PromptContext = Field(
        description="Context to guide code generation for this section"
    )
    priority: Optional[int] = Field(
        default=1,
        ge=1,
        le=5,
        description="Priority level (1=highest, 5=lowest)"
    )


class Response(BaseModel):
    """Response containing the list of sections to implement."""
    model_config = ConfigDict(extra='forbid')
    
    sections: List[Section] = Field(
        min_items=1,
        max_items=10,
        description="List of sections to implement in parallel"
    )


# Example usage for LLM understanding
EXAMPLE_RESPONSE = Response(
    sections=[
        Section(
            id="task-list",
            title="Task List Component",
            description="Display all tasks with status indicators and actions",
            acceptance=[
                "Shows all tasks in a clean list format",
                "Each task displays title, status, and actions",
                "Supports marking tasks as complete",
                "Has delete functionality"
            ],
            prompt_context=PromptContext(
                component_type="list",
                data_model="task",
                interactions=["view", "update", "delete"],
                styling_approach="tailwind"
            ),
            priority=1
        ),
        Section(
            id="add-task",
            title="Add Task Form",
            description="Form component to create new tasks",
            acceptance=[
                "Input field for task title",
                "Optional description field",
                "Submit button with loading state",
                "Form validation and error display"
            ],
            prompt_context=PromptContext(
                component_type="form",
                data_model="task",
                interactions=["create"],
                styling_approach="tailwind",
                dependencies=["task-list"]
            ),
            priority=2
        )
    ]
)


if __name__ == "__main__":
    # Rebuild models to ensure proper schema generation
    Section.model_rebuild()
    Response.model_rebuild()
    
    # Print example for reference
    print("Example Response:")
    print(EXAMPLE_RESPONSE.model_dump_json(indent=2))