/**
 * 滑动手势 Hook
 * 支持移动端触摸手势和桌面端鼠标手势
 */

import { useCallback, useRef, useState, useEffect } from 'react';

interface SwipeGestureConfig {
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
  onSwipeDown?: () => void;
  threshold?: number;
  preventDefaultTouchmove?: boolean;
  trackMouse?: boolean;
  delta?: number;
}

interface TouchPoint {
  x: number;
  y: number;
  time: number;
}

export function useSwipeGesture({
  onSwipeLeft,
  onSwipeRight,
  onSwipeUp,
  onSwipeDown,
  threshold = 50,
  preventDefaultTouchmove = true,
  trackMouse = true,
  delta = 10,
}: SwipeGestureConfig) {
  const [isSwiping, setIsSwiping] = useState(false);
  const [startPoint, setStartPoint] = useState<TouchPoint | null>(null);
  const [currentPoint, setCurrentPoint] = useState<TouchPoint | null>(null);
  const elementRef = useRef<HTMLElement>(null);

  const getEventPoint = useCallback((event: TouchEvent | MouseEvent): TouchPoint => {
    const point = 'touches' in event ? event.touches[0] : event;
    return {
      x: point.clientX,
      y: point.clientY,
      time: Date.now(),
    };
  }, []);

  const calculateDistance = useCallback((point1: TouchPoint, point2: TouchPoint) => {
    const deltaX = point2.x - point1.x;
    const deltaY = point2.y - point1.y;
    return {
      deltaX,
      deltaY,
      distance: Math.sqrt(deltaX * deltaX + deltaY * deltaY),
    };
  }, []);

  const calculateVelocity = useCallback((point1: TouchPoint, point2: TouchPoint) => {
    const timeDelta = point2.time - point1.time;
    const { distance } = calculateDistance(point1, point2);
    return timeDelta > 0 ? distance / timeDelta : 0;
  }, [calculateDistance]);

  const handleStart = useCallback((event: TouchEvent | MouseEvent) => {
    const point = getEventPoint(event);
    setStartPoint(point);
    setCurrentPoint(point);
    setIsSwiping(true);

    // 阻止默认行为（如页面滚动）
    if (preventDefaultTouchmove && 'touches' in event) {
      event.preventDefault();
    }
  }, [getEventPoint, preventDefaultTouchmove]);

  const handleMove = useCallback((event: TouchEvent | MouseEvent) => {
    if (!startPoint || !isSwiping) return;

    const point = getEventPoint(event);
    setCurrentPoint(point);

    // 阻止默认的触摸移动行为
    if (preventDefaultTouchmove && 'touches' in event) {
      event.preventDefault();
    }
  }, [startPoint, isSwiping, getEventPoint, preventDefaultTouchmove]);

  const handleEnd = useCallback((event: TouchEvent | MouseEvent) => {
    if (!startPoint || !currentPoint || !isSwiping) {
      setIsSwiping(false);
      return;
    }

    const { deltaX, deltaY, distance } = calculateDistance(startPoint, currentPoint);
    const velocity = calculateVelocity(startPoint, currentPoint);

    // 检查是否满足滑动条件
    const isValidSwipe = distance > threshold && velocity > 0.1;

    if (isValidSwipe) {
      // 确定滑动方向
      const absDeltaX = Math.abs(deltaX);
      const absDeltaY = Math.abs(deltaY);

      if (absDeltaX > absDeltaY) {
        // 水平滑动
        if (deltaX > delta) {
          onSwipeRight?.();
        } else if (deltaX < -delta) {
          onSwipeLeft?.();
        }
      } else {
        // 垂直滑动
        if (deltaY > delta) {
          onSwipeDown?.();
        } else if (deltaY < -delta) {
          onSwipeUp?.();
        }
      }
    }

    // 重置状态
    setIsSwiping(false);
    setStartPoint(null);
    setCurrentPoint(null);
  }, [
    startPoint,
    currentPoint,
    isSwiping,
    calculateDistance,
    calculateVelocity,
    threshold,
    delta,
    onSwipeLeft,
    onSwipeRight,
    onSwipeUp,
    onSwipeDown,
  ]);

  // 绑定事件监听器
  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    // 触摸事件
    element.addEventListener('touchstart', handleStart, { passive: false });
    element.addEventListener('touchmove', handleMove, { passive: false });
    element.addEventListener('touchend', handleEnd, { passive: false });

    // 鼠标事件（如果启用）
    if (trackMouse) {
      element.addEventListener('mousedown', handleStart);
      element.addEventListener('mousemove', handleMove);
      element.addEventListener('mouseup', handleEnd);
      element.addEventListener('mouseleave', handleEnd);
    }

    return () => {
      element.removeEventListener('touchstart', handleStart);
      element.removeEventListener('touchmove', handleMove);
      element.removeEventListener('touchend', handleEnd);

      if (trackMouse) {
        element.removeEventListener('mousedown', handleStart);
        element.removeEventListener('mousemove', handleMove);
        element.removeEventListener('mouseup', handleEnd);
        element.removeEventListener('mouseleave', handleEnd);
      }
    };
  }, [handleStart, handleMove, handleEnd, trackMouse]);

  // 计算滑动进度（用于视觉反馈）
  const swipeProgress = useMemo(() => {
    if (!startPoint || !currentPoint || !isSwiping) {
      return { x: 0, y: 0, direction: null };
    }

    const { deltaX, deltaY } = calculateDistance(startPoint, currentPoint);
    const absDeltaX = Math.abs(deltaX);
    const absDeltaY = Math.abs(deltaY);

    let direction = null;
    if (absDeltaX > absDeltaY && absDeltaX > delta) {
      direction = deltaX > 0 ? 'right' : 'left';
    } else if (absDeltaY > absDeltaX && absDeltaY > delta) {
      direction = deltaY > 0 ? 'down' : 'up';
    }

    return {
      x: deltaX,
      y: deltaY,
      direction,
      progress: Math.min(Math.max(absDeltaX, absDeltaY) / threshold, 1),
    };
  }, [startPoint, currentPoint, isSwiping, calculateDistance, delta, threshold]);

  return {
    elementRef,
    isSwiping,
    swipeProgress,
  };
}

