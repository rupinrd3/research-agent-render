/**
 * Header component with navigation, settings, and history access.
 * Features glassmorphism design with gradient branding.
 */

'use client';

import React from 'react';
import { Microscope, Settings, History, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface HeaderProps {
  onSettingsClick?: () => void;
  onHistoryClick?: () => void;
  className?: string;
}

/**
 * Application header with branding and navigation controls.
 *
 * Features:
 * - Glassmorphism effect for modern aesthetics
 * - Gradient brand identity
 * - Settings and history navigation
 * - User profile placeholder
 *
 * @example
 * ```tsx
 * <Header
 *   onSettingsClick={() => setShowSettings(true)}
 *   onHistoryClick={() => router.push('/history')}
 * />
 * ```
 */
export function Header({ onSettingsClick, onHistoryClick, className }: HeaderProps) {
  return (
    <header
      className={cn(
        'fixed top-0 w-full z-50 bg-slate-950/80 backdrop-blur border-b border-slate-800/60 shadow-lg',
        className
      )}
    >
      <div className="container mx-auto px-6 py-4 flex items-center justify-between">
        {/* Brand Logo and Title */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg">
            <Microscope className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-xl font-bold gradient-text">
            Agentic Research Lab
          </h1>
        </div>

        {/* Navigation Controls */}
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={onSettingsClick}
            className="hover:bg-slate-800"
            aria-label="Settings"
          >
            <Settings className="w-5 h-5" />
          </Button>

          <Button
            variant="ghost"
            size="icon"
            onClick={onHistoryClick}
            className="hover:bg-slate-800"
            aria-label="History"
          >
            <History className="w-5 h-5" />
          </Button>

          <Button
            variant="ghost"
            size="icon"
            onClick={onSettingsClick}
            className="rounded-full w-10 h-10 bg-gradient-to-br from-slate-700 to-slate-800 hover:from-slate-600 hover:to-slate-900 border border-slate-600/30"
            aria-label="Open settings"
          >
            <User className="w-5 h-5 text-slate-100" />
          </Button>
        </div>
      </div>
    </header>
  );
}
