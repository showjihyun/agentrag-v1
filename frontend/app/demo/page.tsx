/**
 * Demo Page - Phase 2 & 3 Features
 * Demonstrates all new features: lazy loading, forms, animations, WebSocket, i18n
 */

'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Header } from '@/components/Header';
import { useTranslation } from '@/lib/hooks/useTranslation';
import { useLoginForm } from '@/lib/hooks/useForm';
import { useWebSocket, useRealtimeMessages } from '@/lib/hooks/useWebSocket';
import {
  pageVariants,
  fadeVariants,
  slideUpVariants,
  listContainerVariants,
  listItemVariants,
  buttonVariants,
} from '@/lib/animations/variants';

// Lazy loaded components
import dynamic from 'next/dynamic';

const LazyMonitoringDashboard = dynamic(
  () => import('@/components/monitoring/AdaptiveMonitoringDashboard'),
  {
    loading: () => <div className="animate-pulse bg-gray-200 h-64 rounded-lg" />,
    ssr: false,
  }
);

export default function DemoPage() {
  const { t, locale } = useTranslation();
  const { isConnected } = useWebSocket();
  const [showMonitoring, setShowMonitoring] = useState(false);
  const [activeTab, setActiveTab] = useState<'forms' | 'animations' | 'websocket' | 'i18n'>('forms');

  // Form demo
  const loginForm = useLoginForm();

  const onSubmit = (data: any) => {
    console.log('Form submitted:', data);
    alert(`${t('auth.loginSuccess')}! Email: ${data.email}`);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header />

      <motion.main
        variants={pageVariants}
        initial="initial"
        animate="animate"
        className="container mx-auto px-4 py-8"
      >
        {/* Hero Section */}
        <motion.div
          variants={fadeVariants}
          initial="hidden"
          animate="visible"
          className="text-center mb-12"
        >
          <h1 className="text-4xl font-bold mb-4">
            {t('common.loading') === 'Loading...' ? 'Phase 2 & 3 Features Demo' : '기능 데모'}
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-lg">
            Code Splitting • Forms • Animations • WebSocket • i18n
          </p>
        </motion.div>

        {/* Status Cards */}
        <motion.div
          variants={listContainerVariants}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8"
        >
          <motion.div variants={listItemVariants} className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Current Language</div>
            <div className="text-2xl font-bold">{locale.toUpperCase()}</div>
          </motion.div>

          <motion.div variants={listItemVariants} className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">WebSocket</div>
            <div className="text-2xl font-bold">
              {isConnected ? (
                <span className="text-green-600">Connected</span>
              ) : (
                <span className="text-red-600">Disconnected</span>
              )}
            </div>
          </motion.div>

          <motion.div variants={listItemVariants} className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Animations</div>
            <div className="text-2xl font-bold text-blue-600">60fps</div>
          </motion.div>

          <motion.div variants={listItemVariants} className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Bundle Size</div>
            <div className="text-2xl font-bold text-green-600">-30%</div>
          </motion.div>
        </motion.div>

        {/* Tabs */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow mb-8">
          <div className="border-b border-gray-200 dark:border-gray-700">
            <div className="flex">
              {(['forms', 'animations', 'websocket', 'i18n'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-6 py-3 font-medium transition-colors ${
                    activeTab === tab
                      ? 'border-b-2 border-blue-600 text-blue-600'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                  }`}
                >
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div className="p-6">
            {/* Forms Tab */}
            {activeTab === 'forms' && (
              <motion.div
                variants={slideUpVariants}
                initial="hidden"
                animate="visible"
              >
                <h2 className="text-2xl font-bold mb-4">React Hook Form with Zod Validation</h2>
                <form onSubmit={loginForm.handleSubmit(onSubmit)} className="max-w-md space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      {t('auth.email')}
                    </label>
                    <input
                      {...loginForm.register('email')}
                      type="email"
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-600 dark:bg-gray-700 dark:border-gray-600"
                      placeholder="user@example.com"
                    />
                    {loginForm.formState.errors.email && (
                      <p className="text-red-600 text-sm mt-1">
                        {loginForm.formState.errors.email.message}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      {t('auth.password')}
                    </label>
                    <input
                      {...loginForm.register('password')}
                      type="password"
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-600 dark:bg-gray-700 dark:border-gray-600"
                      placeholder="••••••••"
                    />
                    {loginForm.formState.errors.password && (
                      <p className="text-red-600 text-sm mt-1">
                        {loginForm.formState.errors.password.message}
                      </p>
                    )}
                  </div>

                  <motion.button
                    variants={buttonVariants}
                    whileHover="hover"
                    whileTap="tap"
                    type="submit"
                    className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium"
                  >
                    {t('auth.login')}
                  </motion.button>
                </form>
              </motion.div>
            )}

            {/* Animations Tab */}
            {activeTab === 'animations' && (
              <motion.div
                variants={slideUpVariants}
                initial="hidden"
                animate="visible"
              >
                <h2 className="text-2xl font-bold mb-4">Framer Motion Animations</h2>
                <div className="space-y-4">
                  <motion.div
                    variants={listContainerVariants}
                    initial="hidden"
                    animate="visible"
                    className="space-y-2"
                  >
                    {[1, 2, 3, 4, 5].map((i) => (
                      <motion.div
                        key={i}
                        variants={listItemVariants}
                        className="bg-blue-100 dark:bg-blue-900 p-4 rounded-lg"
                      >
                        Stagger Animation Item {i}
                      </motion.div>
                    ))}
                  </motion.div>

                  <motion.button
                    variants={buttonVariants}
                    whileHover="hover"
                    whileTap="tap"
                    className="bg-green-600 text-white px-6 py-2 rounded-lg"
                  >
                    Hover & Tap Me!
                  </motion.button>
                </div>
              </motion.div>
            )}

            {/* WebSocket Tab */}
            {activeTab === 'websocket' && (
              <motion.div
                variants={slideUpVariants}
                initial="hidden"
                animate="visible"
              >
                <h2 className="text-2xl font-bold mb-4">WebSocket Real-time Updates</h2>
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                    <span className="font-medium">
                      Status: {isConnected ? 'Connected' : 'Disconnected'}
                    </span>
                  </div>

                  <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      WebSocket connection enables real-time features like:
                    </p>
                    <ul className="mt-2 space-y-1 text-sm">
                      <li>• Real-time message updates</li>
                      <li>• Typing indicators</li>
                      <li>• Online presence</li>
                      <li>• Live notifications</li>
                    </ul>
                  </div>
                </div>
              </motion.div>
            )}

            {/* i18n Tab */}
            {activeTab === 'i18n' && (
              <motion.div
                variants={slideUpVariants}
                initial="hidden"
                animate="visible"
              >
                <h2 className="text-2xl font-bold mb-4">Internationalization (i18n)</h2>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded-lg">
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">Common</div>
                      <div className="space-y-1 text-sm">
                        <div>Loading: {t('common.loading')}</div>
                        <div>Error: {t('common.error')}</div>
                        <div>Success: {t('common.success')}</div>
                      </div>
                    </div>

                    <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded-lg">
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">Auth</div>
                      <div className="space-y-1 text-sm">
                        <div>Login: {t('auth.login')}</div>
                        <div>Register: {t('auth.register')}</div>
                        <div>Logout: {t('auth.logout')}</div>
                      </div>
                    </div>

                    <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded-lg">
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">Chat</div>
                      <div className="space-y-1 text-sm">
                        <div>Send: {t('chat.send')}</div>
                        <div>New Chat: {t('chat.newChat')}</div>
                        <div>History: {t('chat.history')}</div>
                      </div>
                    </div>

                    <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded-lg">
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">Dashboard</div>
                      <div className="space-y-1 text-sm">
                        <div>Title: {t('dashboard.title')}</div>
                        <div>Overview: {t('dashboard.overview')}</div>
                        <div>Usage: {t('dashboard.usage')}</div>
                      </div>
                    </div>
                  </div>

                  <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                    <p className="text-sm">
                      💡 Use the language switcher in the header to see translations in action!
                    </p>
                  </div>
                </div>
              </motion.div>
            )}
          </div>
        </div>

        {/* Lazy Loading Demo */}
        <motion.div
          variants={fadeVariants}
          initial="hidden"
          animate="visible"
          className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
        >
          <h2 className="text-2xl font-bold mb-4">Code Splitting & Lazy Loading</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Click the button below to lazy load the Monitoring Dashboard component.
            Check the Network tab to see the chunk being loaded on demand.
          </p>

          <motion.button
            variants={buttonVariants}
            whileHover="hover"
            whileTap="tap"
            onClick={() => setShowMonitoring(!showMonitoring)}
            className="bg-purple-600 text-white px-6 py-2 rounded-lg font-medium"
          >
            {showMonitoring ? 'Hide' : 'Load'} Monitoring Dashboard
          </motion.button>

          {showMonitoring && (
            <motion.div
              variants={slideUpVariants}
              initial="hidden"
              animate="visible"
              className="mt-6"
            >
              <LazyMonitoringDashboard isAdmin={false} />
            </motion.div>
          )}
        </motion.div>
      </motion.main>
    </div>
  );
}
