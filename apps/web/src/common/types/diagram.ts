// Diagram and state types
import { Node, DiagramNode } from './node';
import { Arrow } from './arrow';
import { PersonDefinition } from './person';
import { ApiKey } from './api';

export interface Diagram {
  nodes: Node[];
  arrows: Arrow[];
  persons: PersonDefinition[];
  metadata?: DiagramMetadata;
}

export interface DiagramMetadata {
  id?: string;
  name?: string;
  description?: string;
  version?: string;
  createdAt?: number;
  updatedAt?: number;
}

export interface DiagramState {
  persons: PersonDefinition[];
  nodes: DiagramNode[];
  arrows: Arrow[];
  apiKeys: ApiKey[];
}