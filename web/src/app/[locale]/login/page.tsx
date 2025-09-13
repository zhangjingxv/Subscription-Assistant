'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';
import type { LoginCredentials } from '@/types';

export default function LoginPage({ params }: { params: { locale: string } }) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState<LoginCredentials>({
    email: '',
    password: ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await apiClient.login(formData);
      toast.success('登录成功！');
      router.push(`/${params.locale}`);
    } catch (error) {
      console.error('Login failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md w-full space-y-8"
      >
        <div className="text-center">
          <div className="w-16 h-16 bg-primary-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="text-white font-bold text-xl">AS</span>
          </div>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            欢迎回来
          </h2>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            登录您的AttentionSync账户
          </p>
        </div>

        <form className="space-y-6" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              邮箱地址
            </label>
            <input
              id="email"
              name="email"
              type="email"
              required
              className="input"
              placeholder="your@email.com"
              value={formData.email}
              onChange={handleChange}
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              密码
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              className="input"
              placeholder="请输入密码"
              value={formData.password}
              onChange={handleChange}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full btn-primary flex items-center justify-center"
          >
            {isLoading ? (
              <>
                <div className="spinner mr-2" />
                登录中...
              </>
            ) : (
              '登录'
            )}
          </button>
        </form>

        <div className="text-center">
          <p className="text-gray-600 dark:text-gray-400">
            还没有账户？{' '}
            <a href={`/${params.locale}/register`} className="text-primary-600 dark:text-primary-400 hover:underline">
              立即注册
            </a>
          </p>
        </div>

        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
          <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-2">
            💡 演示账号
          </h4>
          <p className="text-xs text-blue-600 dark:text-blue-300">
            邮箱: admin@attentionsync.io<br />
            密码: admin123
          </p>
        </div>
      </motion.div>
    </div>
  );
}

