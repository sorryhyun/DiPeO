# Forms System Documentation

## Overview

The Forms system provides a modular, composable approach to form management in the DiPeO application. It was created as part of Phase 2 refactoring to eliminate redundancy and establish consistent patterns across form handling.

## Core Hooks

### `useFormState`
- Manages form data, errors, touched fields, and dirty state
- Provides operations for updating fields and resetting form
- Supports re-initialization when initial values change

### `useFormValidation`
- Handles field-level and form-level validation
- Supports async validation
- Configurable validate-on-change and validate-on-blur behavior
- Manages validation state and error messages

### `useFormAutoSave`
- Provides automatic saving functionality with debouncing
- Tracks save state and last saved time
- Handles save errors gracefully
- Can be disabled in read-only modes

### `useAsyncFieldOptions`
- Integrates with React Query for dynamic field options
- Supports field dependencies
- Manages loading and error states for async options
- Caches results for better performance

### `useFormManager`
- Composite hook that combines all form functionality
- Provides a unified API for form management
- Handles form submission
- Integrates all the above hooks seamlessly

## Validation Library

Pre-built validators for common use cases:

- `required` - Ensures field has a value
- `minLength` / `maxLength` - String length validation
- `min` / `max` - Numeric range validation
- `pattern` - Regex pattern matching
- `email` - Email format validation
- `url` - URL format validation
- `integer` - Whole number validation
- `oneOf` - Enum validation
- `compose` - Combine multiple validators
- `conditional` - Apply validation based on conditions
- `dependsOn` - Validation based on other field values

## Usage Example

```typescript
import { useFormManager, required, minLength, compose } from '@/domain/diagram/forms';

const MyForm = () => {
  const form = useFormManager({
    config: {
      initialValues: {
        name: '',
        email: '',
        age: null
      },
      validators: {
        name: compose(required(), minLength(3)),
        email: required('Email is required'),
        age: (value) => ({
          valid: !value || value >= 18,
          errors: value < 18 ? [{ field: 'age', message: 'Must be 18+' }] : []
        })
      }
    },
    autoSave: {
      enabled: true,
      delay: 1000,
      onSave: async (data) => {
        // Save logic here
      }
    }
  });

  return (
    <form onSubmit={form.handlers.handleSubmit}>
      <input
        value={form.formState.data.name}
        onChange={(e) => form.operations.updateField({ 
          field: 'name', 
          value: e.target.value 
        })}
        onBlur={() => form.handlers.handleBlur('name')}
      />
      {form.formState.errors.name && (
        <span>{form.formState.errors.name[0].message}</span>
      )}
      
      <button type="submit" disabled={!form.computed.canSubmit}>
        Submit
      </button>
    </form>
  );
};
```

## Migration from usePropertyManager

The refactored `usePropertyManager` now uses the forms system internally. Key benefits:

1. **Reduced code size**: From ~470 lines to ~280 lines
2. **Better separation of concerns**: Form logic is now modular
3. **Reusability**: Form hooks can be used in other features
4. **Type safety**: Improved TypeScript support throughout
5. **Testing**: Easier to test individual pieces

## Architecture Benefits

- **Modular**: Each hook handles one concern
- **Composable**: Hooks can be combined as needed
- **Extensible**: Easy to add new validators or hooks
- **Performant**: Optimized re-renders and memoization
- **Type-safe**: Full TypeScript support with generics