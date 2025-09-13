import type { Metadata } from 'next';
import '../globals.css';
import { Inter } from 'next/font/google';
import { Providers } from '../providers';
import { TranslationProvider } from '@/i18n/TranslationProvider';
import { getDictionary } from '@/i18n';
import { i18n } from '@/i18n/config';

const inter = Inter({ subsets: ['latin'] });

export async function generateStaticParams() {
  return i18n.locales.map((l) => ({ locale: l }));
}

export async function generateMetadata({ params }: { params: { locale: string } }): Promise<Metadata> {
  const baseUrl = 'https://attentionsync.io';
  const alternates: Record<string, string> = {};
  for (const l of i18n.locales) {
    alternates[l] = `${baseUrl}/${l}`;
  }
  return {
    title: 'AttentionSync - 智能信息聚合平台',
    description: '让每个人用3分钟掌握一天的关键信息，永不错过重要机会。',
    alternates: {
      canonical: `${baseUrl}/${params.locale}`,
      languages: alternates,
    },
  };
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  const messages = await getDictionary(params.locale as any);
  return (
    <html lang={params.locale} suppressHydrationWarning>
      <body className={inter.className}>
        <TranslationProvider locale={params.locale} messages={messages}>
          <Providers>{children}</Providers>
        </TranslationProvider>
      </body>
    </html>
  );
}

