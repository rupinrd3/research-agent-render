/**
 * Metric Card Component
 *
 * Modern glass-morphism card for displaying individual metrics.
 */

'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  icon?: React.ReactNode;
  subtitle?: string;
  className?: string;
}

export function MetricCard({
  label,
  value,
  unit,
  icon,
  subtitle,
  className,
}: MetricCardProps) {
  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-lg bg-gradient-to-br from-slate-800/40 to-slate-900/60',
        'border border-slate-700/30 p-4 backdrop-blur-sm',
        'hover:border-indigo-500/50 transition-all duration-300 group',
        className
      )}
    >
      {/* Background glow effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

      <div className="relative z-10">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            {icon && <div className="text-indigo-400">{icon}</div>}
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wide">
              {label}
            </span>
          </div>
        </div>

        {/* Value */}
        <div className="flex items-baseline gap-2 mb-1">
          <span className="text-3xl font-bold text-slate-100 font-mono">
            {value}
          </span>
          {unit && (
            <span className="text-sm text-slate-500 font-medium">{unit}</span>
          )}
        </div>

        {/* Subtitle */}
        {subtitle && (
          <p className="text-xs text-slate-500 mt-1">{subtitle}</p>
        )}
      </div>
    </div>
  );
}
