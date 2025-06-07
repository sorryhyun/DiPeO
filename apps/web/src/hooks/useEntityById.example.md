# useEntityById Hook Examples

## Basic Usage

```typescript
// Before: Manual useMemo pattern
const person = useMemo(() => {
  if (!selectedPersonId) return null;
  const found = persons?.find(p => p.id === selectedPersonId);
  if (!found) return null;
  return found;
}, [selectedPersonId, persons]);

// After: Using useEntityById
const person = useEntityById(selectedPersonId, persons);
```

## With Transformation

```typescript
// Before: Manual transformation
const personData = useMemo(() => {
  if (!selectedPersonId) return null;
  const person = persons?.find(p => p.id === selectedPersonId);
  if (!person) return null;
  return { ...person, type: 'person' as const };
}, [selectedPersonId, persons]);

// After: Using useEntityById with transformer
const personData = useEntityById(
  selectedPersonId,
  persons,
  (person) => ({ ...person, type: 'person' as const })
);
```

## With Context (Complex Transformations)

```typescript
// Before: Complex transformation requiring additional data
const arrowData = useMemo(() => {
  if (!selectedArrowId) return null;
  const arrow = arrows?.find(a => a.id === selectedArrowId);
  if (!arrow || !arrow.data) return null;
  
  const sourceNode = nodes?.find(n => n.id === arrow.source);
  return {
    ...arrow.data,
    type: 'arrow' as const,
    _sourceNodeType: sourceNode?.data.type
  };
}, [selectedArrowId, arrows, nodes]);

// After: Using useEntityByIdWithContext
const arrowData = useEntityByIdWithContext(
  selectedArrowId,
  arrows,
  nodes,
  (arrow, nodes) => {
    if (!arrow.data) return null;
    const sourceNode = nodes?.find(n => n.id === arrow.source);
    return {
      ...arrow.data,
      type: 'arrow' as const,
      _sourceNodeType: sourceNode?.data.type
    };
  }
);
```

## Multiple Lookups in a Component

```typescript
// In ConversationDashboard component
const selectedPerson = useEntityById(dashboardSelectedPerson, persons);
const personLabel = selectedPerson?.label || 'Unknown';

// Instead of repeated inline finds:
// persons.find(p => p.id === dashboardSelectedPerson)?.label
```