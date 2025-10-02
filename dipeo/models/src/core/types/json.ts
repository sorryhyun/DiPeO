// Define recursive JSON-serializable types for strict schema validation
// These types ensure compatibility with OpenAI's structured output requirements

export type JsonPrimitive = string | number | boolean | null;

// JsonValue must be defined before JsonDict due to recursive reference
export type JsonValue = JsonPrimitive | { [key: string]: JsonValue } | JsonValue[];

// Utility type alias for strict JSON dictionaries
export type JsonDict = { [key: string]: JsonValue };
