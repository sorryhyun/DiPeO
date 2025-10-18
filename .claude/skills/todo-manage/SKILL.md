---
name: todo-manage
description: Manage and organize TODO.md at project root - plan features, track progress, mark tasks complete, and clean up completed items. Use when planning tasks, organizing work, reviewing priorities, or managing the project TODO list. Access via /dipeotodos command.
---

# TODO List Manager

This guide is for managing and organizing the project TODO list (`TODO.md` at project root). Use this to plan work, track progress, and maintain an organized task management system.

**IMPORTANT**: Manage `TODO.md` at the project root, accessible via `/dipeotodos`.

## Core Responsibilities

### 1. Task Planning & Organization
- Break down feature requests into specific, actionable tasks
- Organize by priority (High/Medium/Low), category, or project area
- Create clear descriptions with acceptance criteria when appropriate
- Add estimated effort or complexity indicators
- Group related tasks into logical sections or milestones
- Note which expert sub-agents are responsible for each task

### 2. Task Tracking & Updates
- Mark tasks as complete when work is finished
- Update task status and progress notes
- Add blockers or dependencies when identified
- Track who is working on what (if relevant)
- Maintain timestamps for creation and completion

### 3. Cleanup & Maintenance
- Remove completed tasks after a reasonable period
- Consolidate duplicate or overlapping tasks
- Archive old completed tasks to separate section if needed
- Reorganize for clarity and usability
- Remove stale or obsolete tasks

### 4. Proactive Management
- Suggest next tasks based on priority and dependencies
- Identify tasks that are blocked or need attention
- Recommend breaking down large tasks
- Flag tasks pending too long

## Format Standards

```markdown
# DiPeO Project Todos

## High Priority
- [ ] Task description with clear action items
  - Acceptance criteria or details
  - Estimated effort: [Small/Medium/Large]
  - Dependencies: [if any]

## Medium Priority
- [ ] Another task

## Low Priority / Future Enhancements
- [ ] Nice-to-have features

## In Progress
- [ ] Currently being worked on
  - Started: YYYY-MM-DD
  - Assigned to: [name/agent]

## Completed (Recent)
- [x] Completed task (YYYY-MM-DD)
```

## Phase-Based Organization (IMPORTANT)

When organizing TODO.md, **always group tasks into logical phases** (3-4 recommended):
- **Phase 1**: Foundation/High Priority - immediate work with high impact
- **Phase 2**: Structural Improvements - medium priority architectural work
- **Phase 3**: Polish & Consistency - standardization and documentation
- **Phase 4**: Future Improvements - low priority enhancements

**Key principles**:
- Group by dependencies and logical workflow
- Each phase should have clear focus and estimated effort
- Remove completed tasks to keep file focused
- Maintain phase structure when adding new tasks
- Avoid scattered, unorganized lists

## Scope Management & Communication

**Be ambitious and proactive** in organizing and creating tasks.

1. **Assess workload first**: Read TODO.md and assess total tasks
2. **Set ambitious objectives**: Be comprehensive in scope
3. **Communicate scope back**: Report tasks and categories, suggest execution plan
4. **Batch work ambitiously**:
   - Small (1-5 tasks): Proceed directly
   - Medium (6-15 tasks): Organize comprehensively with full plan
   - Large (15+ tasks): Organize into phases with multi-session strategy
5. **Be proactive**: Suggest related improvements, break down large tasks, identify technical debt
6. **Status reporting**: Summarize accomplishments, remaining tasks, next priorities

## Operational Guidelines

1. **Always read TODO.md first** before making changes
2. **Be specific**: Tasks should be clear to anyone
3. **Maintain context**: Include enough detail for future reference
4. **Balance detail**: Enough info without overwhelming
5. **Regular cleanup**: Remove completed tasks after 1-2 weeks
6. **Preserve history**: Archive important completed tasks
7. **Cross-reference**: Link to relevant files/issues when helpful
8. **Prioritize ruthlessly**: Not everything can be high priority
9. **Slash command integration**: Users can view via `/dipeotodos`

## Decision Framework

**When adding tasks**:
- Is it specific and actionable?
- Clear success criteria?
- Appropriate priority level?
- Dependencies noted?

**When cleaning up**:
- Completed for more than 2 weeks?
- Still relevant to project goals?
- Archive rather than delete?
- Related tasks to consolidate?

**When prioritizing**:
- Business/user impact?
- Blocking dependencies?
- Effort-to-value ratio?
- Aligns with current focus?

## Quality Control

- Consistent checkbox syntax: `- [ ]` or `- [x]`
- Priority sections clearly separated
- Completed tasks have completion dates
- Task descriptions clear and actionable
- File structure clean and scannable

## Edge Cases

- **No TODO.md exists**: Create at project root with clean structure starting with "# DiPeO Project Todos"
- **Conflicting priorities**: Ask for clarification or use best judgment
- **Unclear tasks**: Break into subtasks or ask questions
- **Large cleanup needed**: Summarize and ask for confirmation
- **Cross-project tasks**: Clearly indicate which component

The goal is to maintain `TODO.md` as a reliable, up-to-date source of truth for what needs to be done, what's in progress, and what's been completed.
