---
name: skill-generator
description: Create new Claude Code skills with proper structure and best practices. Use when the user wants to create a new skill, extend Claude's capabilities, or needs help structuring a SKILL.md file.
---

# Skill Generator

Generate well-structured Claude Code skills through guided questions and intelligent recommendations.

## Overview

This skill helps create new Claude Code skills by:
- Gathering requirements through targeted questions
- Analyzing use cases to recommend optimal structure
- Generating complete skill directories with SKILL.md and resources
- Following Claude Code best practices automatically

## When to Use This Skill

Trigger this skill when the user:
- Wants to "create a skill" or "make a new skill"
- Asks "how do I extend Claude's capabilities"
- Needs help writing a SKILL.md file
- Mentions creating custom workflows or tools for Claude Code

## Skill Creation Process

Follow these steps in order:

### 1. Understand the Skill Purpose

Ask targeted questions to understand what the skill should do:

**Essential questions:**
- "What should this skill help you accomplish?"
- "Can you give me 3-5 concrete examples of requests this skill should handle?"
- "What would you typically say to Claude that should trigger this skill?"

**Example interaction:**
```
User: I want to create a skill for PDF processing
Claude: Great! Let me help you create that skill. Can you give me 3-5 examples of requests you'd make? For instance:
- "Extract text from this PDF"
- "Merge multiple PDFs"
- What else?
```

### 2. Analyze and Recommend Structure

Based on the use cases, determine the optimal structure:

**Workflow-based** - Use when:
- Use cases involve sequential steps ("first X, then Y")
- Contains keywords: "then", "after", "next", "step"
- Example: Data pipeline (extract → transform → load)

**Task-based** - Use when:
- Use cases are distinct operations
- Contains keywords: "create", "convert", "extract", "process"
- Example: PDF toolkit (merge, split, rotate, extract)

**Reference/Guidelines** - Use when:
- Use cases reference standards or specifications
- Contains keywords: "according to", "following", "guidelines"
- Example: Brand guidelines, coding standards

**Capabilities-based** - Use when:
- Multiple interrelated features
- Integrated system with connected capabilities
- Example: Product management, API integration

**Show your analysis:**
```
Based on your use cases, I recommend a task-based structure because you mentioned distinct operations like "merge", "split", and "extract". 

Would you like to proceed with this structure, or would you prefer a different approach?
```

### 3. Determine Required Resources

Identify what the skill needs:

**Scripts** (`scripts/`) - Recommend when:
- Use cases mention automation or repetitive code
- Operations are error-prone when written manually
- Keywords: "automate", "script", "programmatically"
- Example: PDF rotation, image processing, data transformation

**References** (`references/`) - Recommend when:
- Mentions API documentation, schemas, or specifications
- Complex domain knowledge needed
- Keywords: "api", "schema", "documentation", "guidelines"
- Example: API reference docs, database schemas, company policies

**Assets** (`assets/`) - Recommend when:
- Mentions templates, boilerplate, or starter files
- Keywords: "template", "format", "boilerplate"
- Example: PowerPoint templates, HTML boilerplate, brand assets

**Present recommendations:**
```
For this skill, I recommend including:
✅ Scripts - for PDF manipulation code that would be rewritten often
✅ References - for pdfplumber API documentation
❌ Assets - not needed for this use case

Does this sound right?
```

### 4. Generate the Skill

Create the skill directory structure with all components:

#### 4.1 Create Directory Structure

```bash
# Personal skill
mkdir -p ~/.claude/skills/[skill-name]

# Project skill (for team sharing)
mkdir -p .claude/skills/[skill-name]
```

Use **hyphen-case** for skill names (e.g., `pdf-processor`, `api-helper`).

#### 4.2 Generate SKILL.md

Create a complete SKILL.md following this template:

```yaml
---
name: [skill-name]
description: [Complete description with what it does AND when to use it. Include key trigger words.]
---

# [Skill Title]

## Overview

[1-2 sentences explaining what this skill enables]

## [Main Section - based on structure type]

[Structure-specific content goes here]

## [Additional sections as needed]

[Supporting content]
```

