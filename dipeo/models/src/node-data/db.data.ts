/**
 * DB node data interface
 */

import { BaseNodeData } from '../diagram';
import { DBBlockSubType } from '../enums';

export interface DBNodeData extends BaseNodeData {
  file?: string;
  collection?: string;
  sub_type: DBBlockSubType;
  operation: string;
  query?: string;
  data?: Record<string, any>;
}