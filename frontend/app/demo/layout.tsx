/**
 * Demo Pages Layout
 * Provides navigation between all demo pages
 */

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const demoPages = [
  { href: '/demo', label: 'Overview', description: 'Phase 2 & 3 Features' },
  { href: '/demo/ai-agent', label: 'AI Agent', description: 'AI Agent Demo' },
  { href: '/demo/tool-config', label: 'Tool Config', description: 'Tool Configuration' },
  { href: '/demo/tool-editor', label: 'Tool Editor', description: 'Tool Editor Demo' },
  { href: '/demo/unified-panel', label: 'Unified Panel', description: 'Unified Panel Demo' },
  { href: '/demo/workflow-phase2', label: 'Workflow Phase 2', description: 'Workflow Features' },
  { href: '/demo/workflow-phase3', label: 'Workflow Phase 3', description: 'Advanced Workflow' },
  { href: '/demo/workflow-phase5', label: 'Workflow Phase 5', description: 'Latest Workflow' },
];

export default function DemoLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Demo Navigation */}
      <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="container mx-auto px-4">
          <div className="flex items-center gap-1 py-2 overflow-x-auto">
            <span className="text-sm font-medium text-gray-500 dark:text-gray-400 mr-2">
              Demos:
            </span>
            {demoPages.map((page) => (
              <Link
                key={page.href}
                href={page.href}
                className={`px-3 py-1.5 text-sm rounded-md whitespace-nowrap transition-colors ${
                  pathname === page.href
                    ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                {page.label}
              </Link>
            ))}
          </div>
        </div>
      </nav>

      {/* Page Content */}
      {children}
    </div>
  );
}
