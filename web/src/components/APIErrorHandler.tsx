'use client';

import { useState, useEffect, ReactNode } from 'react';
import { toast } from 'react-hot-toast';

interface APIError {
  message: string;
  status?: number;
  code?: string;
  details?: any;
}

interface APIErrorHandlerProps {
  children: ReactNode;
  onError?: (error: APIError) => void;
  showToast?: boolean;
}

export function APIErrorHandler({ 
  children, 
  onError, 
  showToast = true 
}: APIErrorHandlerProps) {
  const [errors, setErrors] = useState<APIError[]>([]);

  useEffect(() => {
    // 监听全局错误
    const handleError = (event: ErrorEvent) => {
      const error: APIError = {
        message: event.message,
        code: event.error?.name || 'UnknownError',
        details: {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
        }
      };
      
      handleAPIError(error);
    };

    // 监听未处理的 Promise 拒绝
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      const error: APIError = {
        message: event.reason?.message || 'Unhandled Promise Rejection',
        code: 'UnhandledRejection',
        details: event.reason
      };
      
      handleAPIError(error);
    };

    window.addEventListener('error', handleError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);

    return () => {
      window.removeEventListener('error', handleError);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, []);

  const handleAPIError = (error: APIError) => {
    console.error('API Error caught:', error);
    
    // 添加到错误列表
    setErrors(prev => [...prev, error]);
    
    // 显示 toast 通知
    if (showToast) {
      const errorMessage = getErrorMessage(error);
      toast.error(errorMessage);
    }
    
    // 调用自定义错误处理函数
    if (onError) {
      onError(error);
    }
  };

  const getErrorMessage = (error: APIError): string => {
    // 根据错误类型返回用户友好的错误信息
    if (error.status) {
      switch (error.status) {
        case 400:
          return '请求参数错误，请检查输入';
        case 401:
          return '认证失败，请重新登录';
        case 403:
          return '权限不足，无法访问此资源';
        case 404:
          return '请求的资源不存在';
        case 429:
          return '请求过于频繁，请稍后再试';
        case 500:
          return '服务器内部错误，请稍后重试';
        case 502:
          return '网关错误，服务暂时不可用';
        case 503:
          return '服务暂时不可用，请稍后重试';
        default:
          return `请求失败 (${error.status})`;
      }
    }

    // 网络错误
    if (error.code === 'NetworkError' || error.message.includes('fetch')) {
      return '网络连接失败，请检查网络设置';
    }

    // 超时错误
    if (error.code === 'TimeoutError' || error.message.includes('timeout')) {
      return '请求超时，请稍后重试';
    }

    // 默认错误信息
    return error.message || '发生未知错误';
  };

  const clearErrors = () => {
    setErrors([]);
  };

  const retryLastError = () => {
    if (errors.length > 0) {
      const lastError = errors[errors.length - 1];
      // 这里可以实现重试逻辑
      console.log('Retrying error:', lastError);
      setErrors(prev => prev.slice(0, -1));
    }
  };

  return (
    <div className="api-error-handler">
      {children}
      
      {/* 错误显示区域 */}
      {errors.length > 0 && (
        <div className="fixed bottom-4 right-4 max-w-sm">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 shadow-lg">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h4 className="text-sm font-medium text-red-800">
                  发生错误 ({errors.length})
                </h4>
                <p className="text-sm text-red-600 mt-1">
                  {getErrorMessage(errors[errors.length - 1])}
                </p>
              </div>
              <div className="flex space-x-2 ml-4">
                {errors.length > 1 && (
                  <button
                    onClick={retryLastError}
                    className="text-xs text-red-600 hover:text-red-800 underline"
                  >
                    重试
                  </button>
                )}
                <button
                  onClick={clearErrors}
                  className="text-xs text-red-600 hover:text-red-800 underline"
                >
                  清除
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Hook 用于在组件中处理 API 错误
export function useAPIError() {
  const [error, setError] = useState<APIError | null>(null);

  const handleError = (err: any) => {
    const apiError: APIError = {
      message: err.message || 'Unknown error',
      status: err.status || err.response?.status,
      code: err.code || err.name,
      details: err.response?.data || err.details
    };
    
    setError(apiError);
    console.error('API Error:', apiError);
  };

  const clearError = () => {
    setError(null);
  };

  return {
    error,
    handleError,
    clearError,
    hasError: !!error
  };
}

// 高阶组件用于包装需要错误处理的组件
export function withAPIErrorHandler<P extends object>(
  Component: React.ComponentType<P>,
  errorHandlerProps?: Omit<APIErrorHandlerProps, 'children'>
) {
  const WrappedComponent = (props: P) => (
    <APIErrorHandler {...errorHandlerProps}>
      <Component {...props} />
    </APIErrorHandler>
  );

  WrappedComponent.displayName = `withAPIErrorHandler(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
}

export default APIErrorHandler;