import { z } from 'zod';
import { DataType, NodeType, HandlePosition } from '@/types/enums';

/**
 * Branded type schemas
 */
export const NodeIDSchema = z.string().brand<'NodeID'>();
export const HandleIDSchema = z.string().regex(/^.+:.+$/).brand<'HandleID'>();
export const ArrowIDSchema = z.string().brand<'ArrowID'>();
export const PersonIDSchema = z.string().brand<'PersonID'>();

/**
 * Primitive schemas
 */
export const Vec2Schema = z.object({
  x: z.number(),
  y: z.number()
});

/**
 * Handle schemas
 */
export const HandleDirectionSchema = z.enum(['input', 'output']);

export const DomainHandleSchema = z.object({
  id: HandleIDSchema,
  nodeId: NodeIDSchema,
  name: z.string(),
  direction: HandleDirectionSchema,
  dataType: z.nativeEnum(DataType),
  position: z.nativeEnum(HandlePosition).optional(),
  offset: z.number().optional(),
  label: z.string().optional(),
  maxConnections: z.number().optional()
});

export const InputHandleSchema = DomainHandleSchema.extend({
  direction: z.literal('input'),
  required: z.boolean().optional(),
  defaultValue: z.unknown().optional()
});

export const OutputHandleSchema = DomainHandleSchema.extend({
  direction: z.literal('output'),
  dynamic: z.boolean().optional()
});

/**
 * Arrow schema
 */
export const DomainArrowSchema = z.object({
  id: ArrowIDSchema,
  source: HandleIDSchema,
  target: HandleIDSchema,
  data: z.record(z.unknown()).optional()
});

/**
 * Person schemas
 */
export const LLMServiceSchema = z.enum(['openai', 'claude', 'gemini', 'groq', 'grok']);
export const ForgettingModeSchema = z.enum(['no_forget', 'on_every_turn', 'upon_request']);

export const DomainPersonSchema = z.object({
  id: PersonIDSchema,
  name: z.string(),
  model: z.string(),
  service: LLMServiceSchema,
  systemPrompt: z.string().optional(),
  temperature: z.number().min(0).max(2).optional(),
  maxTokens: z.number().positive().optional(),
  topP: z.number().min(0).max(1).optional(),
  frequencyPenalty: z.number().min(-2).max(2).optional(),
  presencePenalty: z.number().min(-2).max(2).optional(),
  forgettingMode: ForgettingModeSchema.optional()
});

/**
 * Node data schemas
 */
export const StartNodeDataSchema = z.object({
  label: z.string().optional(),
  customData: z.record(z.unknown()),
  outputDataStructure: z.record(z.string())
});

export const ConditionNodeDataSchema = z.object({
  label: z.string().optional(),
  condition: z.string(),
  detect_max_iterations: z.boolean().optional(),
  _node_indices: z.array(z.string()).optional()
});

export const PersonJobNodeDataSchema = z.object({
  label: z.string().optional(),
  agent: z.string().optional(),
  firstOnlyPrompt: z.string(),
  defaultPrompt: z.string().optional(),
  maxIterations: z.number().positive().optional(),
  no_forget: z.boolean().optional(),
  forget_on_every_turn: z.boolean().optional(),
  forget_upon_request: z.boolean().optional()
});

export const EndpointNodeDataSchema = z.object({
  label: z.string().optional(),
  saveToFile: z.boolean().optional(),
  fileName: z.string().optional()
});

export const DBNodeDataSchema = z.object({
  label: z.string().optional(),
  file: z.string().optional(),
  collection: z.string().optional(),
  operation: z.enum(['query', 'write', 'update', 'delete']).optional(),
  query: z.string().optional(),
  data: z.record(z.unknown()).optional()
});

export const JobNodeDataSchema = z.object({
  label: z.string().optional(),
  codeType: z.enum(['python', 'javascript', 'bash']),
  code: z.string()
});

export const UserResponseNodeDataSchema = z.object({
  label: z.string().optional(),
  prompt: z.string(),
  timeout: z.number().min(1).max(60).optional()
});

export const NotionNodeDataSchema = z.object({
  label: z.string().optional(),
  operation: z.enum(['create', 'read', 'update']),
  pageId: z.string().optional(),
  databaseId: z.string().optional(),
  title: z.string().optional(),
  content: z.string().optional(),
  properties: z.record(z.unknown()).optional()
});

export const PersonBatchJobNodeDataSchema = z.object({
  label: z.string().optional(),
  agent: z.string().optional(),
  process_type: z.enum(['batch', 'sequential']),
  basePrompt: z.string(),
  outputStructure: z.record(z.string()),
  parallelism: z.number().positive().optional()
});

/**
 * Node schemas with specific data validation
 */
export const StartNodeSchema = z.object({
  id: NodeIDSchema,
  type: z.literal('start'),
  position: Vec2Schema,
  data: StartNodeDataSchema
});

export const ConditionNodeSchema = z.object({
  id: NodeIDSchema,
  type: z.literal('condition'),
  position: Vec2Schema,
  data: ConditionNodeDataSchema
});

export const PersonJobNodeSchema = z.object({
  id: NodeIDSchema,
  type: z.literal('person_job'),
  position: Vec2Schema,
  data: PersonJobNodeDataSchema
});

export const EndpointNodeSchema = z.object({
  id: NodeIDSchema,
  type: z.literal('endpoint'),
  position: Vec2Schema,
  data: EndpointNodeDataSchema
});

export const DBNodeSchema = z.object({
  id: NodeIDSchema,
  type: z.literal('db'),
  position: Vec2Schema,
  data: DBNodeDataSchema
});

export const JobNodeSchema = z.object({
  id: NodeIDSchema,
  type: z.literal('job'),
  position: Vec2Schema,
  data: JobNodeDataSchema
});

export const UserResponseNodeSchema = z.object({
  id: NodeIDSchema,
  type: z.literal('user_response'),
  position: Vec2Schema,
  data: UserResponseNodeDataSchema
});

export const NotionNodeSchema = z.object({
  id: NodeIDSchema,
  type: z.literal('notion'),
  position: Vec2Schema,
  data: NotionNodeDataSchema
});

export const PersonBatchJobNodeSchema = z.object({
  id: NodeIDSchema,
  type: z.literal('person_batch_job'),
  position: Vec2Schema,
  data: PersonBatchJobNodeDataSchema
});

/**
 * Union of all node schemas
 */
export const DiagramNodeSchema = z.union([
  StartNodeSchema,
  ConditionNodeSchema,
  PersonJobNodeSchema,
  EndpointNodeSchema,
  DBNodeSchema,
  JobNodeSchema,
  UserResponseNodeSchema,
  NotionNodeSchema,
  PersonBatchJobNodeSchema
]);

/**
 * Type inference
 */
export type ValidatedNode = z.infer<typeof DiagramNodeSchema>;
export type ValidatedHandle = z.infer<typeof DomainHandleSchema>;
export type ValidatedArrow = z.infer<typeof DomainArrowSchema>;
export type ValidatedPerson = z.infer<typeof DomainPersonSchema>;