'use client';

import { memo, useMemo, useCallback, useState, useEffect } from 'react';
import { FixedSizeList as List } from 'react-window';
import { motion, AnimatePresence } from 'framer-motion';
import { ItemCard } from './ItemCard';
import type { ItemSummary } from '@/types';

interface OptimizedItemListProps {
  items: ItemSummary[];
  onItemClick?: (item: ItemSummary) => void;
  onItemLike?: (item: ItemSummary) => void;
  onItemSave?: (item: ItemSummary) => void;
  onItemShare?: (item: ItemSummary) => void;
  onItemSkip?: (item: ItemSummary) => void;
  likedItems?: Set<number>;
  savedItems?: Set<number>;
  height?: number;
  itemHeight?: number;
}

// 虚拟化列表项组件
const VirtualizedItem = memo(({ 
  index, 
  style, 
  data 
}: { 
  index: number; 
  style: React.CSSProperties; 
  data: {
    items: ItemSummary[];
    onItemClick?: (item: ItemSummary) => void;
    onItemLike?: (item: ItemSummary) => void;
    onItemSave?: (item: ItemSummary) => void;
    onItemShare?: (item: ItemSummary) => void;
    onItemSkip?: (item: ItemSummary) => void;
    likedItems?: Set<number>;
    savedItems?: Set<number>;
  };
}) => {
  const item = data.items[index];
  
  if (!item) return null;

  return (
    <div style={style}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: index * 0.05 }}
        className="p-2"
      >
        <ItemCard
          item={item}
          onLike={() => data.onItemLike?.(item)}
          onSave={() => data.onItemSave?.(item)}
          onShare={() => data.onItemShare?.(item)}
          onSkip={() => data.onItemSkip?.(item)}
          isLiked={data.likedItems?.has(item.id) || false}
          isSaved={data.savedItems?.has(item.id) || false}
        />
      </motion.div>
    </div>
  );
});

VirtualizedItem.displayName = 'VirtualizedItem';

// 骨架屏组件
const SkeletonItem = memo(() => (
  <div className="p-4 bg-white rounded-lg shadow-sm border animate-pulse">
    <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
    <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
    <div className="h-3 bg-gray-200 rounded w-2/3 mb-4"></div>
    <div className="flex justify-between items-center">
      <div className="h-3 bg-gray-200 rounded w-1/4"></div>
      <div className="h-3 bg-gray-200 rounded w-1/6"></div>
    </div>
  </div>
));

SkeletonItem.displayName = 'SkeletonItem';

// 主组件
export const OptimizedItemList = memo<OptimizedItemListProps>(({
  items,
  onItemClick,
  onItemLike,
  onItemSave,
  onItemShare,
  onItemSkip,
  likedItems = new Set(),
  savedItems = new Set(),
  height = 600,
  itemHeight = 200
}) => {
  const [isLoading, setIsLoading] = useState(true);
  const [visibleItems, setVisibleItems] = useState<ItemSummary[]>([]);

  // 模拟加载延迟
  useEffect(() => {
    const timer = setTimeout(() => {
      setVisibleItems(items);
      setIsLoading(false);
    }, 500);

    return () => clearTimeout(timer);
  }, [items]);

  // 使用 useMemo 优化数据传递
  const listData = useMemo(() => ({
    items: visibleItems,
    onItemClick,
    onItemLike,
    onItemSave,
    onItemShare,
    onItemSkip,
    likedItems,
    savedItems
  }), [visibleItems, onItemClick, onItemLike, onItemSave, onItemShare, onItemSkip, likedItems, savedItems]);

  // 使用 useCallback 优化回调函数
  const handleItemClick = useCallback((item: ItemSummary) => {
    onItemClick?.(item);
  }, [onItemClick]);

  const handleItemLike = useCallback((item: ItemSummary) => {
    onItemLike?.(item);
  }, [onItemLike]);

  const handleItemSave = useCallback((item: ItemSummary) => {
    onItemSave?.(item);
  }, [onItemSave]);

  const handleItemShare = useCallback((item: ItemSummary) => {
    onItemShare?.(item);
  }, [onItemShare]);

  const handleItemSkip = useCallback((item: ItemSummary) => {
    onItemSkip?.(item);
  }, [onItemSkip]);

  // 渲染骨架屏
  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 5 }).map((_, index) => (
          <SkeletonItem key={index} />
        ))}
      </div>
    );
  }

  // 如果没有项目，显示空状态
  if (visibleItems.length === 0) {
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

  // 如果项目数量较少，使用普通渲染
  if (visibleItems.length <= 10) {
    return (
      <AnimatePresence>
        <div className="space-y-4">
          {visibleItems.map((item, index) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
            >
              <ItemCard
                item={item}
                onLike={() => handleItemLike(item)}
                onSave={() => handleItemSave(item)}
                onShare={() => handleItemShare(item)}
                onSkip={() => handleItemSkip(item)}
                isLiked={likedItems.has(item.id)}
                isSaved={savedItems.has(item.id)}
              />
            </motion.div>
          ))}
        </div>
      </AnimatePresence>
    );
  }

  // 对于大量数据，使用虚拟化列表
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <List
        height={height}
        itemCount={visibleItems.length}
        itemSize={itemHeight}
        itemData={listData}
        overscanCount={5} // 预渲染额外项目以提高滚动性能
      >
        {VirtualizedItem}
      </List>
    </div>
  );
});

OptimizedItemList.displayName = 'OptimizedItemList';

// 导出类型
export type { OptimizedItemListProps };