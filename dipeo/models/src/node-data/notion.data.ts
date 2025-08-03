
import { BaseNodeData } from '../diagram';
import { NotionOperation } from '../integration';

export interface NotionNodeData extends BaseNodeData {
  api_key: string;
  database_id: string;
  operation: NotionOperation;
  page_id?: string;
}