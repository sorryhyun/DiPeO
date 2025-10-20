/**
 * GraphQL Queries for ChatGPT Widgets
 *
 * This file contains all GraphQL queries used by the widgets.
 * Types are generated from these queries using @graphql-codegen.
 */

import { gql } from 'graphql-request';

export const GET_EXECUTION_QUERY = gql`
  query GetExecution($sessionId: String!) {
    execution(sessionId: $sessionId) {
      sessionId
      status
      diagramName
      startedAt
      completedAt
      metadata
    }
  }
`;

export const LIST_EXECUTIONS_QUERY = gql`
  query ListExecutions($limit: Int) {
    executions(limit: $limit) {
      sessionId
      status
      diagramName
      startedAt
      completedAt
    }
  }
`;

export const LIST_DIAGRAMS_QUERY = gql`
  query ListDiagrams {
    diagrams {
      id
      name
      description
      format
      createdAt
      nodeCount
    }
  }
`;
