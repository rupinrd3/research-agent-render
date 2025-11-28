/**
 * Root layout component for Next.js App Router.
 * Provides global styles, metadata, and layout structure.
 */

import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#4F46E5',
};

export const metadata: Metadata = {
  title: 'Agentic Research Lab | AI-Powered Research Assistant',
  description: 'An autonomous AI research assistant powered by ReAct architecture with real-time trace visualization',
  keywords: ['AI', 'Research', 'ReAct', 'LLM', 'Autonomous Agents'],
  authors: [{ name: 'Agentic Research Lab Team' }],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} antialiased`}>
        {children}
      </body>
    </html>
  );
}
