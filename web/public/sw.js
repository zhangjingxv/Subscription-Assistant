/**
 * AttentionSync Service Worker
 * 提供离线支持和缓存管理
 */

const CACHE_NAME = 'attentionsync-v1.0.0';
const API_CACHE_NAME = 'attentionsync-api-v1.0.0';
const STATIC_CACHE_NAME = 'attentionsync-static-v1.0.0';

// 需要缓存的静态资源
const STATIC_ASSETS = [
  '/',
  '/login',
  '/manifest.json',
  '/favicon.ico',
  // 添加其他静态资源
];

// 需要缓存的 API 端点
const CACHEABLE_APIS = [
  '/api/v1/daily/digest',
  '/api/v1/sources',
  '/api/v1/items',
  '/api/v1/auth/me',
];

// 离线时的后备页面
const OFFLINE_PAGE = '/offline.html';

// 安装事件
self.addEventListener('install', (event) => {
  console.log('Service Worker installing...');
  
  event.waitUntil(
    Promise.all([
      // 缓存静态资源
      caches.open(STATIC_CACHE_NAME).then((cache) => {
        return cache.addAll(STATIC_ASSETS);
      }),
      // 预缓存离线页面
      caches.open(CACHE_NAME).then((cache) => {
        return cache.add(OFFLINE_PAGE);
      }),
    ]).then(() => {
      console.log('Service Worker installed successfully');
      // 立即激活新的 Service Worker
      return self.skipWaiting();
    })
  );
});

// 激活事件
self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...');
  
  event.waitUntil(
    Promise.all([
      // 清理旧缓存
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (
              cacheName !== CACHE_NAME &&
              cacheName !== API_CACHE_NAME &&
              cacheName !== STATIC_CACHE_NAME
            ) {
              console.log('Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      }),
      // 声明控制所有客户端
      self.clients.claim(),
    ]).then(() => {
      console.log('Service Worker activated successfully');
    })
  );
});

// 获取请求
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // 只处理同源请求
  if (url.origin !== location.origin) {
    return;
  }

  // 根据请求类型使用不同的缓存策略
  if (request.method === 'GET') {
    if (url.pathname.startsWith('/api/')) {
      // API 请求：网络优先，缓存后备
      event.respondWith(handleApiRequest(request));
    } else if (isStaticAsset(url.pathname)) {
      // 静态资源：缓存优先
      event.respondWith(handleStaticRequest(request));
    } else {
      // 页面请求：网络优先，离线后备
      event.respondWith(handlePageRequest(request));
    }
  }
});

