export const i18n = {
  // Update locales as we expand
  locales: ['en', 'zh-CN', 'de', 'fr', 'es', 'ja'] as const,
  defaultLocale: 'en' as const,
};

export type Locale = typeof i18n.locales[number];

export function isSupportedLocale(locale: string | undefined | null): locale is Locale {
  return !!locale && (i18n.locales as readonly string[]).includes(locale);
}

export function getDefaultLocale(): Locale {
  return i18n.defaultLocale;
}

export function negotiateLocale(acceptLanguageHeader: string | null | undefined): Locale {
  if (!acceptLanguageHeader) {
    return i18n.defaultLocale;
  }

  try {
    const ranges = acceptLanguageHeader
      .split(',')
      .map((part) => {
        const [tag, qValue] = part.trim().split(';q=');
        const quality = qValue ? parseFloat(qValue) : 1;
        return { tag: tag.toLowerCase(), quality };
      })
      .sort((a, b) => b.quality - a.quality);

    for (const range of ranges) {
      // Exact match first
      const exact = (i18n.locales as readonly string[]).find(
        (loc) => loc.toLowerCase() === range.tag
      );
      if (exact) return exact as Locale;

      // Match primary subtag (e.g., "en" matches "en-US")
      const primary = range.tag.split('-')[0];
      const primaryMatch = (i18n.locales as readonly string[]).find(
        (loc) => loc.toLowerCase().split('-')[0] === primary
      );
      if (primaryMatch) return primaryMatch as Locale;
    }
  } catch {
    // noop
  }

  return i18n.defaultLocale;
}

