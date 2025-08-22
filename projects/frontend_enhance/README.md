# Frontend Enhance - AI-Powered React Application Generator

## Overview

Frontend Enhance is an advanced AI-driven system that generates production-ready React applications through intelligent context selection and iterative refinement. The system uses DiPeO's multi-agent architecture to build complex frontend applications section by section, with each section maintaining awareness of the broader application context.

## Key Features

### 🎯 Intelligent Memory Selection
The project now features an advanced **memory selector** system that intelligently manages context for each code generation section:

- **Context-Aware Generation**: Each section receives precisely the context it needs from previously generated sections
- **Dynamic Memory Management**: Uses LLM-based selection to identify relevant code and patterns from prior sections
- **Dependency Resolution**: Automatically includes dependent sections based on import requirements
- **Keyword-Based Filtering**: Technical keywords help select relevant context (e.g., "React", "TypeScript", "Router" for technical specs)

### 🔄 Iterative Section Generation
- **Section Planning**: AI architect defines the overall application structure and splits work into manageable sections
- **Sequential Building**: Each section builds upon previous ones, maintaining consistency
- **Smart Context Selection**: Only relevant previous sections are included in context, avoiding information overload

### 🚀 Production-Ready Output
- **Modern Stack**: React 18+, TypeScript 5+, Tailwind CSS, Vite
- **Complete Applications**: Generates fully functional apps with routing, state management, and UI components
- **Best Practices**: Follows React best practices, TypeScript strict mode, accessibility standards

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Section Planner │────▶│ Memory Selector  │────▶│ Code Generator  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │                         │
         │                       │                         │
         ▼                       ▼                         ▼
   [Architecture]         [Context Filter]          [React Code]
   [Section Plan]         [Dependencies]            [TypeScript]
   [File Mapping]         [Keywords]                [Components]
```

## Memory Selector System

### How It Works

The memory selector (`memory_selector.py`) provides intelligent context management:

1. **Criteria Building**: Constructs selection criteria based on:
   - Section dependencies (which sections this one needs)
   - Component types (what kind of component is being built)
   - Technical keywords (relevant technologies and patterns)

2. **Context Selection**: Uses an LLM to intelligently select relevant messages from previous generations:
   - Avoids redundant information already in the task preview
   - Respects memory limits (`at_most` parameter)
   - Prioritizes most relevant context

3. **Memory Modes**:
   - **Default**: Includes all relevant context
   - **Selective**: Uses criteria to filter messages
   - **Limited**: Respects `at_most` constraint
   - **GOLDFISH**: No memory (fresh start)

### Configuration Example

```yaml
# In consolidated_generator.light.yaml
- label: Generate Frontend Code
  type: person_job
  props:
    person: Frontend Generator
    memorize_to: "Necessary codes to implement or which are dependent to"
    at_most: 1  # Limit context to most relevant section
    prompt_file: frontend_generator.txt
