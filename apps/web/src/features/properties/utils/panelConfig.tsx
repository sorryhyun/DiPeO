import React from 'react';
import {
  UserCheckIcon, GitBranchIcon, DatabaseIcon, ArrowRightIcon,
  UserIcon, FlagIcon, Settings
} from 'lucide-react';
import {
  PersonJobPanelContent,
  PersonBatchJobPanelContent,
  ConditionPanelContent,
  DBPanelContent,
  ArrowPanelContent,
  PersonPanelContent,
  EndpointPanelContent,
  JobPanelContent
} from '../components';
import type {
  PersonJobBlockData, PersonBatchJobBlockData, ConditionBlockData, DBBlockData,
  ArrowData, PersonDefinition, EndpointBlockData, JobBlockData
} from '@/shared/types';

export type PanelConfig = {
  [key: string]: {
    icon: React.ReactNode;
    title: string;
    render: (props: any) => React.ReactNode;
  };
};

export const PANEL_CONFIGS: PanelConfig = {
  personJob: {
    icon: <UserCheckIcon className="w-5 h-5" />,
    title: "Person Job Properties",
    render: (props: { nodeId: string; data: PersonJobBlockData }) => 
      <PersonJobPanelContent {...props} />
  },

  personBatchJob: {
    icon: <UserCheckIcon className="w-5 h-5" />,
    title: "Person Batch Job Properties",
    render: (props: { nodeId: string; data: PersonBatchJobBlockData }) => 
      <PersonBatchJobPanelContent {...props} />
  },

  condition: {
    icon: <GitBranchIcon className="w-5 h-5" />,
    title: "Condition Properties",
    render: (props: { nodeId: string; data: ConditionBlockData }) => 
      <ConditionPanelContent {...props} />
  },

  db: {
    icon: <DatabaseIcon className="w-5 h-5" />,
    title: "Database Properties",
    render: (props: { nodeId: string; data: DBBlockData }) => 
      <DBPanelContent {...props} />
  },

  arrow: {
    icon: <ArrowRightIcon className="w-5 h-5" />,
    title: "Arrow Properties",
    render: (props: { arrowId: string; data: ArrowData }) => 
      <ArrowPanelContent {...props} />
  },

  person: {
    icon: <UserIcon className="w-5 h-5" />,
    title: "Person Properties",
    render: (props: { personId: string; data: PersonDefinition }) => 
      <PersonPanelContent {...props} />
  },

  endpoint: {
    icon: <FlagIcon className="w-5 h-5" />,
    title: "Endpoint Properties",
    render: (props: { nodeId: string; data: EndpointBlockData }) => 
      <EndpointPanelContent {...props} />
  },

  job: {
    icon: <Settings className="w-5 h-5" />,
    title: "Job Properties",
    render: (props: { nodeId: string; data: JobBlockData }) => 
      <JobPanelContent {...props} />
  }
};