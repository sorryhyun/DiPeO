/**
 * THIS FILE WAS GENERATED - DO NOT EDIT
 * Generated GraphQL to Domain type mappings
 * Source: dipeo/models/scripts/generate-frontend-mappings.ts
 * Run "make codegen" to regenerate
 */

import type { TypedDocumentNode } from '@apollo/client';
import type * as Domain from '@dipeo/domain-models';
import type * as GraphQL from '@/__generated__/graphql';

// Enum Mappings
export function graphQLNodeTypeToDomain(value: GraphQL.NodeType): Domain.NodeType {
  return value as Domain.NodeType;
}

export function domainNodeTypeToGraphQL(value: Domain.NodeType): GraphQL.NodeType {
  return value as GraphQL.NodeType;
}

export function graphQLHandleDirectionToDomain(value: GraphQL.HandleDirection): Domain.HandleDirection {
  return value as Domain.HandleDirection;
}

export function domainHandleDirectionToGraphQL(value: Domain.HandleDirection): GraphQL.HandleDirection {
  return value as GraphQL.HandleDirection;
}

export function graphQLHandleLabelToDomain(value: GraphQL.HandleLabel): Domain.HandleLabel {
  return value as Domain.HandleLabel;
}

export function domainHandleLabelToGraphQL(value: Domain.HandleLabel): GraphQL.HandleLabel {
  return value as GraphQL.HandleLabel;
}

export function graphQLDataTypeToDomain(value: GraphQL.DataType): Domain.DataType {
  return value as Domain.DataType;
}

export function domainDataTypeToGraphQL(value: Domain.DataType): GraphQL.DataType {
  return value as GraphQL.DataType;
}

export function graphQLForgettingModeToDomain(value: GraphQL.ForgettingMode): Domain.ForgettingMode {
  return value as Domain.ForgettingMode;
}

export function domainForgettingModeToGraphQL(value: Domain.ForgettingMode): GraphQL.ForgettingMode {
  return value as GraphQL.ForgettingMode;
}

export function graphQLMemoryViewToDomain(value: GraphQL.MemoryView): Domain.MemoryView {
  return value as Domain.MemoryView;
}

export function domainMemoryViewToGraphQL(value: Domain.MemoryView): GraphQL.MemoryView {
  return value as GraphQL.MemoryView;
}

export function graphQLDiagramFormatToDomain(value: GraphQL.DiagramFormat): Domain.DiagramFormat {
  return value as Domain.DiagramFormat;
}

export function domainDiagramFormatToGraphQL(value: Domain.DiagramFormat): GraphQL.DiagramFormat {
  return value as GraphQL.DiagramFormat;
}

export function graphQLDBBlockSubTypeToDomain(value: GraphQL.DBBlockSubType): Domain.DBBlockSubType {
  return value as Domain.DBBlockSubType;
}

export function domainDBBlockSubTypeToGraphQL(value: Domain.DBBlockSubType): GraphQL.DBBlockSubType {
  return value as GraphQL.DBBlockSubType;
}

export function graphQLContentTypeToDomain(value: GraphQL.ContentType): Domain.ContentType {
  return value as Domain.ContentType;
}

export function domainContentTypeToGraphQL(value: Domain.ContentType): GraphQL.ContentType {
  return value as GraphQL.ContentType;
}

export function graphQLSupportedLanguageToDomain(value: GraphQL.SupportedLanguage): Domain.SupportedLanguage {
  return value as Domain.SupportedLanguage;
}

export function domainSupportedLanguageToGraphQL(value: Domain.SupportedLanguage): GraphQL.SupportedLanguage {
  return value as GraphQL.SupportedLanguage;
}

export function graphQLHttpMethodToDomain(value: GraphQL.HttpMethod): Domain.HttpMethod {
  return value as Domain.HttpMethod;
}

export function domainHttpMethodToGraphQL(value: Domain.HttpMethod): GraphQL.HttpMethod {
  return value as GraphQL.HttpMethod;
}

export function graphQLHookTypeToDomain(value: GraphQL.HookType): Domain.HookType {
  return value as Domain.HookType;
}