```

## Project Structure

```
projects/frontend_enhance/
├── README.md                           # This file
├── code/
│   ├── memory_selector.py              # Intelligent context selection
│   └── extract_and_setup_app.py        # App scaffolding and setup
├── prompts/
│   ├── frontend_generator.txt          # Main generation prompt
│   ├── section_planner_format.txt      # Section planning format
│   └── code_evaluator.txt              # Code quality evaluation
├── generated/
│   ├── src/                            # Generated React application
│   │   ├── app/                        # Application core
│   │   ├── features/                   # Feature modules
│   │   └── shared/                     # Shared components
│   ├── consolidated_results.json       # Generation results
│   └── sections_data.json              # Section planning data
├── consolidated_generator.light.yaml    # Main workflow with memory selector
├── section_models.py                   # Pydantic models for sections
└── rename_generated_files.py           # File organization utility
```

## Workflow Execution

### 1. Run the Generator

```bash
dipeo run projects/frontend_enhance/consolidated_generator --light --debug --timeout=180
```

### 2. What Happens

1. **Section Planning**: 
   - Analyzes requirements
   - Creates application architecture
   - Splits into 8-10 manageable sections

2. **Sequential Generation**:
   - Each section is generated with awareness of relevant prior sections
   - Memory selector identifies which previous sections to include
   - Context is limited to avoid overwhelming the model

3. **File Organization**:
   - Generated code is organized into proper file structure
   - Each section typically represents one or more related files

### 3. Run the Generated App

```bash
cd projects/frontend_enhance/generated
pnpm install
pnpm dev
```

## Generated Application Structure

The system generates a complete React application with:

```
generated/
├── src/
│   ├── app/
│   │   ├── main.tsx                 # Application entry
│   │   ├── config/
│   │   │   └── config.ts            # App configuration
│   │   └── routes/
│   │       └── ProtectedRoute.tsx   # Route protection
│   ├── features/
│   │   ├── auth/
│   │   │   └── components/
│   │   │       └── SignIn.tsx       # Authentication
│   │   └── dashboard/
│   │       ├── components/
│   │       │   ├── DashboardLayout.tsx
│   │       │   ├── DataTable.tsx
│   │       │   └── LiveUpdates.tsx
│   │       └── pages/
│   │           └── Dashboard.tsx
│   └── shared/
│       ├── components/
│       │   └── ChartCard.tsx        # Reusable components
│       ├── hooks/
│       │   └── useWebSocket.ts      # Custom hooks
│       └── i18n/
│           └── i18n.ts              # Internationalization
├── package.json                      # Dependencies
├── tsconfig.json                     # TypeScript config
├── vite.config.ts                   # Build configuration
└── tailwind.config.js               # Styling configuration
```

## Section Dependencies Example

Each section declares its dependencies, which the memory selector uses:

```json
{
  "id": "state-management",
  "priority": 4,
  "prompt_context": {
    "dependencies": ["component-requirements", "technical-specifications"],
    "component_type": "state",
    "focus": "Context API and TanStack Query integration"
  }
}
```

## Memory Selector Keywords

The system uses domain-specific keywords to improve context selection:

| Section | Keywords |
|---------|----------|
| component-requirements | Button, Input, Modal, Card, component, props, TypeScript |
| technical-specifications | React, TypeScript, Router, API, Query, Suspense, lazy |
| design-system | Tailwind, theme, dark mode, tokens, CSS, colors |
| state-management | Context, useReducer, TanStack, Query, state, dispatch |
| error-handling | ErrorBoundary, fallback, retry, recovery, error |
| performance | memo, lazy, Suspense, virtualization, optimization |
| accessibility | ARIA, keyboard, focus, a11y, screen reader |
| testing | test, mock, Vitest, RTL, coverage |

## Advanced Features

### Dynamic Memory Limits

The system adjusts memory limits based on section position:

```python
def calculate_memory_limit(section_index, total_sections):
    if section_index <= 2:
        return 3  # Early sections need less context
    elif section_index <= 5:
        return 5  # Middle sections need moderate context
    else:
        return 8  # Later sections may need more context
```

### Intelligent Dependency Detection

Automatically extracts dependencies from generated code:
- Analyzes imports and code patterns
- Detects required npm packages
- Configures build tools appropriately

### Component Discovery

Finds and showcases generated components:
- Extracts exported components
- Identifies interfaces and types
- Creates demo instances automatically

## Customization

### Modify Section Planning

Edit the Section Planner's system prompt in `consolidated_generator.light.yaml`:

```yaml
Section Planner:
  system_prompt: |
    # Your custom planning instructions
```

### Adjust Memory Selection

Configure memory selection per node:

```yaml
memorize_to: "React hooks, state management patterns"
at_most: 5  # Maximum sections to include
```

### Custom Keywords

Add domain-specific keywords in `memory_selector.py`:

```python
keyword_map = {
    "your-section": ["keyword1", "keyword2", "keyword3"]
}
```

## Best Practices

1. **Start Simple**: Begin with basic requirements, add complexity gradually
2. **Review Section Plans**: Check the generated `sections_data.json` before proceeding
3. **Monitor Memory Usage**: Use `--debug` to see what context each section receives
4. **Validate Output**: Always test the generated application locally
5. **Iterate**: Use the feedback from one generation to improve the next

## Troubleshooting

### Low Quality Output
- Simplify requirements initially
- Increase `at_most` for more context
- Review section dependencies

### Missing Dependencies
- Check `extract_and_setup_app.py` detection logic
- Manually add to `package.json` if needed

### Context Overflow
- Reduce `at_most` parameter
- Use more specific `memorize_to` criteria
- Split into smaller sections

### TypeScript Errors
- Verify `tsconfig.json` settings
- Check import paths consistency
- Ensure type definitions are complete

## Future Enhancements

- **Multi-Framework Support**: Vue, Angular, Svelte generation
- **Visual Preview**: Real-time rendering during generation
- **Test Generation**: Comprehensive test suites
- **Design System Integration**: Use existing component libraries
- **Performance Metrics**: Estimate bundle size and performance

## Related Projects

- **dipeodipeo**: AI-powered DiPeO diagram generation
- **codegen**: DiPeO's code generation system
- **DiPeO Core**: The underlying workflow orchestration engine

## Conclusion

Frontend Enhance demonstrates the power of intelligent context management in AI code generation. By using the memory selector to provide precisely the right context for each section, it achieves high-quality, consistent code generation that scales to complex applications. The system proves that with smart context selection, AI can build production-ready frontend applications that maintain architectural coherence across hundreds of files.