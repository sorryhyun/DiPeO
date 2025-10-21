---
name: skill-generator
description: Create new Claude Code skills with proper structure and best practices. Use when the user wants to create a new skill, extend Claude's capabilities, or needs help structuring a SKILL.md file.
---

# Skill Generator

Generate concise, focused Claude Code skills through guided questions.

## Process

Follow these steps:

### 1. Understand the Purpose

Ask:
- "What should this skill help you accomplish?"
- "Give me 2-3 concrete examples of when you'd use it"
- "What would you say to Claude to trigger this?"

### 2. Recommend Structure

Based on use cases:
- **Workflow-based**: Sequential steps (pipeline, workflow)
- **Task-based**: Distinct operations (toolkit with separate commands)
- **Reference/Guidelines**: Standards or specs to follow
- **Capabilities-based**: Integrated system with related features

### 3. Recommend Resources (if needed)

- **Scripts** (`scripts/`) - for automation or repetitive code
- **References** (`references/`) - for API docs, schemas, specs
- **Assets** (`assets/`) - for templates or boilerplate

Most simple skills don't need resources.

### 4. Generate SKILL.md

Create directory and SKILL.md:

```bash
# Personal: ~/.claude/skills/[skill-name]/
# Project: .claude/skills/[skill-name]/
```

**SKILL.md template** (keep it concise - aim for <200 lines):

```yaml
---
name: [hyphen-case-name]
description: [What it does + when to use + trigger keywords]
---

# [Skill Title]

[1-2 sentence overview]

## [Main Section]

[Core instructions - keep focused]

### [Subsection if needed]

[Concrete examples, not lengthy explanations]
```

**Key requirements:**
- Description includes what, when, and triggers
- Use hyphen-case for name
- Keep concise - split long content to references/
- Provide examples over explanations
- Validate YAML frontmatter

### 5. Show Result & Usage

Present the generated skill concisely and explain how to use it:

```
Created: ~/.claude/skills/[name]/SKILL.md

To use:
1. Restart Claude Code
2. Test with: "[example trigger phrase]"

To share: Move to .claude/skills/ and commit
```

## Quick Templates

**Workflow-based:**
```markdown
## Workflow
### Step 1: [Action]
### Step 2: [Process]
### Step 3: [Output]
```

**Task-based:**
```markdown
## Tasks
### 1. [Task]
[Brief description + example]
### 2. [Task]
[Brief description + example]
```

**Reference/Guidelines:**
```markdown
## Guidelines
### [Category]
[Standard/spec + example]
```

## Best Practices

**Effective descriptions:**
- State what it does + when to use + trigger words
- ✅ "Extract PDF text, fill forms, merge docs. Use when working with PDFs."
- ❌ "Helps with data" (too vague)

**Keep it concise:**
- Aim for <200 lines in SKILL.md
- Move details to references/ files
- Prefer examples over lengthy explanations

**Resource organization:**
```
skill-name/
├── SKILL.md           # Main (required)
├── references/        # Docs (optional)
├── scripts/          # Utils (optional)
└── assets/           # Templates (optional)
```

## Common Issues

- **Skill not triggering**: Add more trigger keywords to description
- **YAML invalid**: Check `---` markers are on their own lines
- **Scripts fail**: `chmod +x scripts/*.py`
