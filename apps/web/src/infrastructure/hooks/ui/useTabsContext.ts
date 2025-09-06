import { useContext } from 'react';
import { TabsContext } from '@/ui/components/common/ui/tabs/TabsContext';

export function useTabsContext() {
  const context = useContext(TabsContext);
  if (!context) {
    throw new Error('useTabsContext must be used within a Tabs component');
  }
  return context;
}
