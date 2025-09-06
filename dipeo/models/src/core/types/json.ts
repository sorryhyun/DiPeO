// Define recursive JSON-serializable types for strict schema validation
// These types ensure compatibility with OpenAI's structured output requirements

export type JsonPrimitive = string | number | boolean | null;
export type JsonObject = { [key: string]: JsonValue };
export type JsonArray = JsonValue[];
export type JsonValue = JsonPrimitive | JsonObject | JsonArray;

// For backwards compatibility during migration
export type JsonAny = JsonValue;

// Utility type for strict JSON dictionaries
export type JsonDict = Record<string, JsonValue>;
