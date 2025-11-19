/**
 * Current Activity Panel Component - Center Panel
 * Shows real-time status, progress, and tool outputs during research.
 */

'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bot,
  Sparkles,
  MessageSquare,
  Wrench,
  ChevronDown,
  Search,
  FileText,
  Github,
  FileUp,
  Loader2,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { cn, formatTimeAgo } from '@/lib/utils';
import type { ActivityState, ToolOutputSummary } from '@/types';

interface CurrentActivityPanelProps {
  activityState: ActivityState | null;
  toolOutputs: ToolOutputSummary[];
  className?: string;
}

/**
 * Displays the current research activity and agent status in real-time.
 *
 * Features:
 * - Agent status with animated icon
 * - Progress bar with ETA
 * - Latest update messages
 * - Tool output summaries with collapsible details
 *
 * @example
 * ```tsx
 * <CurrentActivityPanel
 *   activityState={currentActivity}
 *   toolOutputs={toolOutputs}
 * />
 * ```
 */
export function CurrentActivityPanel({
  activityState,
  toolOutputs,
  className,
}: CurrentActivityPanelProps) {
  const [expandedTools, setExpandedTools] = React.useState<Set<string>>(new Set());

  const toggleTool = (toolId: string) => {
    setExpandedTools((prev) => {
      const next = new Set(prev);
      if (next.has(toolId)) {
        next.delete(toolId);
      } else {
        next.add(toolId);
      }
      return next;
    });
  };

  if (!activityState) {
    return (
      <Card className={cn('h-full border-slate-700/50 bg-slate-800/50 backdrop-blur', className)}>
        <CardContent className="flex flex-col items-center justify-center h-full text-center p-8">
          <Bot className="w-16 h-16 text-slate-600 mb-4" />
          <p className="text-slate-400 text-lg mb-2">Ready to start research</p>
          <p className="text-slate-500 text-sm">
            Enter a query above to begin
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn('h-full border-slate-700/50 bg-slate-800/50 backdrop-blur', className)}>
      <CardHeader className="border-b border-slate-700/50">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <motion.div
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ repeat: Infinity, duration: 2 }}
            >
              <Bot className="w-5 h-5 text-indigo-400" />
            </motion.div>
            Current Activity
          </CardTitle>
          <Badge variant="outline" className="animate-pulse">
            {activityState.currentPhase}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="p-6 space-y-6 overflow-y-auto h-[calc(100%-80px)] scrollbar-thin">
        {/* Agent Status */}
        <AgentStatus activityState={activityState} />

        {/* Latest Update */}
        <LatestUpdate update={activityState.latestUpdate} />

        {/* Tool Outputs */}
        {toolOutputs.length > 0 && (
          <ToolOutputs
            toolOutputs={toolOutputs}
            expandedTools={expandedTools}
            onToggle={toggleTool}
          />
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Agent status component showing current activity and progress
 */
interface AgentStatusProps {
  activityState: ActivityState;
}

function AgentStatus({ activityState }: AgentStatusProps) {
  return (
    <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-700/50">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center animate-pulse">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-200">Researcher Agent</h3>
            <p className="text-sm text-slate-400">
              Iteration {activityState.currentIteration}/{activityState.maxIterations}
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <div>
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-slate-400">Currently:</span>
            <span className="text-slate-200">{activityState.currentActivity}</span>
          </div>
          <Progress value={activityState.progress} className="h-2" />
        </div>

        <div className="flex items-center gap-4 text-xs text-slate-400">
          <span>⏱️ {activityState.elapsed}s elapsed</span>
          {activityState.estimatedTimeRemaining > 0 && (
            <span>🔄 ETA ~{activityState.estimatedTimeRemaining}s</span>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Latest update message component
 */
interface LatestUpdateProps {
  update: {
    id: string;
    message: string;
    timestamp: Date;
  };
}

function LatestUpdate({ update }: LatestUpdateProps) {
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={update.id}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className="p-4 rounded-lg bg-indigo-500/10 border border-indigo-500/20"
      >
        <div className="flex items-start gap-3">
          <MessageSquare className="w-5 h-5 text-indigo-400 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <p className="text-sm text-slate-200 leading-relaxed">{update.message}</p>
            <span className="text-xs text-slate-500 mt-1 block">
              {formatTimeAgo(update.timestamp)}
            </span>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

/**
 * Tool outputs section
 */
interface ToolOutputsProps {
  toolOutputs: ToolOutputSummary[];
  expandedTools: Set<string>;
  onToggle: (toolId: string) => void;
}

function ToolOutputs({ toolOutputs, expandedTools, onToggle }: ToolOutputsProps) {
  return (
    <div className="space-y-3">
      <h4 className="text-sm font-medium text-slate-300 flex items-center gap-2">
        <Wrench className="w-4 h-4" />
        Tool Outputs ({toolOutputs.length})
      </h4>

      {toolOutputs.map((output) => (
        <ToolOutputCard
          key={output.id}
          output={output}
          isExpanded={expandedTools.has(output.id)}
          onToggle={() => onToggle(output.id)}
        />
      ))}
    </div>
  );
}

/**
 * Individual tool output card
 */
interface ToolOutputCardProps {
  output: ToolOutputSummary;
  isExpanded: boolean;
  onToggle: () => void;
}

function ToolOutputCard({ output, isExpanded, onToggle }: ToolOutputCardProps) {
  const toolIcon = getToolIcon(output.tool);

  return (
    <Card className="bg-slate-900/30 border-slate-700/30">
      <button
        onClick={onToggle}
        className="w-full p-3 flex items-center justify-between hover:bg-slate-900/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          {toolIcon}
          <div className="text-left">
            <div className="font-medium text-sm text-slate-200">{output.tool}</div>
            <div className="text-xs text-slate-400">{output.resultsCount} results</div>
          </div>
        </div>
        <ChevronDown
          className={cn(
            'w-4 h-4 text-slate-400 transition-transform',
            isExpanded && 'rotate-180'
          )}
        />
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-slate-700/30"
          >
            <div className="p-3 space-y-2">
              {output.summaries.slice(0, 3).map((summary, idx) => (
                <div
                  key={idx}
                  className="p-2 rounded bg-slate-900/50 text-sm text-slate-300"
                >
                  <div className="font-medium mb-1 text-slate-200">{summary.title}</div>
                  <p className="text-xs text-slate-400 line-clamp-2">{summary.summary}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <Badge variant="outline" className="text-xs">
                      Relevance: {(summary.relevance * 10).toFixed(1)}/10
                    </Badge>
                  </div>
                </div>
              ))}

              {output.summaries.length > 3 && (
                <Button variant="ghost" size="sm" className="w-full mt-2">
                  View all {output.resultsCount} results
                </Button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}

/**
 * Get the appropriate icon for each tool
 */
function getToolIcon(toolName: string): React.ReactNode {
  const iconMap: Record<string, React.ReactNode> = {
    web_search: <Search className="w-5 h-5 text-cyan-400" />,
    arxiv_search: <FileText className="w-5 h-5 text-purple-400" />,
    github_search: <Github className="w-5 h-5 text-orange-400" />,
    pdf_parser: <FileUp className="w-5 h-5 text-emerald-400" />,
  };

  return iconMap[toolName] || <Wrench className="w-5 h-5 text-slate-400" />;
}
