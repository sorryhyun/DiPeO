// src/i18n/useI18n.ts
import { useMemo } from 'react';
import { Locale, t } from './i18n';

export const useI18n = (locale: Locale = 'en') => {
  const translate = useMemo(() => (k: string) => t(k, locale), [locale]);
  return { t: translate, locale };
};