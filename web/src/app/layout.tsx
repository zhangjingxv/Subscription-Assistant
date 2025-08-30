import './globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { Providers } from './providers';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'AttentionSync - 智能信息聚合平台',
  description: '让每个人用3分钟掌握一天的关键信息，永不错过重要机会。',
  keywords: ['信息聚合', 'AI摘要', 'RSS阅读器', '内容管理'],
  authors: [{ name: 'AttentionSync Team' }],
  viewport: 'width=device-width, initial-scale=1',
  themeColor: '#3b82f6',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}