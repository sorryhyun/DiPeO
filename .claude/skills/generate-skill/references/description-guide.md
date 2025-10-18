# Effective Skill Descriptions

## Why Descriptions Matter

The description is the MOST CRITICAL part of a skill. Claude uses it to decide when to activate your skill, so it must be both informative and discoverable.

## Anatomy of a Good Description

A good description has three parts:

1. **What it does** - Core functionality in clear terms
2. **When to use it** - Specific triggers and use cases  
3. **Context clues** - File types, technologies, or keywords

## The Formula

```
[What it does]. Use when [trigger scenarios] or when the user mentions [keywords].
```

Optional: Add package requirements at the end.

## Examples: Good vs Bad

### Example 1: PDF Processing

❌ **Bad:**
```yaml
description: For PDFs
```

**Problems:**
- Too vague - what about PDFs?
- No trigger scenarios
- Missing keywords

✅ **Good:**
```yaml
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction. Requires pypdf and pdfplumber packages.
```

**Why it works:**
- Clear capabilities (extract, fill, merge)
- Specific triggers (working with PDFs, mentions forms)
- Keywords (PDFs, forms, extraction)
- Lists dependencies

### Example 2: API Integration

❌ **Bad:**
```yaml
description: GitHub integration
```

✅ **Good:**
```yaml
description: Interact with GitHub API for repository management, issues, and pull requests. Use when working with GitHub repositories, managing issues, or automating GitHub workflows.
```

**Why it works:**
- Lists specific operations
- Clear use cases
- Multiple trigger points

### Example 3: Data Processing

❌ **Bad:**
```yaml
description: Helps with data
```

✅ **Good:**
```yaml
description: Analyze Excel spreadsheets, create pivot tables, and generate charts. Use when working with Excel files, spreadsheets, or analyzing tabular data in .xlsx or .csv format.
```

**Why it works:**
- Specific data type (Excel)
- Clear operations (analyze, pivot, chart)
- File format triggers (.xlsx, .csv)

### Example 4: Code Quality

❌ **Bad:**
```yaml
description: Reviews code
```

✅ **Good:**
```yaml
description: Review code for best practices, security vulnerabilities, and performance issues. Use when reviewing pull requests, checking code quality, or analyzing codebases for improvements.
```

**Why it works:**
- Specific review types
- Multiple use case triggers
- Clear value proposition

### Example 5: Brand Guidelines

❌ **Bad:**
```yaml
description: Company branding
```

✅ **Good:**
```yaml
description: Company brand visual identity standards including colors, typography, and logo usage. Use when creating branded content, marketing materials, presentations, or any content requiring brand compliance.
```

**Why it works:**
- Specific guidelines covered
- Multiple content types listed
- Clear compliance purpose

## Common Mistakes

### Mistake 1: Too Generic

❌ Don't:
```yaml
description: File processing tool
```

This could mean anything. Be specific about:
- Which file types?
- What kind of processing?
- When should it activate?

✅ Do:
```yaml
description: Convert image files between formats (PNG, JPEG, WebP) and resize for web optimization. Use when working with images, photos, or when the user mentions image conversion or optimization.
```

### Mistake 2: Missing Triggers

❌ Don't:
```yaml
description: Generates SQL queries from natural language
```

This describes what it does but not when to use it.

✅ Do:
```yaml
description: Generate SQL queries from natural language descriptions. Use when the user asks database questions, needs to query data, or mentions SQL, databases, or data retrieval.
```

### Mistake 3: No Keywords

❌ Don't:
```yaml
description: A tool for making charts
```

No specific keywords for Claude to match against.

✅ Do:
```yaml
description: Create data visualizations and charts from CSV or Excel data. Use when visualizing data, creating graphs, or when the user mentions charts, plots, or data visualization.
```

### Mistake 4: Too Narrow

❌ Don't:
```yaml
description: Rotates PDF pages 90 degrees clockwise
```

Too specific - skill won't activate for other rotation angles.

✅ Do:
```yaml
description: Rotate, merge, split, and manipulate PDF documents. Use when working with PDFs or when the user mentions PDF manipulation, document rotation, or combining PDFs.
```

### Mistake 5: Technical Jargon Only

❌ Don't:
```yaml
description: Implements OAuth 2.0 flow with PKCE extension
```

Users might not know technical terms.

✅ Do:
```yaml
description: Handle user authentication and login flows using OAuth 2.0. Use when implementing user login, authentication, or secure API access. Supports PKCE for enhanced security.
```

## Advanced Patterns

### Pattern 1: Multiple File Types

```yaml
description: Convert between document formats including PDF, DOCX, Markdown, and HTML. Use when converting documents or when the user mentions format conversion, file transformation, or cross-format compatibility.
```

**Key:** List all supported formats explicitly

### Pattern 2: Domain-Specific Workflows

```yaml
description: Manage product roadmaps, prioritize features using RICE framework, and track OKRs. Use when planning product features, prioritizing backlog, or managing product strategy.
```

