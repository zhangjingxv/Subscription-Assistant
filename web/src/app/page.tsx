import { DailyDigest } from '@/components/DailyDigest';
import { Navigation } from '@/components/Navigation';
import { Header } from '@/components/Header';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header />
      
      <main className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            📅 今日精选
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            10条精选内容 · 预计阅读时间 3分钟
          </p>
        </div>
        
        <DailyDigest />
      </main>
      
      <Navigation />
    </div>
  );
}