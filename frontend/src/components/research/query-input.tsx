/**
 * Query Input component for submitting research queries.
 * Features example queries, character counting, and validation.
 */

'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Settings, Play, Loader2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { EXAMPLE_QUERIES, MAX_VALUES } from '@/lib/constants';
import type { ExampleQuery } from '@/types';

interface QueryInputProps {
  onSubmit: (query: string) => void;
  isResearching: boolean;
  className?: string;
}

/**
 * Research query input component with example suggestions.
 *
 * Features:
 * - Multi-line textarea with character limit
 * - Example query suggestions with categories
 * - Visual feedback for input length
 * - Disabled state during research
 *
 * @example
 * ```tsx
 * <QueryInput
 *   onSubmit={(query) => startResearch(query)}
 *   isResearching={isResearching}
 * />
 * ```
 */
export function QueryInput({ onSubmit, isResearching, className }: QueryInputProps) {
  const [query, setQuery] = useState('');
  const [showExamples, setShowExamples] = useState(false);

  const handleSubmit = () => {
    if (query.trim() && !isResearching) {
      onSubmit(query.trim());
    }
  };

  const handleExampleClick = (example: ExampleQuery) => {
    setQuery(example.query);
    setShowExamples(false);
  };

  const isValidLength = query.length <= MAX_VALUES.QUERY_LENGTH;
  const canSubmit = query.trim().length > 0 && isValidLength && !isResearching;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn('mb-8', className)}
    >
      <Card className="border-slate-700/50 bg-slate-800/50 backdrop-blur">
        <CardContent className="p-6">
          {/* Textarea Input */}
          <div className="relative">
            <Textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && e.ctrlKey) {
                  handleSubmit();
                }
              }}
              placeholder="What would you like to research? Try: 'Latest advances in multimodal LLMs' or 'Compare RAG vs fine-tuning approaches'"
              className="min-h-[100px] text-lg bg-slate-900/50 border-slate-700 focus:border-indigo-500 transition-colors resize-none text-slate-100 placeholder-slate-500 focus:ring-0"
              disabled={isResearching}
            />

            {/* Character count */}
            <div className="absolute bottom-3 right-3 text-sm">
              <span
                className={cn(
                  'transition-colors',
                  query.length > MAX_VALUES.QUERY_LENGTH
                    ? 'text-red-400'
                    : query.length > MAX_VALUES.QUERY_LENGTH * 0.8
                    ? 'text-amber-400'
                    : query.length > MAX_VALUES.QUERY_LENGTH * 0.5
                    ? 'text-slate-400'
                    : 'text-slate-500'
                )}
              >
                {query.length} / {MAX_VALUES.QUERY_LENGTH}
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="mt-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowExamples(!showExamples)}
                disabled={isResearching}
                className="border-slate-700 text-slate-400 hover:text-white hover:border-slate-500"
              >
                <Sparkles className="w-4 h-4 mr-2 text-slate-400" />
                Example Queries
              </Button>
            </div>

            <Button
              size="lg"
              onClick={handleSubmit}
              disabled={!canSubmit}
              className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700"
            >
              {isResearching ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Researching...
                </>
              ) : (
                <>
                  <Play className="w-5 h-5 mr-2" />
                  Start Research
                </>
              )}
            </Button>
          </div>

          {/* Example Queries Dropdown */}
          {showExamples && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-4 pt-4 border-t border-slate-700/50"
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {EXAMPLE_QUERIES.map((example) => (
                  <button
                    key={example.id}
                    onClick={() => handleExampleClick(example)}
                    className="text-left p-3 rounded-lg bg-slate-900/50 hover:bg-slate-900 border border-slate-700/30 hover:border-indigo-500/50 transition-all group"
                    disabled={isResearching}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-medium text-slate-200 group-hover:text-indigo-400 transition-colors">
                        {example.title}
                      </h4>
                      <Badge variant="outline" className="text-xs">
                        {example.category}
                      </Badge>
                    </div>
                    <p className="text-sm text-slate-400 line-clamp-2">
                      {example.query}
                    </p>
                    {example.estimatedDuration && (
                      <p className="text-xs text-slate-500 mt-2">
                        Est. {example.estimatedDuration}
                      </p>
                    )}
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          {/* Help text */}
          {!isResearching && (
            <p className="mt-3 text-xs text-slate-500">
              Press <kbd className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700">Ctrl</kbd> +{' '}
              <kbd className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700">Enter</kbd> to submit
            </p>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
