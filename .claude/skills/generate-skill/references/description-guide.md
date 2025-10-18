# Effective Skill Descriptions

## The Formula

```
[What it does]. Use when [trigger scenarios] or when the user mentions [keywords].
```

Optional: Add package requirements at the end.

## Good vs Bad

❌ **Bad:** "For PDFs" (too vague)

✅ **Good:** "Extract PDF text, fill forms, merge docs. Use when working with PDFs or when user mentions forms, extraction."

## Key Elements

1. **What it does** - Specific actions (extract, convert, analyze)
2. **When to use** - Scenarios that trigger it
3. **Keywords** - Terms users naturally say

## Common Patterns

**File Processing:**
```
[Action] [file types] including [operations]. Use when working with [file types] or mentions [keywords].
```

**API Integration:**
```
Interact with [API] for [capabilities]. Use when [scenarios] or mentions [API/domain].
```

**Workflow:**
```
[End-to-end process]. Use when [workflow scenario] or mentions [workflow keywords].
```

## Mistakes to Avoid

- ❌ Too generic: "File processing tool"
- ❌ Missing triggers: "Generates SQL queries" (no "when")
- ❌ No keywords: "A tool for charts" (what keywords?)
- ❌ Too narrow: "Rotates PDFs 90 degrees" (too specific)
- ❌ Jargon only: "OAuth 2.0 PKCE" (use plain language)

## Quick Checklist

- [ ] States what it does
- [ ] Includes "Use when" clause
- [ ] Lists keywords users would say
- [ ] Mentions file types/tech if relevant
- [ ] Lists required packages if any
- [ ] Under 300 characters
