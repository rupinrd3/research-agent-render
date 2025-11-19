/**
 * Score Bar Component
 *
 * Animated progress bar for displaying 0-1 evaluation scores.
 */

'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface ScoreBarProps {
  label: string;
  score: number; // 0-1
}

export function ScoreBar({ label, score }: ScoreBarProps) {
  const percentage = score * 100;

  // Color based on score
  const getColor = () => {
    if (score >= 0.8) return 'bg-green-500';
    if (score >= 0.6) return 'bg-blue-400';
    if (score >= 0.4) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="text-slate-400">{label}</span>
        <span className="font-mono font-semibold text-slate-200">
          {score.toFixed(2)}
        </span>
      </div>
      <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={cn(
            'h-full rounded-full transition-all duration-700 ease-out',
            getColor()
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