// 处理 API 请求
async function handleApiRequest(request) {
  const url = new URL(request.url);
  const isCacheable = CACHEABLE_APIS.some(api => url.pathname.startsWith(api));

  if (!isCacheable) {
    // 不可缓存的 API 请求，直接发送网络请求
    return fetch(request);
  }

  try {
    // 尝试网络请求
    const response = await fetch(request);
    
    if (response.ok) {
      // 成功响应，更新缓存
      const cache = await caches.open(API_CACHE_NAME);
      cache.put(request, response.clone());
      return response;
    }
    
    throw new Error('Network response was not ok');
  } catch (error) {
    console.log('Network request failed, trying cache...', error);
    
    // 网络请求失败，尝试从缓存获取
    const cache = await caches.open(API_CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      console.log('Serving from cache:', request.url);
      return cachedResponse;
    }
    
    // 缓存中也没有，返回离线响应
    return new Response(
      JSON.stringify({
        error: {
          code: 'OFFLINE_ERROR',
          message: '网络不可用，请检查网络连接',
        },
      }),
      {
        status: 503,
        statusText: 'Service Unavailable',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
  }
}

// 处理静态资源请求
async function handleStaticRequest(request) {
  // 缓存优先策略
  const cache = await caches.open(STATIC_CACHE_NAME);
  const cachedResponse = await cache.match(request);

  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    console.log('Failed to fetch static asset:', request.url);
    return new Response('', { status: 404 });
  }
}

// 处理页面请求
async function handlePageRequest(request) {
  try {
    // 尝试网络请求
    const response = await fetch(request);
    
    if (response.ok) {
      // 缓存页面响应
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
      return response;
    }
    
    throw new Error('Network response was not ok');
  } catch (error) {
    console.log('Page request failed, trying cache...', error);
    
    // 尝试从缓存获取
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // 返回离线页面
    return caches.match(OFFLINE_PAGE);
  }
}

// 判断是否为静态资源
function isStaticAsset(pathname) {
  return /\.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$/.test(pathname);
}

// 消息处理
self.addEventListener('message', (event) => {
  const { type, payload } = event.data;

  switch (type) {
    case 'SKIP_WAITING':
      self.skipWaiting();
      break;
    
    case 'CACHE_INVALIDATE':
      // 清除指定缓存
      if (payload.url) {
        invalidateCache(payload.url);
      }
      break;
    
    case 'CACHE_CLEAR':
      // 清除所有缓存
      clearAllCaches();
      break;
    
    case 'GET_CACHE_STATS':
      // 获取缓存统计
      getCacheStats().then(stats => {
        event.ports[0].postMessage(stats);
      });
      break;
  }
});

// 缓存管理函数
async function invalidateCache(url) {
  const cacheNames = await caches.keys();
  
  for (const cacheName of cacheNames) {
    const cache = await caches.open(cacheName);
    await cache.delete(url);
  }
  
  console.log('Cache invalidated for:', url);
}

async function clearAllCaches() {
  const cacheNames = await caches.keys();
  
  for (const cacheName of cacheNames) {
    await caches.delete(cacheName);
  }
  
  console.log('All caches cleared');
}

async function getCacheStats() {
  const cacheNames = await caches.keys();
  const stats = {};

  for (const cacheName of cacheNames) {
    const cache = await caches.open(cacheName);
    const keys = await cache.keys();
    stats[cacheName] = keys.length;
  }

  return {
    caches: stats,
    totalCaches: cacheNames.length,
    timestamp: new Date().toISOString(),
  };
}

// 后台同步
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

async function doBackgroundSync() {
  // 执行后台同步任务
  // 例如：同步离线时的用户操作
  console.log('Background sync triggered');
  
  try {
    // 获取离线时的操作队列
    const cache = await caches.open('offline-actions');
    const requests = await cache.keys();
    
    for (const request of requests) {
      try {
        await fetch(request);
        await cache.delete(request);
      } catch (error) {
        console.log('Failed to sync request:', request.url);
      }
    }
  } catch (error) {
    console.log('Background sync failed:', error);
  }
}

// 推送通知
self.addEventListener('push', (event) => {
  if (!event.data) return;

  const data = event.data.json();
  const { title, body, icon, badge, tag, url } = data;

  const options = {
    body,
    icon: icon || '/icon-192x192.png',
    badge: badge || '/badge-72x72.png',
    tag: tag || 'attentionsync-notification',
    data: { url },
    actions: [
      {
        action: 'open',
        title: '查看',
        icon: '/icon-open.png',
      },
      {
        action: 'dismiss',
        title: '关闭',
        icon: '/icon-close.png',
      },
    ],
    requireInteraction: true,
    vibrate: [200, 100, 200],
  };

  event.waitUntil(
    self.registration.showNotification(title || 'AttentionSync', options)
  );
});

// 通知点击处理
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const { action, data } = event;
  const url = data?.url || '/';

  if (action === 'open' || !action) {
    event.waitUntil(
      clients.matchAll({ type: 'window' }).then((clientList) => {
        // 查找已打开的窗口
        for (const client of clientList) {
          if (client.url.includes(url) && 'focus' in client) {
            return client.focus();
          }
        }
        
        // 打开新窗口
        if (clients.openWindow) {
          return clients.openWindow(url);
        }
      })
    );
  }
  // 'dismiss' 操作不需要额外处理
});

console.log('AttentionSync Service Worker loaded');