export function domainHookTypeToGraphQL(value: Domain.HookType): GraphQL.HookType {
  return value as GraphQL.HookType;
}

export function graphQLHookTriggerModeToDomain(value: GraphQL.HookTriggerMode): Domain.HookTriggerMode {
  return value as Domain.HookTriggerMode;
}

export function domainHookTriggerModeToGraphQL(value: Domain.HookTriggerMode): GraphQL.HookTriggerMode {
  return value as GraphQL.HookTriggerMode;
}

export function graphQLVoiceModeToDomain(value: GraphQL.VoiceMode): Domain.VoiceMode {
  return value as Domain.VoiceMode;
}

export function domainVoiceModeToGraphQL(value: Domain.VoiceMode): GraphQL.VoiceMode {
  return value as GraphQL.VoiceMode;
}

export function graphQLExecutionStatusToDomain(value: GraphQL.ExecutionStatus): Domain.ExecutionStatus {
  return value as Domain.ExecutionStatus;
}

export function domainExecutionStatusToGraphQL(value: Domain.ExecutionStatus): GraphQL.ExecutionStatus {
  return value as GraphQL.ExecutionStatus;
}

export function graphQLNodeExecutionStatusToDomain(value: GraphQL.NodeExecutionStatus): Domain.NodeExecutionStatus {
  return value as Domain.NodeExecutionStatus;
}

export function domainNodeExecutionStatusToGraphQL(value: Domain.NodeExecutionStatus): GraphQL.NodeExecutionStatus {
  return value as GraphQL.NodeExecutionStatus;
}

export function graphQLEventTypeToDomain(value: GraphQL.EventType): Domain.EventType {
  return value as Domain.EventType;
}

export function domainEventTypeToGraphQL(value: Domain.EventType): GraphQL.EventType {
  return value as GraphQL.EventType;
}

export function graphQLLLMServiceToDomain(value: GraphQL.LLMService): Domain.LLMService {
  return value as Domain.LLMService;
}

export function domainLLMServiceToGraphQL(value: Domain.LLMService): GraphQL.LLMService {
  return value as GraphQL.LLMService;
}

export function graphQLAPIServiceTypeToDomain(value: GraphQL.APIServiceType): Domain.APIServiceType {
  return value as Domain.APIServiceType;
}

export function domainAPIServiceTypeToGraphQL(value: Domain.APIServiceType): GraphQL.APIServiceType {
  return value as GraphQL.APIServiceType;
}

export function graphQLNotionOperationToDomain(value: GraphQL.NotionOperation): Domain.NotionOperation {
  return value as Domain.NotionOperation;
}

export function domainNotionOperationToGraphQL(value: Domain.NotionOperation): GraphQL.NotionOperation {
  return value as GraphQL.NotionOperation;
}

export function graphQLToolTypeToDomain(value: GraphQL.ToolType): Domain.ToolType {
  return value as Domain.ToolType;
}

export function domainToolTypeToGraphQL(value: Domain.ToolType): GraphQL.ToolType {
  return value as GraphQL.ToolType;
}


// Type Conversion Functions
export function convertGraphQLDiagramToDomain(
  graphql: GraphQL.Diagram
): Domain.DomainDiagram {
  return {
    nodes: graphql.nodes.map(item => convertGraphQLNodeToDomain(item)),
    handles: graphql.handles.map(item => convertGraphQLHandleToDomain(item)),
    arrows: graphql.arrows.map(item => convertGraphQLArrowToDomain(item)),
    persons: graphql.persons.map(item => convertGraphQLPersonToDomain(item)),
    metadata: graphql.metadata != null ? graphql.metadata : undefined,
  };
}

export function convertDomainDomainDiagramToGraphQL(
  domain: Domain.DomainDiagram
): Partial<GraphQL.Diagram> {
  return {
    nodes: domain.nodes.map(item => convertDomainDomainNodeToGraphQL(item)),
    handles: domain.handles.map(item => convertDomainDomainHandleToGraphQL(item)),
    arrows: domain.arrows.map(item => convertDomainDomainArrowToGraphQL(item)),
    persons: domain.persons.map(item => convertDomainDomainPersonToGraphQL(item)),
    metadata: domain.metadata != null ? domain.metadata : undefined,
  };
}

