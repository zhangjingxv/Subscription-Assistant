'use client';

import React from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { i18n } from '@/i18n/config';

function extractLocaleFromPath(pathname: string): string | null {
  const seg = pathname.split('/')[1];
  return i18n.locales.includes(seg as any) ? seg : null;
}

export function LanguageSwitcher() {
  const router = useRouter();
  const pathname = usePathname();
  const currentLocale = extractLocaleFromPath(pathname || '/') || i18n.defaultLocale;

  const onChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const nextLocale = e.target.value;
    document.cookie = `NEXT_LOCALE=${nextLocale}; path=/; max-age=${60 * 60 * 24 * 365}`;

    const segments = (pathname || '/').split('/');
    if ((i18n.locales as readonly string[]).some((l) => l === segments[1])) {
      segments[1] = nextLocale;
    } else {
      segments.splice(1, 0, nextLocale);
    }
    const nextPath = segments.join('/') || `/${nextLocale}`;
    router.push(nextPath);
  };

  return (
    <select
      aria-label="Select language"
      value={currentLocale}
      onChange={onChange}
      className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm rounded-md px-2 py-1"
   >
      {(i18n.locales as readonly string[]).map((loc) => (
        <option key={loc} value={loc}>{loc}</option>
      ))}
    </select>
  );
}

