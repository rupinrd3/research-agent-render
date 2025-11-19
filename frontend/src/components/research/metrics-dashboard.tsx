/**
 * Metrics Dashboard Component
 *
 * Displays current run and historical metrics in a modern, polished design.
 */

'use client';

import React from 'react';
import {
  Clock,
  Zap,
  Timer,
  Hash,
  Award,
  TrendingUp,
  BarChart3,
} from 'lucide-react';
import type { CurrentRunMetrics, InceptionMetrics } from '@/types';
import { MetricCard } from './metric-card';
import { ScoreBar } from './score-bar';
import { ToolBreakdown } from './tool-breakdown';

interface MetricsDashboardProps {
  current: CurrentRunMetrics | null;
  inception: InceptionMetrics | null;
}

export function MetricsDashboard({ current, inception }: MetricsDashboardProps) {
  if (!current && !inception) {
    return null; // Don't show until data available
  }

  return (
    <div className="mt-6 animate-in fade-in duration-300">
      {/* Section Header */}
      <div className="mb-6 p-6 rounded-lg border-t-2 border-indigo-500/50 bg-gradient-to-r from-slate-900/80 to-slate-800/60 backdrop-blur">
        <h2 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-indigo-400" />
          Research Metrics & Evaluation
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Performance metrics and quality scores for current run and historical trends
        </p>
      </div>

      {/* Two-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Current Run */}
        {current && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
              <Zap className="w-5 h-5 text-indigo-400" />
              Current Run
            </h3>
            <CurrentRunPanel metrics={current} />
          </div>
        )}

        {/* Inception Till Date */}
        {inception && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-indigo-400" />
              Inception Till Date
              <span className="text-xs text-slate-500 font-normal">
                ({inception.totalSessions} sessions)
              </span>
            </h3>
            <InceptionPanel metrics={inception} />
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Current Run Panel
 */
function CurrentRunPanel({ metrics }: { metrics: CurrentRunMetrics }) {
  return (
    <div className="space-y-6">
      {/* Three-Column Grid: Performance, Token & Cost, Agent Behavior */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Performance Metrics */}
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
            <Clock className="w-4 h-4 text-indigo-400" />
            Performance Metrics
          </h4>
          <div className="space-y-3">
            <MetricCard
              label="Iteration Latency"
              value={Math.round(metrics.iterationLatencyAvg)}
              unit="ms"
              icon={<Zap className="w-4 h-4" />}
              subtitle="Average per cycle"
            />
            <MetricCard
              label="End-to-End Duration"
              value={metrics.endToEndSeconds.toFixed(1)}
              unit="seconds"
              icon={<Timer className="w-4 h-4" />}
              subtitle="Total research time"
            />
          </div>

          {/* Tool Breakdown */}
          {Object.keys(metrics.toolExecutionTimes).length > 0 && (
            <div className="mt-3">
              <ToolBreakdown tools={metrics.toolExecutionTimes} />
            </div>
          )}
        </div>

        {/* Token & Cost Tracking */}
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
            <Hash className="w-4 h-4 text-indigo-400" />
            Token & Cost Tracking
          </h4>
          <div className="space-y-3">
            <MetricCard
              label="Total Tokens"
              value={metrics.totalTokens.toLocaleString()}
              icon={<Hash className="w-4 h-4" />}
              subtitle="Across all iterations"
            />
            <MetricCard
              label="Cost"
              value={`$${metrics.totalCostUsd.toFixed(4)}`}
              subtitle="Real-time USD tracking"
            />
          </div>
        </div>

        {/* Agent Behavior */}
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
            <Zap className="w-4 h-4 text-indigo-400" />
            Agent Behavior
          </h4>
          <div className="space-y-3">
            <MetricCard
              label="Iterations to Completion"
              value={metrics.iterationsToCompletion}
              subtitle="ReAct cycles needed"
            />
            <MetricCard
              label="Tool Success Rate"
              value={`${(metrics.toolSuccessRate * 100).toFixed(1)}%`}
              subtitle="Successful vs failed calls"
            />
          </div>
        </div>
      </div>

      {/* Quality Evaluation - Full Width */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <Award className="w-4 h-4 text-indigo-400" />
          Quality Evaluation
        </h4>
        <div className="space-y-2">
          <ScoreBar label="Relevance" score={metrics.evaluation.relevance} />
          <ScoreBar label="Accuracy" score={metrics.evaluation.accuracy} />
          <ScoreBar label="Completeness" score={metrics.evaluation.completeness} />
          <ScoreBar label="Source Quality" score={metrics.evaluation.sourceQuality} />
        </div>

        {/* Strengths & Weaknesses */}
        {(metrics.evaluation.strengths.length > 0 || metrics.evaluation.weaknesses.length > 0) && (
          <div className="mt-4 p-4 rounded-lg bg-slate-900/50 border border-slate-700/30 space-y-3">
            {metrics.evaluation.strengths.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-green-400 mb-2">✓ Strengths</p>
                <ul className="text-xs text-slate-300 space-y-1">
                  {metrics.evaluation.strengths.map((strength, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-green-400">•</span>
                      <span>{strength}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {metrics.evaluation.weaknesses.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-yellow-400 mb-2">⚠ Areas for Improvement</p>
                <ul className="text-xs text-slate-300 space-y-1">
                  {metrics.evaluation.weaknesses.map((weakness, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-yellow-400">•</span>
                      <span>{weakness}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Inception Panel
 */
function InceptionPanel({ metrics }: { metrics: InceptionMetrics }) {
  if (metrics.totalSessions === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center border-2 border-dashed border-slate-700/50 rounded-lg">
        <BarChart3 className="w-12 h-12 text-slate-600 mb-3" />
        <p className="text-sm text-slate-400 mb-1">No historical data yet</p>
        <p className="text-xs text-slate-500">
          Complete more research sessions to see trends
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Three-Column Grid: Performance, Token & Cost, Agent Behavior */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Performance Metrics */}
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
            <Clock className="w-4 h-4 text-indigo-400" />
            Performance Metrics
          </h4>
          <div className="space-y-3">
            <MetricCard
              label="Iteration Latency"
              value={Math.round(metrics.iterationLatencyMedian)}
              unit="ms"
              icon={<Zap className="w-4 h-4" />}
              subtitle="Median per cycle"
            />
            <MetricCard
              label="End-to-End Duration"
              value={metrics.endToEndMedian.toFixed(1)}
              unit="seconds"
              icon={<Timer className="w-4 h-4" />}
              subtitle="Median research time"
            />
          </div>

          {/* Tool Breakdown */}
          {Object.keys(metrics.tools).length > 0 && (
            <div className="mt-3">
              <ToolBreakdown tools={metrics.tools} isMedian />
            </div>
          )}
        </div>

        {/* Token & Cost Tracking */}
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
            <Hash className="w-4 h-4 text-indigo-400" />
            Token & Cost Tracking
          </h4>
          <div className="space-y-3">
            <MetricCard
              label="Avg Tokens"
              value={Math.round(metrics.avgTokens).toLocaleString()}
              icon={<Hash className="w-4 h-4" />}
              subtitle="Average per session"
            />
            <MetricCard
              label="Avg Cost"
              value={`$${metrics.avgCostUsd.toFixed(4)}`}
              subtitle="Average per session"
            />
          </div>
        </div>

        {/* Agent Behavior */}
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
            <Zap className="w-4 h-4 text-indigo-400" />
            Agent Behavior
          </h4>
          <div className="space-y-3">
            <MetricCard
              label="Avg Iterations"
              value={metrics.avgIterations.toFixed(1)}
              subtitle="Average cycles to completion"
            />
            <MetricCard
              label="Tool Success Rate"
              value={`${(metrics.toolSuccessRate * 100).toFixed(1)}%`}
              subtitle="Successful vs failed (total)"
            />
          </div>
        </div>
      </div>

      {/* Reliability Metrics - Full Width */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <Award className="w-4 h-4 text-indigo-400" />
          Reliability Metrics
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <MetricCard
            label="Session Success Rate"
            value={`${(metrics.sessionSuccessRate * 100).toFixed(1)}%`}
            subtitle={`${metrics.completedSessions} / ${metrics.totalSessions} completed`}
          />
          <MetricCard
            label="Provider Failover Rate"
            value={`${(metrics.providerFailoverRate * 100).toFixed(1)}%`}
            subtitle="LLM provider switches"
          />
        </div>
      </div>

      {/* Quality Evaluation - Full Width */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <Award className="w-4 h-4 text-indigo-400" />
          Quality Evaluation
        </h4>
        <div className="space-y-2">
          <ScoreBar label="Relevance" score={metrics.relevanceAvg} />
          <ScoreBar label="Accuracy" score={metrics.accuracyAvg} />
          <ScoreBar label="Completeness" score={metrics.completenessAvg} />
          <ScoreBar label="Source Quality" score={metrics.sourceQualityAvg} />
        </div>
      </div>
    </div>
  );
}
