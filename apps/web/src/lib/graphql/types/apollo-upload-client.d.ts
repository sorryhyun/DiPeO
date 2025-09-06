declare module 'apollo-upload-client' {
  import { ApolloLink } from '@apollo/client';

  export function createUploadLink(options?: {
    uri?: string;
    credentials?: string;
    headers?: Record<string, string>;
    includeExtensions?: boolean;
    fetchOptions?: RequestInit;
    fetch?: typeof fetch;
  }): ApolloLink;
}
