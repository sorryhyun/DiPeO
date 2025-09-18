// Auto-generated TypeScript model for diff_patch node
import { z } from 'zod';

export interface DiffPatchNodeData {
  target_path: string;
  diff: string;
  format?: string | undefined;
  apply_mode?: string | undefined;
  backup?: boolean | undefined;
  validate?: boolean | undefined;
  backup_dir?: string | undefined;
  strip_level?: number | undefined;
  fuzz_factor?: number | undefined;
  reject_file?: string | undefined;
  ignore_whitespace?: boolean | undefined;
  create_missing?: boolean | undefined;
}

// Zod schema for validation
export const DiffPatchNodeDataSchema = z.object({
  target_path: z.string().describe("Path to the file to patch"),
  diff: z.string().describe("Unified diff content to apply"),
  format: z.any().optional().describe("Diff format type"),
  apply_mode: z.any().optional().describe("How to apply the patch"),
  backup: z.boolean().optional().describe("Create backup before patching"),
  validate: z.boolean().optional().describe("Validate patch before applying"),
  backup_dir: z.string().optional().describe("Directory for backup files"),
  strip_level: z.number().min(0).max(10).optional().describe("Strip N leading path components (like patch -pN)"),
  fuzz_factor: z.number().min(0).max(100).optional().describe("Number of lines that can be ignored when matching context"),
  reject_file: z.string().optional().describe("Path to save rejected hunks"),
  ignore_whitespace: z.boolean().optional().describe("Ignore whitespace changes when matching"),
  create_missing: z.boolean().optional().describe("Create target file if it doesn't exist"),
});
