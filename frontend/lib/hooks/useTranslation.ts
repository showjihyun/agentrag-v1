/**
 * Translation hook for easy i18n integration
 */

import { useCallback } from 'react';
import { useAppStore } from '../stores/app-store';
import { getTranslation, TranslationKey } from '../i18n/translations';
import { Locale } from '../i18n/config';

export function useTranslation() {
  const locale = useAppStore((state) => state.locale);
  const setLocale = useAppStore((state) => state.setLocale);

  const t = useCallback(
    (key: TranslationKey, params?: Record<string, string | number>): string => {
      let text = getTranslation(locale, key);

      // Replace parameters
      if (params) {
        Object.entries(params).forEach(([key, value]) => {
          text = text.replace(`{${key}}`, String(value));
        });
      }

      return text;
    },
    [locale]
  );

  return {
    t,
    locale,
    setLocale,
  };
}

// Utility hook for locale-specific formatting
export function useLocaleFormat() {
  const locale = useAppStore((state) => state.locale);

  const formatDate = useCallback(
    (date: Date) => {
      return new Intl.DateTimeFormat(locale).format(date);
    },
    [locale]
  );

  const formatNumber = useCallback(
    (num: number) => {
      return new Intl.NumberFormat(locale).format(num);
    },
    [locale]
  );

  const formatCurrency = useCallback(
    (amount: number, currency = 'USD') => {
      return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency,
      }).format(amount);
    },
    [locale]
  );

  return {
    formatDate,
    formatNumber,
    formatCurrency,
  };
}
