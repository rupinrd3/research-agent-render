/**
 * Main Research Page Component
 * Integrates all panels: Header, Query Input, ReAct Trace, Current Activity, and Research Output.
 * Manages WebSocket connections and real-time state updates.
 */

'use client';

import React, { useEffect, useState } from 'react';
import { Header } from '@/components/research/header';
import { QueryInput } from '@/components/research/query-input';
import { ReactTraceTimeline } from '@/components/research/react-trace-timeline';
import { ResearchOutputPanel } from '@/components/research/research-output-panel';
import { SettingsModal } from '@/components/research/settings-modal';
import { MetricsDashboard } from '@/components/research/metrics-dashboard';
import { WorkflowChart } from '@/components/workflow/WorkflowChart';
import { useResearchStore, useMetrics } from '@/store/research-store';
import { useWebSocket } from '@/hooks/use-websocket';
import { useWorkflowStore } from '@/stores/workflowStore';
import { cn } from '@/lib/utils';
import type { ResearchReport } from '@/types';

/**
 * Main application page component.
 *
 * Layout:
 * - Fixed header at top
 * - Query input below header
 * - Workflow visualization (full width)
 * - Two-column layout:
 *   - Left (50%): ReAct Trace Timeline
 *   - Right (50%): Research Output Panel
 *
 * Features:
 * - Real-time WebSocket updates
 * - Responsive three-panel layout
 * - State management with Zustand
 * - Smooth animations with Framer Motion
 */
export default function ResearchPage() {
  const [showSettings, setShowSettings] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  // Get state and actions from store
  const {
    currentSession,
    isResearching,
    iterations,
    activityState,
    toolOutputs,
    report,
    isGeneratingReport,
    startResearch,
    stopResearch,
  } = useResearchStore();

  // Get metrics from store
  const metrics = useMetrics();

  // Get workflow store for event handling
  const { handleEvent: handleWorkflowEvent } = useWorkflowStore();

  // WebSocket connection for real-time updates
  const { isConnected, status } = useWebSocket({
    sessionId: currentSession?.id || null,
    sessionUrl: currentSession?.websocketUrl || null,
    enabled: !!currentSession,
    onUpdate: (update) => {
      // Map WebSocket event types to workflow event types
      const workflowEventTypes = [
        'session_start', 'session_complete', 'session_failed',
        'iteration_start', 'thought', 'action', 'tool_execution',
        'observation', 'finish_guard', 'finish',
        'evaluator_start', 'evaluator_complete',
        'tool_blocked', 'error'
      ];

      // Forward only supported events to workflow store
      if (workflowEventTypes.includes(update.type)) {
        handleWorkflowEvent({
          type: update.type as any,
          timestamp: update.timestamp.toISOString(),
          iteration: update.iteration || 0,
          nodeId: undefined,
          edgeId: undefined,
          data: update.data || {}
        });
      }
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
    },
  });

  /**
   * Handle research submission
   */
  const handleStartResearch = async (query: string) => {
    try {
      await startResearch(query);
    } catch (error) {
      console.error('Failed to start research:', error);
    }
  };

  const buildMarkdownReport = (currentReport: ResearchReport) => {
    const orderedSections = [...(currentReport.sections || [])].sort(
      (a, b) => a.order - b.order
    );
    const sectionsMarkdown = orderedSections
      .map((section) => `## ${section.title}\n\n${section.content}`)
      .join('\n\n');
    const sourcesMarkdown = (currentReport.sources || [])
      .map(
        (source, index) =>
          `- [${index + 1}] ${source.title} (${source.url})${
            source.type ? ` | ${source.type}` : ''
          }`
      )
      .join('\n');

    const metadata = currentReport.metadata
      ? `\n\n_Generated in ${Math.round(
          currentReport.metadata.generationTime / 1000
        )}s | ${currentReport.metadata.wordCount} words | ${
          currentReport.metadata.sourcesCount
        } sources_`
      : '';

    return `# ${currentReport.title}\n\n## Executive Summary\n${
      currentReport.executiveSummary
    }\n\n${sectionsMarkdown}\n\n## Sources\n${
      sourcesMarkdown || 'No sources provided.'
    }\n${metadata}`;
  };

  /**
   * Handle export functionality
   */
  const handleExport = (_format?: string) => {
    if (!report) return;
    const markdown = buildMarkdownReport(report);

    const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `research-${currentSession?.id || 'report'}.md`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  return (
    <div className="min-h-screen bg-black">
      {/* Header */}
      <Header
        onSettingsClick={() => setShowSettings(true)}
        onHistoryClick={() => setShowHistory(true)}
      />

      {/* Main Content */}
      <main className="pt-20 px-6 pb-6">
        <div className="container mx-auto max-w-[1920px]">
          {/* Query Input */}
          <QueryInput
            onSubmit={handleStartResearch}
            isResearching={isResearching}
          />

          {/* WebSocket Status Indicator (for debugging) */}
          {process.env.NODE_ENV === 'development' && currentSession && (
            <div className="mb-4 text-xs text-gray-500 flex items-center gap-2">
              <div
                className={cn(
                  'w-2 h-2 rounded-full',
                  isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'
                )}
              />
              WebSocket: {status}
            </div>
          )}

          {/* Workflow Visualization (Full Width) */}
          {currentSession && (
            <div className="mb-6 animate-in fade-in duration-300">
              <WorkflowChart />
            </div>
          )}

          {/* Two-Column Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-[700px] max-h-[calc(100vh-380px)] animate-in fade-in duration-300">
            {/* Left Panel: ReAct Trace Timeline */}
            <div className="h-full">
              <ReactTraceTimeline iterations={iterations} />
            </div>

            {/* Right Panel: Research Output */}
            <div className="h-full">
              <ResearchOutputPanel
                report={report}
                isGenerating={isGeneratingReport}
                onExport={handleExport}
              />
            </div>
          </div>

          {/* Metrics Dashboard (appears after research completes) */}
          <MetricsDashboard
            current={metrics.current}
            inception={metrics.inception}
          />
        </div>
      </main>

      {/* Stop Research Button (floating) */}
      {isResearching && (
        <div className="fixed bottom-8 right-8 z-50 animate-in fade-in zoom-in duration-300">
          <button
            onClick={stopResearch}
            className="px-6 py-3 rounded-full bg-red-600 hover:bg-red-700 text-white font-medium shadow-lg hover:shadow-xl transition-all flex items-center gap-2"
          >
            <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
            Stop Research
          </button>
        </div>
      )}

      {/* Settings Modal */}
      <SettingsModal open={showSettings} onOpenChange={setShowSettings} />

      {/* TODO: History Modal */}
      {/* <HistoryModal open={showHistory} onOpenChange={setShowHistory} /> */}
    </div>
  );
}