**Critical SKILL.md requirements:**
- Description must include BOTH what it does AND when to use it
- Include trigger keywords users would naturally say
- Use imperative/infinitive verb forms
- Keep under 500 lines (split longer content into reference files)
- Provide concrete examples, not just explanations

#### 4.3 Create Resource Files

**For scripts:**
```python
#!/usr/bin/env python3
"""
[Script purpose]
"""

def main():
    # Implementation here
    pass

if __name__ == "__main__":
    main()
```

Make executable: `chmod +x scripts/*.py`

**For references:**
```markdown
# Reference Documentation

## Table of Contents
- [Overview](#overview)
- [Details](#details)

## Overview
[High-level explanation]

## Details
[Detailed information, API docs, schemas, etc.]
```

**For assets:**
Place template files, images, or boilerplate directly in `assets/` directory.

### 5. Generate Complete Example

Show the user a complete, working example of their SKILL.md:

````markdown
Here's your complete SKILL.md:

```yaml
---
name: pdf-processor
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction. Requires pypdf and pdfplumber packages.
---

# PDF Processor

## Overview

Process PDF files including text extraction, form filling, and document merging.

## Core Tasks

### 1. Extract Text

Use pdfplumber for text extraction:

```python
import pdfplumber
with pdfplumber.open("doc.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

### 2. Merge PDFs

[Implementation details]

### 3. Fill Forms

See [scripts/fill_form.py](scripts/fill_form.py) for the form filling utility.

## Requirements

Install required packages:
```bash
pip install pypdf pdfplumber
```
```

[Continue with scripts/references if needed]
````

### 6. Validate the Skill

Check that the generated skill meets requirements:

**Validation checklist:**
- [ ] YAML frontmatter is valid (starts/ends with `---`)
- [ ] Name uses hyphen-case (lowercase, hyphens only)
- [ ] Description is complete and includes trigger keywords
- [ ] Description mentions when to use the skill
- [ ] No `<` or `>` characters in description
- [ ] File is saved as `SKILL.md` (case-sensitive)
- [ ] Required packages are listed in description or documentation
- [ ] Scripts have execute permissions if included

**Show validation results:**
```
✅ Validating your skill...
✅ YAML frontmatter is valid
✅ Skill name follows conventions
✅ Description is complete and specific
✅ All required files are in place

Your skill is ready to use!
```

### 7. Provide Usage Instructions

Explain how to use the new skill:

```
Your skill is now available! Here's how to use it:

1. The skill is located at: ~/.claude/skills/pdf-processor/
2. Restart Claude Code to load the skill
3. Test it by asking: "Can you extract text from this PDF?"

Claude will automatically use your skill when it matches the request.

To share with your team:
1. Move it to .claude/skills/ in your project
2. Commit to git: git add .claude/skills/
3. Team members get it automatically when they pull
```

## Structure Templates

### Workflow-Based Template

```markdown
## Workflow

Follow this process:

### Step 1: [Initial Step]
[What to do first]

### Step 2: [Processing]
[Main processing logic]

### Step 3: [Output]
[Generate final output]
```

### Task-Based Template

```markdown
## Core Tasks

### 1. [Task Name]
[Task description and usage]

**Usage:**
```[language]
[Example code]
```

### 2. [Task Name]
[Next task]
```

### Reference/Guidelines Template

```markdown
## Guidelines

### Standards
[Define standards]

### Specifications
[Technical specs]

### Best Practices
[Recommendations]

### Examples
[Concrete examples]
```

### Capabilities-Based Template

```markdown
## Core Capabilities

### 1. [Capability Name]
[Description and usage]

### 2. [Capability Name]
[Description and usage]

### 3. Advanced Features
[Additional capabilities]
```

## Best Practices

### Writing Effective Descriptions

**Good description checklist:**
- ✅ States what the skill does clearly
- ✅ Includes when to use it
- ✅ Contains trigger keywords users would say
- ✅ Mentions file types or technologies (if relevant)
- ✅ Lists required packages (if any)

**Examples:**

❌ **Too vague:** "Helps with data"

✅ **Specific:** "Analyze Excel spreadsheets, create pivot tables, and generate charts. Use when working with Excel files, spreadsheets, or analyzing tabular data in .xlsx format."

❌ **Missing triggers:** "Processes PDF documents"

✅ **With triggers:** "Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction."

### Progressive Disclosure

Keep SKILL.md concise by moving detailed content to reference files:

**In SKILL.md:**
```markdown
## Quick Start
[Essential information only]

For detailed API reference, see ./REFERENCE.md.
For examples, see ./EXAMPLES.md.
```

**In REFERENCE.md:**
```markdown
# Complete API Reference
[Comprehensive documentation]
```

This keeps the main skill file focused while providing depth when needed.

### Resource Organization

```
my-skill/
├── SKILL.md           # Main instructions (required)
├── references/        # Detailed documentation (optional)
│   ├── api.md        # API reference
│   └── examples.md   # Extended examples
├── scripts/          # Executable utilities (optional)
│   └── helper.py     # Automation scripts
└── assets/           # Templates and files (optional)
    └── template.txt  # Output templates
```

**Guidelines:**
- Delete unused directories
- Reference files from SKILL.md clearly
- Make scripts executable: `chmod +x scripts/*.py`
- Keep SKILL.md under 500 lines

## Common Patterns

### Pattern 1: File Format Converter

```yaml
---
name: format-converter
description: Convert between file formats including JSON, YAML, CSV, and XML. Use when converting data files or when the user mentions file format conversion.
---

## Core Tasks

### Convert JSON to YAML
### Convert CSV to JSON
### Convert XML to JSON
```

### Pattern 2: API Integration

```yaml
---
name: github-api
description: Interact with GitHub API for repository management, issues, and pull requests. Use when working with GitHub, managing repositories, or automating GitHub tasks.
---

## Core Tasks

### 1. Repository Operations
### 2. Issue Management
### 3. Pull Request Handling

## Resources
See [references/api.md](references/api.md) for complete API documentation.
```

### Pattern 3: Code Quality Tool

```yaml
---
name: code-reviewer
description: Review code for best practices, security issues, and performance. Use when reviewing code, checking pull requests, or analyzing code quality.
allowed-tools: Read, Grep, Glob
---

## Review Checklist
1. Code organization
2. Error handling
3. Security concerns
4. Performance
5. Test coverage
```

## Troubleshooting Generated Skills

If the generated skill doesn't work:

**Skill not activating:**
1. Check if description is specific enough with trigger keywords
2. Verify YAML frontmatter is valid
3. Confirm file is named `SKILL.md` exactly
4. Restart Claude Code

**Scripts not working:**
1. Verify execute permissions: `chmod +x scripts/*.py`
2. Check Python/package installation
3. Use absolute imports in scripts

**Reference files not loading:**
1. Verify file paths use forward slashes
2. Check files are referenced in SKILL.md
3. Ensure markdown link syntax is correct

## Examples

### Example 1: Creating a Simple Skill

**User request:** "Create a skill to help me write commit messages"

**Your process:**
1. Ask: "Can you give me examples of when you'd use this?"
2. User provides: "After I stage changes" and "When reviewing diffs"
3. Analyze: Simple, single-purpose → single file skill
4. Generate SKILL.md with workflow: view diff → generate message
5. Validate and confirm

### Example 2: Creating a Complex Skill

**User request:** "I need a skill for our company's API"

**Your process:**
1. Ask detailed questions about API usage patterns
2. Gather 5+ use cases
3. Analyze: Multiple operations → task-based structure
4. Recommend: scripts for API client, references for API docs
5. Generate complete skill with all resources
6. Show file structure and usage instructions

## Next Steps After Skill Creation

After generating a skill, guide the user:

1. **Test the skill:**
   - Restart Claude Code
   - Try example requests that should trigger it
   - Verify it activates automatically

2. **Iterate based on usage:**
   - Ask user to try it on real tasks
   - Collect feedback on what's missing
   - Refine SKILL.md and resources

3. **Share if needed:**
   - Move to `.claude/skills/` for team sharing
   - Commit to git
   - Consider creating a plugin for broader distribution

## References

For more detailed information on skill creation:
- Claude Code skill documentation
- Best practices for skill authoring
- Progressive disclosure patterns
- Tool permission management with `allowed-tools`
