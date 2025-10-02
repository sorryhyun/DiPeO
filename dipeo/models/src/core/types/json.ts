// Define recursive JSON-serializable types for strict schema validation
// These types ensure compatibility with OpenAI's structured output requirements

export type JsonPrimitive = string | number | boolean | null;

// Utility type for strict JSON dictionaries
export type JsonDict = { [key: string]: JsonValue };

export type JsonValue = JsonPrimitive | JsonDict | JsonValue[];
