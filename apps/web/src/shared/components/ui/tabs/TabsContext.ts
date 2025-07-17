import { createContext } from 'react';

export interface TabsContextValue {
  activeTab: string;
  setActiveTab: (value: string) => void;
}

export const TabsContext = createContext<TabsContextValue | undefined>(undefined);