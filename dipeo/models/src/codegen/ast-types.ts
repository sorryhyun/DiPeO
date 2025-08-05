/**
 * AST Parser result types
 * These types define the structure of parsed AST information
 * from various programming languages
 */

export interface ParseResult {
  ast: any;
  interfaces: InterfaceInfo[];
  types: TypeAliasInfo[];
  enums: EnumInfo[];
  classes?: ClassInfo[];
  functions?: FunctionInfo[];
  constants?: ConstantInfo[];
  error?: string;
}

export interface InterfaceInfo {
  name: string;
  properties: PropertyInfo[];
  extends?: string[];
  isExported: boolean;
  jsDoc?: string;
}

export interface PropertyInfo {
  name: string;
  type: string;
  optional: boolean;
  readonly: boolean;
  jsDoc?: string;
}

export interface TypeAliasInfo {
  name: string;
  type: string;
  isExported: boolean;
  jsDoc?: string;
}

export interface EnumInfo {
  name: string;
  members: EnumMember[];
  isExported: boolean;
  jsDoc?: string;
}

export interface EnumMember {
  name: string;
  value?: string | number;
}

export interface ClassInfo {
  name: string;
  properties: PropertyInfo[];
  methods: MethodInfo[];
  extends?: string;
  implements?: string[];
  isExported: boolean;
  jsDoc?: string;
}

export interface MethodInfo {
  name: string;
  parameters: ParameterInfo[];
  returnType: string;
  isAsync: boolean;
  jsDoc?: string;
}

export interface ParameterInfo {
  name: string;
  type: string;
  optional: boolean;
  defaultValue?: string;
}

export interface FunctionInfo {
  name: string;
  parameters: ParameterInfo[];
  returnType: string;
  isAsync: boolean;
  isExported: boolean;
  jsDoc?: string;
}

export interface ConstantInfo {
  name: string;
  type: string;
  value: any;
  isExported: boolean;
  jsDoc?: string;
}

// Batch processing types
export interface BatchInput {
  sources: {
    [key: string]: string;
  };
}

export interface BatchResult {
  results: {
    [key: string]: ParseResult;
  };
  metadata?: {
    totalFiles: number;
    successCount: number;
    failureCount: number;
    processingTimeMs: number;
  };
}