export function convertGraphQLNodeToDomain(
  graphql: GraphQL.Node
): Domain.DomainNode {
  return {
    id: graphql.id as Domain.NodeID,
    type: graphql.type,
    position: convertGraphQLVec2ToDomain(graphql.position),
    data: graphql.data,
  };
}

export function convertDomainDomainNodeToGraphQL(
  domain: Domain.DomainNode
): Partial<GraphQL.Node> {
  return {
    id: String(domain.id),
    type: domain.type,
    position: convertDomainVec2ToGraphQL(domain.position),
    data: domain.data,
  };
}

export function convertGraphQLArrowToDomain(
  graphql: GraphQL.Arrow
): Domain.DomainArrow {
  return {
    id: graphql.id as Domain.ArrowID,
    source: graphql.source as Domain.HandleID,
    target: graphql.target as Domain.HandleID,
    content_type: graphql.content_type != null ? graphql.content_type : undefined,
    label: graphql.label != null ? graphql.label : undefined,
    data: graphql.data != null ? graphql.data : undefined,
  };
}

export function convertDomainDomainArrowToGraphQL(
  domain: Domain.DomainArrow
): Partial<GraphQL.Arrow> {
  return {
    id: String(domain.id),
    source: String(domain.source),
    target: String(domain.target),
    content_type: domain.content_type != null ? domain.content_type : undefined,
    label: domain.label != null ? domain.label : undefined,
    data: domain.data != null ? domain.data : undefined,
  };
}

export function convertGraphQLHandleToDomain(
  graphql: GraphQL.Handle
): Domain.DomainHandle {
  return {
    id: graphql.id as Domain.HandleID,
    node_id: graphql.node_id as Domain.NodeID,
    label: graphql.label,
    direction: graphql.direction,
    data_type: graphql.data_type,
    position: graphql.position != null ? graphql.position : undefined,
  };
}

export function convertDomainDomainHandleToGraphQL(
  domain: Domain.DomainHandle
): Partial<GraphQL.Handle> {
  return {
    id: String(domain.id),
    node_id: String(domain.node_id),
    label: domain.label,
    direction: domain.direction,
    data_type: domain.data_type,
    position: domain.position != null ? domain.position : undefined,
  };
}

export function convertGraphQLPersonToDomain(
  graphql: GraphQL.Person
): Domain.DomainPerson {
  return {
    id: graphql.id as Domain.PersonID,
    label: graphql.label,
    llm_config: convertGraphQLPersonLlmConfigToDomain(graphql.llm_config),
    type: graphql.type,
  };
}

export function convertDomainDomainPersonToGraphQL(
  domain: Domain.DomainPerson
): Partial<GraphQL.Person> {
  return {
    id: String(domain.id),
    label: domain.label,
    llm_config: convertDomainPersonLLMConfigToGraphQL(domain.llm_config),
    type: domain.type,
  };
}

export function convertGraphQLApiKeyToDomain(
  graphql: GraphQL.ApiKey
): Domain.DomainApiKey {
  return {
    id: graphql.id as Domain.ApiKeyID,
    label: graphql.label,
    service: graphql.service,
    key: graphql.key != null ? graphql.key : undefined,
  };
}

export function convertDomainDomainApiKeyToGraphQL(
  domain: Domain.DomainApiKey
): Partial<GraphQL.ApiKey> {
  return {
    id: String(domain.id),
    label: domain.label,
    service: domain.service,
    key: domain.key != null ? domain.key : undefined,
  };
}

export function convertGraphQLExecutionToDomain(
  graphql: GraphQL.Execution
): Domain.ExecutionState {
  return {
    id: graphql.id as Domain.ExecutionID,
    status: graphql.status,
    diagram_id: graphql.diagram_id != null ? graphql.diagram_id : undefined,
    started_at: graphql.started_at,
    ended_at: graphql.ended_at != null ? graphql.ended_at : undefined,
    node_states: graphql.node_states,
    node_outputs: graphql.node_outputs,
    token_usage: graphql.token_usage,
    error: graphql.error != null ? graphql.error : undefined,
    variables: graphql.variables,
    duration_seconds: graphql.duration_seconds != null ? graphql.duration_seconds : undefined,
    is_active: graphql.is_active != null ? graphql.is_active : undefined,
    exec_counts: graphql.exec_counts,
    executed_nodes: graphql.executed_nodes,
  };
}

