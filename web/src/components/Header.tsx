'use client';

import { useState } from 'react';
import { MagnifyingGlassIcon, Cog6ToothIcon, UserCircleIcon } from '@heroicons/react/24/outline';
import { getStoredUser, isAuthenticated } from '@/lib/api';

export function Header() {
  const [user] = useState(getStoredUser());
  const [isLoggedIn] = useState(isAuthenticated());

  return (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between max-w-4xl">
        {/* Logo */}
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">AS</span>
          </div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
            AttentionSync
          </h1>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-3">
          {isLoggedIn ? (
            <>
              {/* Search button */}
              <button className="btn-ghost p-2">
                <MagnifyingGlassIcon className="w-5 h-5" />
              </button>
              
              {/* Settings button */}
              <button className="btn-ghost p-2">
                <Cog6ToothIcon className="w-5 h-5" />
              </button>
              
              {/* User menu */}
              <div className="flex items-center space-x-2">
                {user?.avatar_url ? (
                  <img
                    src={user.avatar_url}
                    alt={user.display_name}
                    className="w-8 h-8 rounded-full"
                  />
                ) : (
                  <UserCircleIcon className="w-8 h-8 text-gray-400" />
                )}
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300 hidden sm:block">
                  {user?.full_name || user?.username || user?.email?.split('@')[0]}
                </span>
              </div>
            </>
          ) : (
            <div className="flex items-center space-x-2">
              <a href="/login" className="btn-ghost">
                登录
              </a>
              <a href="/register" className="btn-primary">
                注册
              </a>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}