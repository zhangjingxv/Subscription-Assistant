import { DailyDigest } from '@/components/DailyDigest';
import { Navigation } from '@/components/Navigation';
import { Header } from '@/components/Header';
import { getDictionary } from '@/i18n';

export default async function HomePage({ params }: { params: { locale: string } }) {
  const dict = await getDictionary(params.locale as any);
  const title = (dict as any)?.home?.title || '📅 今日精选';
  const subtitle = (dict as any)?.home?.subtitle
    ? String((dict as any).home.subtitle)
        .replace('{count}', '10')
        .replace('{minutes}', '3')
    : '10条精选内容 · 预计阅读时间 3分钟';
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header />
      <main className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">{title}</h1>
          <p className="text-gray-600 dark:text-gray-400">{subtitle}</p>
        </div>
        <DailyDigest />
      </main>
      <Navigation />
    </div>
  );
}