export function convertDomainExecutionStateToGraphQL(
  domain: Domain.ExecutionState
): Partial<GraphQL.Execution> {
  return {
    id: String(domain.id),
    status: domain.status,
    diagram_id: domain.diagram_id != null ? domain.diagram_id : undefined,
    started_at: domain.started_at,
    ended_at: domain.ended_at != null ? domain.ended_at : undefined,
    node_states: domain.node_states,
    node_outputs: domain.node_outputs,
    token_usage: domain.token_usage,
    error: domain.error != null ? domain.error : undefined,
    variables: domain.variables,
    duration_seconds: domain.duration_seconds != null ? domain.duration_seconds : undefined,
    is_active: domain.is_active != null ? domain.is_active : undefined,
    exec_counts: domain.exec_counts,
    executed_nodes: domain.executed_nodes,
  };
}

export function convertGraphQLNodeStateToDomain(
  graphql: GraphQL.NodeState
): Domain.NodeState {
  return {
    status: graphql.status,
    started_at: graphql.started_at != null ? graphql.started_at : undefined,
    ended_at: graphql.ended_at != null ? graphql.ended_at : undefined,
    error: graphql.error != null ? graphql.error : undefined,
    token_usage: graphql.token_usage != null ? graphql.token_usage : undefined,
    output: graphql.output != null ? graphql.output : undefined,
  };
}

export function convertDomainNodeStateToGraphQL(
  domain: Domain.NodeState
): Partial<GraphQL.NodeState> {
  return {
    status: domain.status,
    started_at: domain.started_at != null ? domain.started_at : undefined,
    ended_at: domain.ended_at != null ? domain.ended_at : undefined,
    error: domain.error != null ? domain.error : undefined,
    token_usage: domain.token_usage != null ? domain.token_usage : undefined,
    output: domain.output != null ? domain.output : undefined,
  };
}

export function convertGraphQLVec2ToDomain(
  graphql: GraphQL.Vec2
): Domain.Vec2 {
  return {
    x: graphql.x,
    y: graphql.y,
  };
}

export function convertDomainVec2ToGraphQL(
  domain: Domain.Vec2
): Partial<GraphQL.Vec2> {
  return {
    x: domain.x,
    y: domain.y,
  };
}

export function convertGraphQLDiagramMetadataToDomain(
  graphql: GraphQL.DiagramMetadata
): Domain.DiagramMetadata {
  return {
    id: graphql.id != null ? graphql.id : undefined,
    name: graphql.name != null ? graphql.name : undefined,
    description: graphql.description != null ? graphql.description : undefined,
    version: graphql.version,
    created: graphql.created,
    modified: graphql.modified,
    author: graphql.author != null ? graphql.author : undefined,
    tags: graphql.tags != null ? graphql.tags : undefined,
  };
}

export function convertDomainDiagramMetadataToGraphQL(
  domain: Domain.DiagramMetadata
): Partial<GraphQL.DiagramMetadata> {
  return {
    id: domain.id != null ? domain.id : undefined,
    name: domain.name != null ? domain.name : undefined,
    description: domain.description != null ? domain.description : undefined,
    version: domain.version,
    created: domain.created,
    modified: domain.modified,
    author: domain.author != null ? domain.author : undefined,
    tags: domain.tags != null ? domain.tags : undefined,
  };
}

export function convertGraphQLPersonLlmConfigToDomain(
  graphql: GraphQL.PersonLlmConfig
): Domain.PersonLLMConfig {
  return {
    service: graphql.service,
    model: graphql.model,
    api_key_id: graphql.api_key_id as Domain.ApiKeyID,
    system_prompt: graphql.system_prompt != null ? graphql.system_prompt : undefined,
    voice: graphql.voice != null ? graphql.voice : undefined,
    voice_id: graphql.voice_id != null ? graphql.voice_id : undefined,
    audio_format: graphql.audio_format != null ? graphql.audio_format : undefined,
  };
}

