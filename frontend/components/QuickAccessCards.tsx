'use client';

import Link from 'next/link';

export function QuickAccessCards() {
  const cards = [
    {
      title: 'Dashboard',
      description: 'User dashboard and document management',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 16a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1H5a1 1 0 01-1-1v-3zM14 13a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1h-4a1 1 0 01-1-1v-7z" />
        </svg>
      ),
      href: '/dashboard',
      color: 'blue'
    },
    {
      title: 'System Metrics',
      description: 'Real-time system performance monitoring',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      href: '/monitoring',
      color: 'green'
    },
    {
      title: 'Statistics Dashboard',
      description: 'Detailed statistics and accuracy analysis',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      href: '/monitoring/stats',
      color: 'purple'
    }
  ];

  const colorClasses = {
    blue: {
      bg: 'bg-blue-50 dark:bg-blue-900/20',
      border: 'border-blue-200 dark:border-blue-800',
      icon: 'text-blue-600 dark:text-blue-400',
      hover: 'hover:border-blue-400 dark:hover:border-blue-600'
    },
    green: {
      bg: 'bg-green-50 dark:bg-green-900/20',
      border: 'border-green-200 dark:border-green-800',
      icon: 'text-green-600 dark:text-green-400',
      hover: 'hover:border-green-400 dark:hover:border-green-600'
    },
    purple: {
      bg: 'bg-purple-50 dark:bg-purple-900/20',
      border: 'border-purple-200 dark:border-purple-800',
      icon: 'text-purple-600 dark:text-purple-400',
      hover: 'hover:border-purple-400 dark:hover:border-purple-600'
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      {cards.map((card) => {
        const colors = colorClasses[card.color as keyof typeof colorClasses];
        return (
          <Link
            key={card.href}
            href={card.href}
            className={`
              ${colors.bg} ${colors.border} ${colors.hover}
              border-2 rounded-xl p-6 
              transition-all duration-200 
              hover:shadow-lg hover:scale-105
              group
            `}
          >
            <div className={`${colors.icon} mb-4 group-hover:scale-110 transition-transform`}>
              {card.icon}
            </div>
            <h3 className="text-lg font-bold mb-2 text-gray-900 dark:text-white">
              {card.title}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {card.description}
            </p>
            <div className="mt-4 flex items-center text-sm font-medium text-gray-700 dark:text-gray-300">
              Go to
              <svg className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </Link>
        );
      })}
    </div>
  );
}
