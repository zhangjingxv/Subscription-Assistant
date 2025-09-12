import type { Metadata } from 'next';
import '../globals.css';
import { Inter } from 'next/font/google';

const inter = Inter({ subsets: ['latin'] });

export async function generateStaticParams() {
  return [
    { locale: 'en' },
    { locale: 'zh-CN' },
    { locale: 'de' },
    { locale: 'fr' },
    { locale: 'es' },
    { locale: 'ja' },
  ];
}

export const metadata: Metadata = {
  title: 'AttentionSync - 智能信息聚合平台',
  description: '让每个人用3分钟掌握一天的关键信息，永不错过重要机会。',
  viewport: 'width=device-width, initial-scale=1',
  themeColor: '#3b82f6',
};

export default function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  return (
    <html lang={params.locale} suppressHydrationWarning>
      <body className={inter.className}>{children}</body>
    </html>
  );
}