// 滑动手势增强的卡片组件
export function SwipeableCard({
  children,
  onSwipeLeft,
  onSwipeRight,
  className = '',
  threshold = 80,
}: {
  children: React.ReactNode;
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  className?: string;
  threshold?: number;
}) {
  const { elementRef, isSwiping, swipeProgress } = useSwipeGesture({
    onSwipeLeft,
    onSwipeRight,
    threshold,
    preventDefaultTouchmove: true,
    trackMouse: true,
  });

  // 计算变换样式
  const transformStyle = useMemo(() => {
    if (!isSwiping || !swipeProgress.direction) {
      return {};
    }

    const translateX = Math.max(-100, Math.min(100, swipeProgress.x * 0.5));
    const opacity = Math.max(0.7, 1 - Math.abs(swipeProgress.progress) * 0.3);

    return {
      transform: `translateX(${translateX}px)`,
      opacity,
      transition: isSwiping ? 'none' : 'transform 0.3s ease, opacity 0.3s ease',
    };
  }, [isSwiping, swipeProgress]);

  // 滑动提示样式
  const hintStyle = useMemo(() => {
    if (!isSwiping || !swipeProgress.direction) {
      return { opacity: 0 };
    }

    const isLeft = swipeProgress.direction === 'left';
    const isRight = swipeProgress.direction === 'right';

    if (!isLeft && !isRight) {
      return { opacity: 0 };
    }

    return {
      opacity: swipeProgress.progress * 0.8,
      backgroundColor: isLeft ? '#ef4444' : '#10b981', // 红色（删除）或绿色（保存）
    };
  }, [isSwiping, swipeProgress]);

  return (
    <div className={`relative ${className}`}>
      {/* 滑动提示背景 */}
      <div
        className="absolute inset-0 rounded-lg flex items-center justify-center text-white font-medium"
        style={hintStyle}
      >
        {swipeProgress.direction === 'left' && '跳过'}
        {swipeProgress.direction === 'right' && '保存'}
      </div>

      {/* 主要内容 */}
      <div
        ref={elementRef}
        style={transformStyle}
        className="relative z-10 bg-white dark:bg-gray-800 rounded-lg"
      >
        {children}
      </div>
    </div>
  );
}

// 手势识别增强
export function useAdvancedGestures() {
  const [gestureState, setGestureState] = useState({
    isDoubleTap: false,
    isLongPress: false,
    isPinch: false,
  });

  const doubleTapTimeout = useRef<NodeJS.Timeout>();
  const longPressTimeout = useRef<NodeJS.Timeout>();
  const lastTapTime = useRef(0);

  const handleDoubleTap = useCallback((callback?: () => void) => {
    return (event: React.TouchEvent | React.MouseEvent) => {
      const now = Date.now();
      const timeDiff = now - lastTapTime.current;

      if (timeDiff < 300) {
        // 双击检测
        setGestureState(prev => ({ ...prev, isDoubleTap: true }));
        callback?.();
        
        if (doubleTapTimeout.current) {
          clearTimeout(doubleTapTimeout.current);
        }
      } else {
        // 单击
        doubleTapTimeout.current = setTimeout(() => {
          setGestureState(prev => ({ ...prev, isDoubleTap: false }));
        }, 300);
      }

      lastTapTime.current = now;
    };
  }, []);

  const handleLongPress = useCallback((callback?: () => void, duration = 500) => {
    return {
      onTouchStart: () => {
        longPressTimeout.current = setTimeout(() => {
          setGestureState(prev => ({ ...prev, isLongPress: true }));
          callback?.();
        }, duration);
      },
      onTouchEnd: () => {
        if (longPressTimeout.current) {
          clearTimeout(longPressTimeout.current);
        }
        setGestureState(prev => ({ ...prev, isLongPress: false }));
      },
      onTouchMove: () => {
        if (longPressTimeout.current) {
          clearTimeout(longPressTimeout.current);
        }
      },
    };
  }, []);

  return {
    gestureState,
    handleDoubleTap,
    handleLongPress,
  };
}