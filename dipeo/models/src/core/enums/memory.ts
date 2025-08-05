/**
 * Memory management enumerations
 */

export enum MemoryView {
  ALL_INVOLVED = 'all_involved',
  SENT_BY_ME = 'sent_by_me',
  SENT_TO_ME = 'sent_to_me',
  SYSTEM_AND_ME = 'system_and_me',
  CONVERSATION_PAIRS = 'conversation_pairs',
  ALL_MESSAGES = 'all_messages',
}

export enum MemoryProfile {
  FULL = 'FULL',
  FOCUSED = 'FOCUSED',
  MINIMAL = 'MINIMAL',
  GOLDFISH = 'GOLDFISH',
  CUSTOM = 'CUSTOM'
}