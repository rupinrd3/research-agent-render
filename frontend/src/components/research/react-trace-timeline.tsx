/**
 * ReAct Trace Timeline Component - Left Panel
 * Displays the complete reasoning trace with collapsible iterations.
 * Shows Thought -> Action -> Observation -> Evaluation for each iteration.
 */

'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Activity,
  Brain,
  Zap,
  Eye,
  BarChart3,
  CheckCircle2,
  ChevronDown,
  XCircle,
  Code,
  Loader2,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn, formatDuration } from '@/lib/utils';
import type { Iteration } from '@/types';

interface ReactTraceTimelineProps {
  iterations: Iteration[];
  className?: string;
}

/**
 * Displays a timeline of ReAct iterations showing the agent's reasoning process.
 *
 * Each iteration shows:
 * - Thought (reasoning)
 * - Action (tool selection and execution)
 * - Observation (result interpretation)
 * - Evaluation (quality assessment)
 *
 * Features:
 * - Collapsible iterations for better UX
 * - Color-coded phases
 * - Real-time status indicators
 * - Token and latency metrics
 *
 * @example
 * ```tsx
 * <ReactTraceTimeline iterations={currentIterations} />
 * ```
 */
export function ReactTraceTimeline({ iterations, className }: ReactTraceTimelineProps) {
  const [expandedIteration, setExpandedIteration] = useState<string | null>(null);

  const toggleIteration = (id: string) => {
    setExpandedIteration(expandedIteration === id ? null : id);
  };

  const totalDuration = iterations.reduce((sum, iter) => sum + iter.duration, 0);

  return (
    <Card className={cn('h-full border-slate-800 bg-slate-900/60 backdrop-blur shadow-lg', className)}>
      <CardHeader className="border-b border-slate-800">
        <CardTitle className="flex items-center gap-2 text-lg text-slate-100">
          <Activity className="w-5 h-5 text-indigo-400" />
          ReAct Trace
        </CardTitle>
        <div className="flex gap-2 mt-2">
          <Badge variant="outline" className="text-xs border-slate-700 text-slate-300">
            {iterations.length} Iterations
          </Badge>
          {totalDuration > 0 && (
            <Badge variant="outline" className="text-xs border-slate-700 text-slate-300">
              {formatDuration(totalDuration / 1000)}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="p-4 overflow-y-auto h-[calc(100%-80px)] scrollbar-thin">
        <div className="space-y-4">
          {iterations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Activity className="w-12 h-12 text-slate-600 mb-3" />
              <p className="text-slate-300">No iterations yet</p>
              <p className="text-sm text-slate-500 mt-1">
                Iterations will appear here as research progresses
              </p>
            </div>
          ) : (
            iterations.map((iteration, idx) => (
              <IterationCard
                key={iteration.id}
                iteration={iteration}
                index={idx}
                isExpanded={expandedIteration === iteration.id}
                onToggle={() => toggleIteration(iteration.id)}
              />
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Individual iteration card component
 */
interface IterationCardProps {
  iteration: Iteration;
  index: number;
  isExpanded: boolean;
  onToggle: () => void;
}

function IterationCard({ iteration, index, isExpanded, onToggle }: IterationCardProps) {
  const numericIndex = typeof iteration.index === 'number' && iteration.index > 0
    ? iteration.index
    : index + 1;
  const isAutoFinish = iteration.mode === 'auto_finish';
  const displayToken = isAutoFinish ? 'AF' : numericIndex;
  const title = isAutoFinish ? 'Final Report (Auto-Finish)' : `Iteration ${numericIndex}`;
  const isComplete = iteration.status === 'complete';
  const isFailed = iteration.status === 'failed';
  const isActive = !isComplete && !isFailed;

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1 }}
      className="relative"
    >
      <button
        onClick={onToggle}
        className="w-full text-left"
      >
        <div
          className={cn(
            'flex items-center justify-between p-3 rounded-lg transition-all cursor-pointer border',
            isActive
              ? 'bg-indigo-500/10 border-indigo-500/40'
              : 'bg-slate-900/50 border-slate-800 hover:border-slate-700',
            isFailed && 'bg-red-500/10 border-red-500/40'
          )}
        >
          <div className="flex items-center gap-3">
            <div
              className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm',
                isComplete && 'bg-emerald-500/15 text-emerald-300',
                isActive && 'bg-indigo-500/20 text-indigo-200 animate-pulse',
                isFailed && 'bg-red-500/15 text-red-300'
              )}
            >
              {isActive ? <Loader2 className="w-4 h-4 animate-spin" /> : displayToken}
            </div>
            <div>
              <span className="font-medium text-slate-100">{title}</span>
              {isComplete && (
                <CheckCircle2 className="w-4 h-4 text-emerald-400 inline ml-2" />
              )}
              {isFailed && (
                <XCircle className="w-4 h-4 text-red-400 inline ml-2" />
              )}
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-400">
              {formatDuration(iteration.duration / 1000)}
            </span>
            <ChevronDown
              className={cn(
                'w-4 h-4 text-slate-400 transition-transform',
                isExpanded && 'rotate-180'
              )}
            />
          </div>
        </div>
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="pt-2 pl-11 space-y-3"
          >
            {/* THOUGHT */}
            <PhaseCard
              icon={<Brain className="w-4 h-4" />}
              title="THOUGHT"
              color="purple"
              content={iteration.thought.content}
              metadata={[
                { label: 'Tokens', value: iteration.thought.tokens },
                { label: 'Latency', value: `${iteration.thought.latency}ms` },
              ]}
            />

            {/* ACTION */}
            <PhaseCard
              icon={<Zap className="w-4 h-4" />}
              title="ACTION"
              color="cyan"
            >
              <div className="flex items-center gap-2">
                <Code className="w-4 h-4 text-cyan-400" />
                <code className="text-sm font-mono text-cyan-300">
                  {iteration.action.toolName}({JSON.stringify(iteration.action.toolParams, null, 2).substring(0, 50)}...)
                </code>
              </div>
            </PhaseCard>

            {/* EXECUTION STATUS */}
            <PhaseCard
              icon={
                iteration.action.success ? (
                  <CheckCircle2 className="w-4 h-4" />
                ) : (
                  <XCircle className="w-4 h-4" />
                )
              }
              title="EXECUTION"
              color={iteration.action.success ? 'green' : 'red'}
              content={
                iteration.action.result?.summary ||
                iteration.action.error ||
                'Executing...'
              }
              metadata={[
                { label: 'Duration', value: `${iteration.action.duration}ms` },
                { label: 'Results', value: iteration.action.result?.count || 0 },
              ]}
            />

            {/* OBSERVATION */}
            <PhaseCard
              icon={<Eye className="w-4 h-4" />}
              title="OBSERVATION"
              color="emerald"
              content={iteration.observation.content}
            />

            {/* EVALUATION */}
            {iteration.evaluation && (
              <PhaseCard
                icon={<BarChart3 className="w-4 h-4" />}
                title="EVALUATION"
                color="amber"
              >
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <MetricDisplay
                    label="Tool Selection"
                    value={iteration.evaluation.toolSelectionScore}
                  />
                  <MetricDisplay
                    label="Execution"
                    value={iteration.evaluation.toolExecutionScore}
                  />
                  <MetricDisplay
                    label="Progress"
                    value={iteration.evaluation.progressScore}
                  />
                  <MetricDisplay
                    label="Info Gain"
                    value={iteration.evaluation.informationGain}
                  />
                </div>
                {iteration.evaluation.reasoning && (
                  <p className="mt-2 text-xs text-slate-400 italic">
                    {iteration.evaluation.reasoning}
                  </p>
                )}
              </PhaseCard>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

/**
 * Phase card for displaying iteration phases
 */
interface PhaseCardProps {
  icon: React.ReactNode;
  title: string;
  color: 'purple' | 'cyan' | 'green' | 'red' | 'emerald' | 'amber';
  content?: string;
  metadata?: Array<{ label: string; value: string | number }>;
  children?: React.ReactNode;
}

function PhaseCard({ icon, title, color, content, metadata, children }: PhaseCardProps) {
  const colorClasses = {
    purple: 'bg-purple-500/10 border-purple-400/40 text-purple-200',
    cyan: 'bg-cyan-500/10 border-cyan-400/40 text-cyan-200',
    green: 'bg-green-500/10 border-green-400/40 text-green-200',
    red: 'bg-red-500/10 border-red-400/40 text-red-200',
    emerald: 'bg-emerald-500/10 border-emerald-400/40 text-emerald-200',
    amber: 'bg-amber-500/10 border-amber-400/40 text-amber-100',
  };

  const iconColor = {
    purple: 'text-purple-300',
    cyan: 'text-cyan-300',
    green: 'text-green-300',
    red: 'text-red-300',
    emerald: 'text-emerald-300',
    amber: 'text-amber-200',
  };

  return (
    <div className={cn('p-3 rounded-lg border', colorClasses[color])}>
      <div className="flex items-center gap-2 mb-2">
        <span className={iconColor[color]}>{icon}</span>
        <span className="font-medium text-sm">{title}</span>
      </div>

      {content && (
        <p className="text-sm text-slate-200 leading-relaxed mb-2">{content}</p>
      )}

      {children}

      {metadata && metadata.length > 0 && (
        <div className="flex gap-4 mt-2 text-xs text-slate-400">
          {metadata.map((item, idx) => (
            <span key={idx}>
              {item.label}: <span className="text-slate-100">{item.value}</span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Metric display component for evaluation scores
 */
interface MetricDisplayProps {
  label: string;
  value: number;
}

function MetricDisplay({ label, value }: MetricDisplayProps) {
  return (
    <div>
      <span className="text-slate-400">{label}:</span>
      <span className="ml-2 text-slate-100 font-medium">{value.toFixed(1)}/10</span>
    </div>
  );
}
