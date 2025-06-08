import { HandleID } from './branded';
import { DataType, ArrowType } from './enums';
import { DomainArrow, isDomainArrow, parseHandleId, connectsNodes } from './domain/arrow';

// Re-export domain arrow types for backward compatibility
export type Arrow = DomainArrow & {
  type?: ArrowType;
  selected?: boolean;
  data?: {
    label?: string;
    [key: string]: unknown;
  };
};

// Arrow data type (can be extended in the future)
export interface ArrowData {
  label?: string;
  [key: string]: unknown;
}

// For backward compatibility - these are now simple aliases
export type TypedArrow = Arrow;
export type HandleRef = HandleID;

// Re-export domain type guard with alias
export const isArrow = isDomainArrow;

// Helper to create a handle reference (now just returns the HandleID)
export function createHandleRef(
  _nodeType: unknown,
  _handleName: unknown,
  handleId: HandleID
): HandleID {
  return handleId;
}

// Helper to check if two data types are compatible at runtime
export function areDataTypesCompatible(from: DataType, to: DataType): boolean {
  // Any type is compatible with everything
  if (from === DataType.Any || to === DataType.Any) return true;
  
  // Same types are compatible
  if (from === to) return true;
  
  // Check special compatibility rules
  const compatibilityMap: Record<DataType, DataType[]> = {
    [DataType.String]: [DataType.Text],
    [DataType.Text]: [DataType.String],
    [DataType.Number]: [DataType.Float, DataType.Integer],
    [DataType.Float]: [DataType.Number],
    [DataType.Integer]: [DataType.Number],
    [DataType.Object]: [DataType.JSON],
    [DataType.JSON]: [DataType.Object],
    [DataType.Boolean]: [],
    [DataType.Array]: [],
    [DataType.Any]: [] // Already handled above
  };
  
  return compatibilityMap[from]?.includes(to) ?? false;
}

// Re-export domain utilities
export { parseHandleId, connectsNodes };