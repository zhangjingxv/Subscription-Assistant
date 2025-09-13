// Axios module augmentation for custom request metadata and retry flags
import 'axios';

declare module 'axios' {
  interface InternalAxiosRequestConfig<D = any> {
    metadata?: { requestId: string; startTime: number };
    _retry?: boolean;
    _retryCount?: number;
  }

  interface AxiosRequestConfig<D = any> {
    metadata?: { requestId: string; startTime: number };
    _retry?: boolean;
    _retryCount?: number;
  }
}

