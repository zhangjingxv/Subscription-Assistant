/**
 * 虚拟化内容列表组件
 * 支持大量数据的高性能渲染
 */

import React, { useState, useEffect, useCallback } from 'react';
import { FixedSizeList as List, ListChildComponentProps } from 'react-window';
import { useVirtualizer } from '@tanstack/react-virtual';
// Removed react-window-infinite-loader due to React 18 peer conflict
import { useInView } from 'react-intersection-observer';
import { motion, AnimatePresence } from 'framer-motion';
import { ItemCard } from './ItemCard';
import { LoadingSpinner } from './LoadingSpinner';
import type { ItemSummary } from '@/types';

interface VirtualizedItemListProps {
  items: ItemSummary[];
  hasNextPage?: boolean;
  isNextPageLoading?: boolean;
  loadNextPage?: () => Promise<void>;
  onItemAction?: (item: ItemSummary, action: string) => void;
  itemHeight?: number;
  containerHeight?: number;
  enableInfiniteScroll?: boolean;
}

// 单个列表项组件
const ListItem = React.memo<ListChildComponentProps<ItemSummary[]>>(
  ({ index, style, data }) => {
    const item = data[index];
    const [isVisible, setIsVisible] = useState(false);

    // 使用 Intersection Observer 优化渲染
    const { ref, inView } = useInView({
      threshold: 0.1,
      triggerOnce: true,
    });

    useEffect(() => {
      if (inView) {
        setIsVisible(true);
      }
    }, [inView]);

    if (!item) {
      return (
        <div style={style} className="flex items-center justify-center">
          <LoadingSpinner size="sm" />
        </div>
      );
    }

    return (
      <div style={style} ref={ref}>
        <AnimatePresence>
          {isVisible && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="px-4 py-2"
            >
              <ItemCard
                item={item}
                onLike={() => {/* 处理点赞 */}}
                onSave={() => {/* 处理保存 */}}
                onShare={() => {/* 处理分享 */}}
                onSkip={() => {/* 处理跳过 */}}
                isLiked={false}
                isSaved={false}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }
);

ListItem.displayName = 'ListItem';

export function VirtualizedItemList({
  items,
  hasNextPage = false,
  isNextPageLoading = false,
  loadNextPage,
  onItemAction,
  itemHeight = 200,
  containerHeight = 600,
  enableInfiniteScroll = true,
}: VirtualizedItemListProps) {
  // mark onItemAction as referenced (used in Tanstack variant)
  void onItemAction;
  // remove unused local state to satisfy lint
  // const [scrollOffset, setScrollOffset] = useState(0);

  // 计算列表项数量（包括加载项）
  const itemCount = hasNextPage ? items.length + 1 : items.length;

  // 检查项目是否已加载
  const isItemLoaded = useCallback(
    (index: number) => !!items[index],
    [items]
  );

  // 加载更多项目
  const loadMoreItems = useCallback(async () => {
    if (isNextPageLoading || !loadNextPage) return;
    
    try {
      await loadNextPage();
    } catch (error) {
      console.error('Failed to load more items:', error);
    }
  }, [isNextPageLoading, loadNextPage]);

  // 渲染单个项目
  const renderItem = useCallback(
    ({ index, style }: ListChildComponentProps) => {
      const item = items[index];

      // 如果是加载项
      if (!item) {
        return (
          <div style={style} className="flex items-center justify-center">
            <LoadingSpinner size="sm" />
            <span className="ml-2 text-gray-500">加载更多...</span>
          </div>
        );
      }

      return (
        <ListItem
          index={index}
          style={style}
          data={items}
        />
      );
    },
    [items]
  );

  // 处理滚动事件
  const handleScroll = useCallback(() => {}, []);

  // 无限滚动版本
  if (enableInfiniteScroll && loadNextPage) {
    return (
      <div className="w-full" style={{ height: containerHeight }}>
        <List
          height={containerHeight}
          itemCount={itemCount}
          itemSize={itemHeight}
          itemData={items}
          onScroll={({ scrollOffset }) => {
            handleScroll();
            // trigger load when near end
            const nearEnd = scrollOffset > itemHeight * (itemCount - 10);
            if (nearEnd && !isNextPageLoading) {
              loadMoreItems();
            }
          }}
          overscanCount={5}
          width="100%"
        >
          {renderItem}
        </List>
      </div>
    );
  }

  // 普通虚拟化版本
  return (
    <div className="w-full" style={{ height: containerHeight }}>
      <List
        height={containerHeight}
        itemCount={items.length}
        itemSize={itemHeight}
        itemData={items}
        onScroll={handleScroll}
        overscanCount={5}
        width="100%"
      >
        {renderItem}
      </List>
    </div>
  );
}

// 使用 @tanstack/react-virtual 的替代实现
export function VirtualizedItemListTanstack({
  items,
  hasNextPage = false,
  isNextPageLoading = false,
  loadNextPage,
  onItemAction,
  itemHeight = 200,
  containerHeight = 600,
}: VirtualizedItemListProps) {
  const parentRef = React.useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: hasNextPage ? items.length + 1 : items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => itemHeight,
    overscan: 5,
  });

  // 无限滚动检测
  useEffect(() => {
    const lastItem = virtualizer.getVirtualItems().slice(-1)[0];
    
    if (!lastItem) return;
    
    if (
      lastItem.index >= items.length - 1 &&
      hasNextPage &&
      !isNextPageLoading &&
      loadNextPage
    ) {
      loadNextPage();
    }
  }, [
    hasNextPage,
    loadNextPage,
    isNextPageLoading,
    virtualizer.getVirtualItems(),
    items.length,
  ]);

  return (
    <div
      ref={parentRef}
      className="w-full overflow-auto"
      style={{ height: containerHeight }}
    >
      <div
        style={{
          height: virtualizer.getTotalSize(),
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => {
          const item = items[virtualItem.index];
          const isLoaderRow = virtualItem.index > items.length - 1;

          return (
            <div
              key={virtualItem.index}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: virtualItem.size,
                transform: `translateY(${virtualItem.start}px)`,
              }}
            >
              {isLoaderRow ? (
                <div className="flex items-center justify-center h-full">
                  <LoadingSpinner size="sm" />
                  <span className="ml-2 text-gray-500">加载更多...</span>
                </div>
              ) : (
                <div className="px-4 py-2 h-full">
                  <ItemCard
                    item={item}
                    onLike={() => onItemAction?.(item, 'like')}
                    onSave={() => onItemAction?.(item, 'save')}
                    onShare={() => onItemAction?.(item, 'share')}
                    onSkip={() => onItemAction?.(item, 'skip')}
                    isLiked={false}
                    isSaved={false}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// 性能监控 Hook
export function useListPerformance() {
  const [metrics, setMetrics] = useState({
    renderTime: 0,
    scrollFPS: 0,
    memoryUsage: 0,
  });

  useEffect(() => {
    let frameCount = 0;
    let lastTime = performance.now();
    let animationId: number;

    const measureFPS = () => {
      frameCount++;
      const currentTime = performance.now();
      
      if (currentTime >= lastTime + 1000) {
        setMetrics(prev => ({
          ...prev,
          scrollFPS: Math.round((frameCount * 1000) / (currentTime - lastTime)),
        }));
        
        frameCount = 0;
        lastTime = currentTime;
      }
      
      animationId = requestAnimationFrame(measureFPS);
    };

    measureFPS();

    return () => {
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
    };
  }, []);

  // 内存使用监控
  useEffect(() => {
    const checkMemory = () => {
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        setMetrics(prev => ({
          ...prev,
          memoryUsage: Math.round(memory.usedJSHeapSize / 1024 / 1024), // MB
        }));
      }
    };

    checkMemory();
    const interval = setInterval(checkMemory, 5000); // 每5秒检查一次

    return () => clearInterval(interval);
  }, []);

  return metrics;
}

// 导出类型
export type { VirtualizedItemListProps };