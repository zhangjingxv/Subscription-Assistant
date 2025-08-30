'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  ClockIcon,
  TagIcon,
  ExternalLinkIcon,
  ChevronDownIcon,
  ChevronUpIcon
} from '@heroicons/react/24/outline';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import clsx from 'clsx';
import type { ItemSummary } from '@/types';

interface ItemCardProps {
  item: ItemSummary;
  onLike: () => void;
  onSave: () => void;
  onSkip: () => void;
  onShare: () => void;
  isLiked: boolean;
  isSaved: boolean;
}

export function ItemCard({
  item,
  onLike,
  onSave,
  onSkip,
  onShare,
  isLiked,
  isSaved
}: ItemCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const handleClick = async () => {
    // Record click and open link
    try {
      await fetch(`/api/v1/items/${item.id}/click`, { method: 'POST' });
      window.open(item.url, '_blank', 'noopener,noreferrer');
    } catch (error) {
      console.error('Failed to record click:', error);
      // Still open the link even if tracking fails
      window.open(item.url, '_blank', 'noopener,noreferrer');
    }
  };

  const getImportanceColor = (score: number) => {
    if (score >= 0.8) return 'border-red-500';
    if (score >= 0.6) return 'border-yellow-500';
    return 'border-gray-300 dark:border-gray-600';
  };

  const getImportanceLabel = (score: number) => {
    if (score >= 0.8) return '重要';
    if (score >= 0.6) return '推荐';
    return '一般';
  };

  const getImportanceBadgeColor = (score: number) => {
    if (score >= 0.8) return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    if (score >= 0.6) return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
    return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
  };

  return (
    <motion.div
      layout
      className={clsx(
        'content-card',
        getImportanceColor(item.importance_score)
      )}
    >
      {/* Header with importance and source */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className={clsx('tag text-xs', getImportanceBadgeColor(item.importance_score))}>
            🔥 {getImportanceLabel(item.importance_score)}
          </span>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {item.source_name}
          </span>
        </div>
        
        {item.published_at && (
          <div className="flex items-center space-x-1 text-xs text-gray-500 dark:text-gray-400">
            <ClockIcon className="w-3 h-3" />
            <span>
              {formatDistanceToNow(new Date(item.published_at), {
                addSuffix: true,
                locale: zhCN
              })}
            </span>
          </div>
        )}
      </div>

      {/* Title */}
      <h2 className="content-card-title cursor-pointer" onClick={handleClick}>
        {item.title}
      </h2>

      {/* Summary */}
      {item.summary && (
        <div className="space-y-2">
          <p className={clsx(
            'content-card-summary',
            !isExpanded && 'text-truncate-3'
          )}>
            {item.summary}
          </p>
          
          {item.summary.length > 150 && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center space-x-1 text-primary-600 dark:text-primary-400 text-sm hover:text-primary-700 dark:hover:text-primary-300 transition-colors"
            >
              {isExpanded ? (
                <>
                  <ChevronUpIcon className="w-4 h-4" />
                  <span>收起</span>
                </>
              ) : (
                <>
                  <ChevronDownIcon className="w-4 h-4" />
                  <span>展开</span>
                </>
              )}
            </button>
          )}
        </div>
      )}

      {/* Topics */}
      {item.topics && item.topics.length > 0 && (
        <div className="flex items-center space-x-2">
          <TagIcon className="w-4 h-4 text-gray-400" />
          <div className="flex flex-wrap gap-1">
            {item.topics.slice(0, 3).map((topic, index) => (
              <span key={index} className="tag-primary">
                #{topic}
              </span>
            ))}
            {item.topics.length > 3 && (
              <span className="tag">
                +{item.topics.length - 3}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Author */}
      {item.author && (
        <div className="text-sm text-gray-600 dark:text-gray-400">
          作者：{item.author}
        </div>
      )}

      {/* Action buttons */}
      <div className="flex items-center justify-between pt-2 border-t border-gray-200 dark:border-gray-700">
        <button
          onClick={handleClick}
          className="flex items-center space-x-1 text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 transition-colors"
        >
          <ExternalLinkIcon className="w-4 h-4" />
          <span className="text-sm">阅读原文</span>
        </button>

        <div className="flex items-center space-x-3">
          <button
            onClick={onLike}
            className={clsx(
              'p-1 rounded transition-colors',
              isLiked
                ? 'text-red-500'
                : 'text-gray-400 hover:text-red-500'
            )}
            title="喜欢"
          >
            ❤️
          </button>

          <button
            onClick={onSave}
            className={clsx(
              'p-1 rounded transition-colors',
              isSaved
                ? 'text-primary-500'
                : 'text-gray-400 hover:text-primary-500'
            )}
            title="收藏"
          >
            🔖
          </button>

          <button
            onClick={onShare}
            className="p-1 rounded text-gray-400 hover:text-blue-500 transition-colors"
            title="分享"
          >
            📤
          </button>

          <button
            onClick={onSkip}
            className="p-1 rounded text-gray-400 hover:text-gray-600 transition-colors"
            title="跳过"
          >
            👁️‍🗨️
          </button>
        </div>
      </div>
    </motion.div>
  );
}