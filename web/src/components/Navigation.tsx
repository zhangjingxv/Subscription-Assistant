'use client';
import { usePathname } from 'next/navigation';
import {
  HomeIcon,
  MagnifyingGlassIcon,
  RssIcon,
  BookmarkIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import {
  HomeIcon as HomeIconSolid,
  MagnifyingGlassIcon as MagnifyingGlassIconSolid,
  RssIcon as RssIconSolid,
  BookmarkIcon as BookmarkIconSolid,
  ChartBarIcon as ChartBarIconSolid
} from '@heroicons/react/24/solid';
import Link from 'next/link';
import clsx from 'clsx';

const navigation = [
  {
    name: '今日',
    href: '/',
    icon: HomeIcon,
    iconActive: HomeIconSolid,
  },
  {
    name: '发现',
    href: '/search',
    icon: MagnifyingGlassIcon,
    iconActive: MagnifyingGlassIconSolid,
  },
  {
    name: '订阅',
    href: '/sources',
    icon: RssIcon,
    iconActive: RssIconSolid,
  },
  {
    name: '收藏',
    href: '/collections',
    icon: BookmarkIcon,
    iconActive: BookmarkIconSolid,
  },
  {
    name: '统计',
    href: '/stats',
    icon: ChartBarIcon,
    iconActive: ChartBarIconSolid,
  },
];

export function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 safe-bottom">
      <div className="container mx-auto px-4 max-w-4xl">
        <div className="flex items-center justify-around py-2">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            const Icon = isActive ? item.iconActive : item.icon;
            
            return (
              <Link
                key={item.name}
                href={item.href}
                className={clsx(
                  'flex flex-col items-center space-y-1 px-3 py-2 rounded-lg transition-colors duration-200',
                  isActive
                    ? 'text-primary-600 dark:text-primary-400'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                )}
              >
                <Icon className="w-6 h-6" />
                <span className="text-xs font-medium">{item.name}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}