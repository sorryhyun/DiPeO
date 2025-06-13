# AutoSaveManager Documentation

The `AutoSaveManager` provides intelligent auto-save functionality that only saves when meaningful structural changes occur, avoiding unnecessary saves for cosmetic changes like node positioning.

## Features

- **Structural Change Detection**: Only saves when diagram structure changes (nodes added/removed, connections changed, data modified)
- **Debounced Saves**: Configurable delay to batch rapid changes
- **Efficient Hashing**: Fast detection of changes using structural hashing
- **Save Status Tracking**: Monitor save progress and unsaved changes
- **Error Handling**: Graceful error handling with optional notifications

## Usage

### Direct Usage with Store

```typescript
import { useUnifiedStore } from '@/stores/unifiedStore';
import { AutoSaveManager } from '@/stores/managers';

const store = useUnifiedStore();
const autoSave = new AutoSaveManager(store, {
  debounceMs: 2000,        // Wait 2 seconds after last change
  enabled: true,           // Start enabled
  onSave: (success) => {   // Success callback
    console.log('Saved:', success);
  },
  onError: (error) => {    // Error callback
    console.error('Save failed:', error);
  }
});

// Start monitoring a diagram
autoSave.start('diagram-123');

// Force immediate save
await autoSave.saveNow();

// Check status
const status = autoSave.getStatus();
console.log('Has unsaved changes:', status.hasUnsavedChanges);

// Stop monitoring
autoSave.stop();
```

### React Hook Usage

```typescript
import { useAutoSave } from '@/hooks/useAutoSave';

function DiagramEditor() {
  const { 
    hasUnsavedChanges, 
    saveInProgress, 
    saveNow,
    toggleAutoSave 
  } = useAutoSave({
    diagramId: currentDiagramId,
    enabled: true,
    showNotifications: true,
    debounceMs: 3000
  });

  return (
    <div>
      <button onClick={saveNow} disabled={saveInProgress}>
        Save Now
      </button>
      <button onClick={toggleAutoSave}>
        Toggle Auto-Save
      </button>
      {hasUnsavedChanges && <span>Unsaved changes</span>}
    </div>
  );
}
```

### Auto-Save Indicator Component

```typescript
import { AutoSaveIndicator } from '@/hooks/useAutoSave';

function Header() {
  return (
    <header>
      <h1>Diagram Editor</h1>
      <AutoSaveIndicator className="ml-4" />
    </header>
  );
}
```

## How It Works

### Structural Hashing

The manager creates a hash of the diagram's structure including:
- Number of nodes and arrows
- Node IDs and types
- Connection topology
- Significant data fields per node type

### Ignored Changes

The following changes do NOT trigger auto-save:
- Node position changes
- Selection state changes
- UI state (zoom, pan)
- Cosmetic properties

### Significant Changes

These changes DO trigger auto-save:
- Adding/removing nodes
- Creating/deleting connections
- Modifying node data (prompts, conditions, etc.)
- Changing node types
- Updating person configurations

## Performance Considerations

1. **Efficient Change Detection**: O(n) complexity for detecting changes
2. **Debouncing**: Prevents excessive saves during rapid edits
3. **Minimal Data Transfer**: Only saves necessary data
4. **Background Operation**: Saves don't block UI

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| debounceMs | number | 2000 | Milliseconds to wait after last change |
| enabled | boolean | true | Whether auto-save is initially enabled |
| onSave | function | - | Callback when save completes |
| onError | function | - | Callback when save fails |

## Best Practices

1. **Set Appropriate Debounce**: 2-5 seconds works well for most use cases
2. **Handle Errors**: Always provide error handling for network failures
3. **Show Status**: Use the indicator component to show save status
4. **Manual Save Option**: Always provide a manual save button
5. **Disable During Bulk Operations**: Temporarily disable during imports or large changes