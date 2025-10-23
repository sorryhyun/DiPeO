/**
 * GraphQL Queries for ChatGPT Widgets
 *
 * This file contains all GraphQL queries used by the widgets.
 * Types are generated from these queries using @graphql-codegen.
 */

import { gql } from 'graphql-request';

export const GET_EXECUTION_QUERY = gql`
  query GetExecution($executionId: String!) {
    getExecution(execution_id: $executionId) {
      id
      status
      diagram_id
      started_at
      ended_at
      error
      llm_usage {
        input
        output
        cached
        total
      }
      metrics
    }
  }
`;

export const LIST_EXECUTIONS_QUERY = gql`
  query ListExecutions($limit: Float) {
    listExecutions(limit: $limit) {
      id
      status
      diagram_id
      started_at
      ended_at
      error
    }
  }
`;

export const LIST_DIAGRAMS_QUERY = gql`
  query ListDiagrams($limit: Float) {
    listDiagrams(limit: $limit) {
      metadata {
        name
        description
        format
        created
        modified
      }
      nodes {
        id
        type
        position {
          x
          y
        }
        data
      }
      arrows {
        id
        source
        target
        label
        content_type
        data
      }
    }
  }
`;