**Key:** Include methodology names (RICE, OKRs) for discovery

### Pattern 3: Tool with Prerequisites

```yaml
description: Deploy applications to AWS using CloudFormation templates. Use when deploying to AWS, managing cloud infrastructure, or automating deployments. Requires AWS CLI and valid credentials.
```

**Key:** State requirements clearly at the end

### Pattern 4: Read-Only Skills

```yaml
description: Analyze code quality and provide improvement suggestions without modifying files. Use when reviewing code or assessing code quality. Read-only access.
allowed-tools: Read, Grep, Glob
```

**Key:** Make read-only nature explicit, use allowed-tools

### Pattern 5: Multi-Step Workflows

```yaml
description: End-to-end data pipeline: extract from sources, transform data, validate quality, and load to destinations. Use when building ETL pipelines, migrating data, or processing data workflows.
```

**Key:** Describe the flow briefly, include ETL/workflow keywords

## Trigger Word Categories

Include words from relevant categories:

### File Types
- PDF, Excel, CSV, JSON, XML, YAML
- Image, photo, PNG, JPEG, SVG
- Document, DOCX, Markdown
- Video, audio, media

### Actions
- Create, generate, build, make
- Convert, transform, migrate
- Extract, parse, analyze
- Merge, combine, split
- Optimize, compress, resize

### Technologies
- API names (GitHub, Stripe, AWS)
- Frameworks (React, Django, Flask)
- Languages (Python, JavaScript, SQL)
- Protocols (OAuth, REST, GraphQL)

### Domains
- Product management (roadmap, OKR, features)
- Data (ETL, pipeline, analytics)
- Design (brand, guidelines, mockups)
- Development (code review, testing, deployment)

### User Intent
- "working with [X]"
- "when the user mentions [X]"
- "managing [X]"
- "building [X]"
- "analyzing [X]"

## Testing Your Description

Ask yourself:

1. **Would Claude activate this skill for the right requests?**
   - List 3-5 example requests
   - Check if description mentions those scenarios

2. **Does it include the words users would say?**
   - Check for natural language triggers
   - Verify file types and tech names are present

3. **Is it too broad or too narrow?**
   - Too broad: Activates for unrelated requests
   - Too narrow: Misses valid use cases

4. **Are dependencies mentioned?**
   - List required packages
   - Note any credentials needed

## Templates

### File Processing Skill
```yaml
description: [Action] [file types] including [specific operations]. Use when working with [file types] or when the user mentions [keywords].
```

Example:
```yaml
description: Process CSV and Excel files including data cleaning, transformation, and analysis. Use when working with spreadsheets or when the user mentions data processing, CSV, or Excel analysis.
```

### API Integration Skill
```yaml
description: Interact with [API name] for [main capabilities]. Use when [user scenarios] or when the user mentions [API name] or [related terms].
```

Example:
```yaml
description: Interact with Stripe API for payment processing, subscription management, and customer billing. Use when implementing payments or when the user mentions Stripe, payments, or subscriptions.
```

### Workflow Skill
```yaml
description: [End-to-end process description]. Use when [workflow scenarios] or when the user mentions [workflow keywords].
```

Example:
```yaml
description: Complete CI/CD pipeline from code commit to production deployment. Use when setting up deployments or when the user mentions CI/CD, deployment automation, or release management.
```

### Guidelines Skill
```yaml
description: [Type of guidelines] including [specific areas]. Use when creating [outputs] or ensuring [compliance aspect].
```

Example:
```yaml
description: Company coding standards including style guidelines, security practices, and testing requirements. Use when writing code, reviewing pull requests, or ensuring code quality compliance.
```

## Checklist

Before finalizing your description, verify:

- [ ] States what the skill does (core functionality)
- [ ] Includes "Use when" clause with scenarios
- [ ] Lists specific keywords users would say
- [ ] Mentions file types or technologies if relevant
- [ ] Lists required packages if any
- [ ] Is neither too vague nor too narrow
- [ ] Uses natural language (how users talk)
- [ ] Doesn't contain `<` or `>` characters
- [ ] Is under 500 characters (aim for 200-300)

## Real-World Examples from Public Skills

### docx Skill
```yaml
description: Comprehensive document creation, editing, and analysis with support for tracked changes, comments, formatting preservation, and text extraction. When Claude needs to work with professional documents (.docx files) for: (1) Creating new documents, (2) Modifying or editing content, (3) Working with tracked changes, (4) Adding comments, or any other document tasks
```

**Why it works:**
- Lists all capabilities upfront
- Specific file type (.docx)
- Numbered use cases for clarity
- Professional context

### pdf Skill
```yaml
description: Comprehensive PDF manipulation toolkit for extracting text and tables, creating new PDFs, merging/splitting documents, and handling forms. When Claude needs to fill in a PDF form or programmatically process, generate, or analyze PDF documents at scale.
```

**Why it works:**
- "Comprehensive toolkit" sets scope
- Lists specific operations
- Mentions forms (common use case)
- "At scale" indicates automation capability
