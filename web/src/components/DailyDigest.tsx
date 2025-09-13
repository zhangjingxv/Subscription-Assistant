'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
import {
  HeartIcon,
  BookmarkIcon,
  ShareIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline';
import {
  HeartIcon as HeartIconSolid,
  BookmarkIcon as BookmarkIconSolid
} from '@heroicons/react/24/solid';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';
import type { ItemSummary } from '@/types';
import { ItemCard } from './ItemCard';
import { LoadingSpinner } from './LoadingSpinner';

export function DailyDigest() {
  const [currentIndex, setCurrentIndex] = useState(0);
  // removed unused readItems state
  const [likedItems, setLikedItems] = useState<Set<number>>(new Set());
  const [savedItems, setSavedItems] = useState<Set<number>>(new Set());

  const {
    data: digestItems,
    isLoading,
    error,
    refetch
  } = useQuery<ItemSummary[]>({
    queryKey: ['daily-digest'],
    queryFn: async () => {
      const res = await apiClient.getDailyDigest({ limit: 10 });
      return res as ItemSummary[];
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const currentItem = digestItems?.[currentIndex];
  const totalItems = digestItems?.length || 0;
  const progress = totalItems > 0 ? ((currentIndex + 1) / totalItems) * 100 : 0;

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft' && currentIndex > 0) {
        setCurrentIndex(currentIndex - 1);
      } else if (e.key === 'ArrowRight' && currentIndex < totalItems - 1) {
        setCurrentIndex(currentIndex + 1);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentIndex, totalItems]);

  const handleNext = () => {
    if (currentIndex < totalItems - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const handleLike = async (item: ItemSummary) => {
    try {
      await apiClient.recordDigestFeedback(item.id, 'like');
      setLikedItems(prev => new Set(prev).add(item.id));
      toast.success('已标记为喜欢');
    } catch (error) {
      toast.error('操作失败');
    }
  };

  const handleSave = async (item: ItemSummary) => {
    try {
      await apiClient.recordDigestFeedback(item.id, 'save');
      setSavedItems(prev => new Set(prev).add(item.id));
      toast.success('已保存到收藏夹');
    } catch (error) {
      toast.error('保存失败');
    }
  };

  const handleSkip = async (item: ItemSummary) => {
    try {
      await apiClient.recordDigestFeedback(item.id, 'skip');
      handleNext();
    } catch (error) {
      toast.error('操作失败');
    }
  };

  const handleShare = async (item: ItemSummary) => {
    try {
      await apiClient.recordShare(item.id);
      
      if (navigator.share) {
        await navigator.share({
          title: item.title,
          text: item.summary,
          url: item.url,
        });
      } else {
        // Fallback: copy to clipboard
        await navigator.clipboard.writeText(`${item.title}\n${item.url}`);
        toast.success('链接已复制到剪贴板');
      }
    } catch (error) {
      toast.error('分享失败');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner />
        <span className="ml-3 text-gray-600 dark:text-gray-400">正在加载今日精选...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600 dark:text-gray-400 mb-4">加载失败</p>
        <button onClick={() => refetch()} className="btn-primary">
          重试
        </button>
      </div>
    );
  }

  if (!digestItems || digestItems.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">📰</div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
          暂无内容
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          请先添加一些信息源来获取内容
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Progress bar */}
      <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
        <motion.div
          className="bg-primary-500 h-full rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.3 }}
        />
      </div>

      {/* Item counter */}
      <div className="text-center">
        <span className="text-sm text-gray-500 dark:text-gray-400">
          {currentIndex + 1} / {totalItems}
        </span>
      </div>

      {/* Main content area */}
      <div className="relative min-h-[400px]">
        <AnimatePresence mode="wait">
          {currentItem && (
            <motion.div
              key={currentItem.id}
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -50 }}
              transition={{ duration: 0.3 }}
              className="absolute inset-0"
            >
              <ItemCard
                item={currentItem}
                onLike={() => handleLike(currentItem)}
                onSave={() => handleSave(currentItem)}
                onSkip={() => handleSkip(currentItem)}
                onShare={() => handleShare(currentItem)}
                isLiked={likedItems.has(currentItem.id)}
                isSaved={savedItems.has(currentItem.id)}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Navigation controls */}
      <div className="flex items-center justify-between">
        <button
          onClick={handlePrevious}
          disabled={currentIndex === 0}
          className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          上一篇
        </button>

        <div className="flex items-center space-x-2">
          {digestItems.map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentIndex(index)}
              className={clsx(
                'w-2 h-2 rounded-full transition-colors duration-200',
                index === currentIndex
                  ? 'bg-primary-500'
                  : 'bg-gray-300 dark:bg-gray-600 hover:bg-gray-400 dark:hover:bg-gray-500'
              )}
            />
          ))}
        </div>

        <button
          onClick={handleNext}
          disabled={currentIndex === totalItems - 1}
          className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          下一篇
        </button>
      </div>

      {/* Quick actions */}
      {currentItem && (
        <div className="flex items-center justify-center space-x-6 py-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={() => handleLike(currentItem)}
            className={clsx(
              'flex flex-col items-center space-y-1 p-2 rounded-lg transition-colors',
              likedItems.has(currentItem.id)
                ? 'text-red-500'
                : 'text-gray-500 hover:text-red-500'
            )}
          >
            {likedItems.has(currentItem.id) ? (
              <HeartIconSolid className="w-6 h-6" />
            ) : (
              <HeartIcon className="w-6 h-6" />
            )}
            <span className="text-xs">喜欢</span>
          </button>

          <button
            onClick={() => handleSave(currentItem)}
            className={clsx(
              'flex flex-col items-center space-y-1 p-2 rounded-lg transition-colors',
              savedItems.has(currentItem.id)
                ? 'text-primary-500'
                : 'text-gray-500 hover:text-primary-500'
            )}
          >
            {savedItems.has(currentItem.id) ? (
              <BookmarkIconSolid className="w-6 h-6" />
            ) : (
              <BookmarkIcon className="w-6 h-6" />
            )}
            <span className="text-xs">收藏</span>
          </button>

          <button
            onClick={() => handleShare(currentItem)}
            className="flex flex-col items-center space-y-1 p-2 rounded-lg text-gray-500 hover:text-blue-500 transition-colors"
          >
            <ShareIcon className="w-6 h-6" />
            <span className="text-xs">分享</span>
          </button>

          <button
            onClick={() => handleSkip(currentItem)}
            className="flex flex-col items-center space-y-1 p-2 rounded-lg text-gray-500 hover:text-gray-700 transition-colors"
          >
            <EyeSlashIcon className="w-6 h-6" />
            <span className="text-xs">跳过</span>
          </button>
        </div>
      )}

      {/* Completion message */}
      {currentIndex === totalItems - 1 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center py-8 bg-green-50 dark:bg-green-900/20 rounded-lg"
        >
          <div className="text-4xl mb-2">🎉</div>
          <h3 className="text-lg font-medium text-green-800 dark:text-green-200 mb-1">
            今日阅读完成！
          </h3>
          <p className="text-green-600 dark:text-green-400 text-sm">
            您已经掌握了今天的关键信息
          </p>
        </motion.div>
      )}
    </div>
  );
}