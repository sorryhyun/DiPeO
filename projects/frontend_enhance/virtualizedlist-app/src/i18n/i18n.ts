// src/i18n/i18n.ts
export type Locale = 'en' | 'es';
export type TranslationKey = string;

type Dict = Record<Locale, Record<string, string>>;

const DICT: Dict = {
  en: {
    title: 'Items',
    loading: 'Loading...',
    error: 'Something went wrong.',
    empty: 'No items found.',
    select: 'Select item',
  },
  es: {
    title: 'Artículos',
    loading: 'Cargando...',
    error: 'Algo salió mal.',
    empty: 'No se encontraron artículos.',
    select: 'Seleccionar artículo',
  },
};

export const t = (key: TranslationKey, locale: Locale = 'en'): string =>
  DICT[locale]?.[key] ?? key;

export const useI18n = (locale: Locale = 'en') => ({
  t: (key: TranslationKey) => t(key, locale),
  locale,
});