export function convertDomainPersonLLMConfigToGraphQL(
  domain: Domain.PersonLLMConfig
): Partial<GraphQL.PersonLlmConfig> {
  return {
    service: domain.service,
    model: domain.model,
    api_key_id: String(domain.api_key_id),
    system_prompt: domain.system_prompt != null ? domain.system_prompt : undefined,
    voice: domain.voice != null ? domain.voice : undefined,
    voice_id: domain.voice_id != null ? domain.voice_id : undefined,
    audio_format: domain.audio_format != null ? domain.audio_format : undefined,
  };
}

// Helper Functions
export function convertNullable<T, R>(
  value: T | null | undefined,
  converter: (v: T) => R
): R | null | undefined {
  return value != null ? converter(value) : value as null | undefined;
}

export function convertArray<T, R>(
  array: T[],
  converter: (item: T) => R
): R[] {
  return array.map(converter);
}

// Exports
export {
  convertGraphQLDiagramToDomain,
  convertDomainDomainDiagramToGraphQL,
  convertGraphQLNodeToDomain,
  convertDomainDomainNodeToGraphQL,
  convertGraphQLArrowToDomain,
  convertDomainDomainArrowToGraphQL,
  convertGraphQLHandleToDomain,
  convertDomainDomainHandleToGraphQL,
  convertGraphQLPersonToDomain,
  convertDomainDomainPersonToGraphQL,
  convertGraphQLApiKeyToDomain,
  convertDomainDomainApiKeyToGraphQL,
  convertGraphQLExecutionToDomain,
  convertDomainExecutionStateToGraphQL,
  convertGraphQLNodeStateToDomain,
  convertDomainNodeStateToGraphQL,
  convertGraphQLVec2ToDomain,
  convertDomainVec2ToGraphQL,
  convertGraphQLDiagramMetadataToDomain,
  convertDomainDiagramMetadataToGraphQL,
  convertGraphQLPersonLlmConfigToDomain,
  convertDomainPersonLLMConfigToGraphQL,
  // Enum mappings
  graphQLNodeTypeToDomain,
  domainNodeTypeToGraphQL,
  graphQLHandleDirectionToDomain,
  domainHandleDirectionToGraphQL,
  graphQLHandleLabelToDomain,
  domainHandleLabelToGraphQL,
  graphQLDataTypeToDomain,
  domainDataTypeToGraphQL,
  graphQLForgettingModeToDomain,
  domainForgettingModeToGraphQL,
  graphQLMemoryViewToDomain,
  domainMemoryViewToGraphQL,
  graphQLDiagramFormatToDomain,
  domainDiagramFormatToGraphQL,
  graphQLDBBlockSubTypeToDomain,
  domainDBBlockSubTypeToGraphQL,
  graphQLContentTypeToDomain,
  domainContentTypeToGraphQL,
  graphQLSupportedLanguageToDomain,
  domainSupportedLanguageToGraphQL,
  graphQLHttpMethodToDomain,
  domainHttpMethodToGraphQL,
  graphQLHookTypeToDomain,
  domainHookTypeToGraphQL,
  graphQLHookTriggerModeToDomain,
  domainHookTriggerModeToGraphQL,
  graphQLVoiceModeToDomain,
  domainVoiceModeToGraphQL,
  graphQLExecutionStatusToDomain,
  domainExecutionStatusToGraphQL,
  graphQLNodeExecutionStatusToDomain,
  domainNodeExecutionStatusToGraphQL,
  graphQLEventTypeToDomain,
  domainEventTypeToGraphQL,
  graphQLLLMServiceToDomain,
  domainLLMServiceToGraphQL,
  graphQLAPIServiceTypeToDomain,
  domainAPIServiceTypeToGraphQL,
  graphQLNotionOperationToDomain,
  domainNotionOperationToGraphQL,
  graphQLToolTypeToDomain,
  domainToolTypeToGraphQL,
  // Helper functions
  convertNullable,
  convertArray,
};