import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import { Providers } from './providers';
// import { PerformanceMonitor } from '@/components/PerformanceMonitor';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'AgenticRAG - AI Workflow Platform',
  description: 'Visual AI Agent Builder for creating sophisticated AI workflows',
  keywords: ['AI', 'workflow', 'automation', 'agent', 'builder'],
  authors: [{ name: 'AgenticRAG Team' }],
  robots: 'index, follow',
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
    { media: '(prefers-color-scheme: dark)', color: '#000000' }
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/favicon.ico" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        <link rel="manifest" href="/manifest.json" />
      </head>
      <body className={inter.className} suppressHydrationWarning>
        <Providers>
          {children}
          {/* <PerformanceMonitor /> */}
        </Providers>
      </body>
    </html>
  );
}