/**
 * Notion node data interface
 */

import { BaseNodeData } from '../diagram';
import { NotionOperation } from '../integration';

export interface NotionNodeData extends BaseNodeData {
  operation: NotionOperation;
  page_id?: string;
  database_id?: string;
}