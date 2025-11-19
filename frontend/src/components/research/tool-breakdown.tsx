/**
 * Tool Breakdown Component
 *
 * Expandable section showing execution times per tool.
 */

'use client';

import React from 'react';
import { ChevronRight, Wrench } from 'lucide-react';

interface ToolBreakdownProps {
  tools: Record<string, number>; // tool name -> time in ms
  isMedian?: boolean;
}

export function ToolBreakdown({ tools, isMedian = false }: ToolBreakdownProps) {
  const toolEntries = Object.entries(tools).sort((a, b) => b[1] - a[1]);

  if (toolEntries.length === 0) {
    return null;
  }

  return (
    <details className="group mt-3">
      <summary className="cursor-pointer text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 select-none">
        <ChevronRight className="w-3 h-3 group-open:rotate-90 transition-transform" />
        <Wrench className="w-3 h-3" />
        View tool breakdown ({toolEntries.length} tools)
      </summary>
      <div className="mt-3 space-y-2 pl-5">
        {toolEntries.map(([tool, time]) => (
          <div
            key={tool}
            className="flex justify-between items-center text-xs p-2 rounded bg-slate-900/30 hover:bg-slate-900/50 transition-colors"
          >
            <span className="text-slate-300">{tool}</span>
            <span className="text-slate-200 font-mono font-semibold">
              {Math.round(time)}ms
              {isMedian && (
                <span className="text-slate-500 ml-1 text-[10px]">median</span>
              )}
            </span>
          </div>
        ))}
      </div>
    </details>
  );
}
