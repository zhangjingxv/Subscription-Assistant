import type { Locale } from './config';

export async function getDictionary(locale: Locale) {
  switch (locale) {
    case 'zh-CN':
      return (await import('./dictionaries/zh-CN')).dictionary;
    case 'de':
    case 'fr':
    case 'es':
    case 'ja':
    case 'en':
    default:
      return (await import('./dictionaries/en')).dictionary;
  }
}

