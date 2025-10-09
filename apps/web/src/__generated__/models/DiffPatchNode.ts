// Auto-generated TypeScript model for diff_patch node
import { z } from 'zod';

export interface DiffPatchNodeData {
  target_path: string;
  diff: string;
  format?: string | undefined;
  apply_mode?: string | undefined;
  backup_dir?: string | undefined;
  strip_level?: number | undefined;
  fuzz_factor?: number | undefined;
  reject_file?: string | undefined;
}

// Zod schema for validation
export const DiffPatchNodeDataSchema = z.object({
  target_path: z.string().describe("Path to the file to patch"),
  diff: z.string().describe("Unified diff content to apply"),
  format: z.any().optional().describe("Diff format type"),
  apply_mode: z.any().optional().describe("How to apply the patch"),
  backup_dir: z.string().optional().describe("Directory for backup files"),
  strip_level: z.number().min(0).max(10).optional().describe("Strip N leading path components (like patch -pN)"),
  fuzz_factor: z.number().min(0).max(100).optional().describe("Number of lines that can be ignored when matching context"),
  reject_file: z.string().optional().describe("Path to save rejected hunks"),
});
