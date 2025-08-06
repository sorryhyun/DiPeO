/**
 * Data type and structure enumerations
 */

export enum DataType {
  ANY = 'any',
  STRING = 'string',
  NUMBER = 'number',
  BOOLEAN = 'boolean',
  OBJECT = 'object',
  ARRAY = 'array'
}

export enum ContentType {
  RAW_TEXT = 'raw_text',
  CONVERSATION_STATE = 'conversation_state',
  OBJECT = 'object',
  EMPTY = 'empty',
  GENERIC = 'generic',
  VARIABLE = 'variable'
}

export enum HandleDirection {
  INPUT = 'input',
  OUTPUT = 'output'
}

export enum HandleLabel {
  DEFAULT = 'default',
  FIRST = 'first',
  CONDTRUE = 'condtrue',
  CONDFALSE = 'condfalse',
  SUCCESS = 'success',
  ERROR = 'error',
  RESULTS = 'results'
}