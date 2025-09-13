'use client';

import React, { createContext, useContext, useMemo } from 'react';
import type { Locale } from './config';

export interface Messages {
  [key: string]: string | Messages;
}

type TranslationContextValue = {
  locale: Locale | string;
  messages: Messages;
};

const TranslationContext = createContext<TranslationContextValue | null>(null);

export function TranslationProvider({
  locale,
  messages,
  children,
}: {
  locale: Locale | string;
  messages: Messages;
  children: React.ReactNode;
}) {
  const value = useMemo(() => ({ locale, messages }), [locale, messages]);
  return (
    <TranslationContext.Provider value={value}>{children}</TranslationContext.Provider>
  );
}

function getByPath(messages: Messages, path: string): string | Messages | undefined {
  const parts = path.split('.');
  let current: any = messages;
  for (const part of parts) {
    if (current && typeof current === 'object') {
      current = current[part];
    } else {
      return undefined;
    }
  }
  return current;
}

function interpolate(template: string, params?: Record<string, string | number>): string {
  if (!params) return template;
  return template.replace(/\{(\w+)\}/g, (_, key) => String(params[key] ?? ''));
}

export function useTranslation() {
  const ctx = useContext(TranslationContext);
  if (!ctx) {
    return {
      locale: 'en',
      t: (key: string, params?: Record<string, string | number>) =>
        interpolate(key, params),
    } as const;
  }

  const t = (key: string, params?: Record<string, string | number>) => {
    const value = getByPath(ctx.messages, key);
    if (typeof value === 'string') return interpolate(value, params);
    return key;
  };

  return { locale: ctx.locale, t } as const;
}

