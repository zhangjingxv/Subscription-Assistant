import type { MetadataRoute } from 'next';
import { i18n } from '@/i18n/config';

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = 'https://attentionsync.io';
  const entries: MetadataRoute.Sitemap = [];
  i18n.locales.forEach((loc) => {
    const locBase = `${baseUrl}/${loc}`;
    entries.push({ url: locBase, changeFrequency: 'daily', priority: 1 });
    entries.push({ url: `${locBase}/search` });
    entries.push({ url: `${locBase}/sources` });
    entries.push({ url: `${locBase}/collections` });
    entries.push({ url: `${locBase}/stats` });
  });
  return entries;
}

