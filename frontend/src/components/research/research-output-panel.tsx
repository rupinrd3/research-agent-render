/**
 * Research Output Panel Component - Right Panel
 * Displays the final research report with markdown rendering and sources.
 */

'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  FileText,
  Loader2,
  FileQuestion,
  Link2,
  Copy,
  Download,
  Share2,
  Check,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn, copyToClipboard } from '@/lib/utils';
import type { ResearchReport, Source } from '@/types';

interface ResearchOutputPanelProps {
  report: ResearchReport | null;
  isGenerating: boolean;
  onExport?: (format: string) => void;
  className?: string;
}

/**
 * Displays the generated research report with formatted content and sources.
 *
 * Features:
 * - Markdown rendering with syntax highlighting
 * - Animated content appearance
 * - Source citations with metadata
 * - Export options (copy, download, share)
 * - Empty state with helpful message
 *
 * @example
 * ```tsx
 * <ResearchOutputPanel
 *   report={currentReport}
 *   isGenerating={false}
 *   onExport={(format) => exportReport(format)}
 * />
 * ```
 */
export function ResearchOutputPanel({
  report,
  isGenerating,
  onExport,
  className,
}: ResearchOutputPanelProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (report) {
      const fullText = `# ${report.title}\n\n${report.executiveSummary}\n\n${report.sections
        .map((s) => `## ${s.title}\n\n${s.content}`)
        .join('\n\n')}`;
      await copyToClipboard(fullText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <Card className={cn('h-full border-slate-800 bg-slate-900/60 backdrop-blur shadow-lg text-white', className)}>
      <CardHeader className="border-b border-slate-800">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg text-white">
            <FileText className="w-5 h-5 text-indigo-400" />
            Research Output
          </CardTitle>
          {isGenerating && (
            <Badge variant="outline" className="animate-pulse border-slate-700 text-white">
              <Loader2 className="w-3 h-3 mr-1 animate-spin text-indigo-300" />
              Generating...
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="p-6 overflow-y-auto h-[calc(100%-120px)] scrollbar-thin text-white">
        {report ? (
          <ReportContent report={report} />
        ) : (
          <EmptyState isGenerating={isGenerating} />
        )}
      </CardContent>

      {report && (
        <CardFooter className="border-t border-slate-800 p-4">
          <div className="flex items-center gap-2 w-full">
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopy}
              disabled={copied}
              className="border-slate-700 text-white hover:border-slate-500"
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4 mr-2" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4 mr-2" />
                  Copy
                </>
              )}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onExport?.('md')}
              className="border-slate-700 text-white hover:border-slate-500"
            >
              <Download className="w-4 h-4 mr-2" />
              Export Markdown
            </Button>
            <Button variant="outline" size="sm" className="border-slate-700 text-white hover:border-slate-500">
              <Share2 className="w-4 h-4 mr-2" />
              Share
            </Button>
          </div>
        </CardFooter>
      )}
    </Card>
  );
}

/**
 * Report content component with markdown rendering
 */
interface ReportContentProps {
  report: ResearchReport;
}

function ReportContent({ report }: ReportContentProps) {
  const filteredSections = (report.sections || []).filter(
    (section) => !/^sources?/i.test(section.title?.trim() || '')
  );

  return (
    <div className="prose prose-invert prose-sm max-w-none prose-headings:text-white prose-p:text-white prose-li:text-white prose-strong:text-white">
      {/* Title */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-2xl font-bold mb-4 text-white">{report.title}</h1>
      </motion.div>

      {/* Executive Summary */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <h2 className="text-xl font-semibold mt-6 mb-3 text-white">
          Executive Summary
        </h2>
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={markdownComponents}
        >
          {report.executiveSummary}
        </ReactMarkdown>
      </motion.div>

      {/* Sections */}
      <AnimatePresence>
        {filteredSections.map((section, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 + idx * 0.1 }}
          >
            <h2 className="text-xl font-semibold mt-6 mb-3 text-white">
              {section.title}
            </h2>
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={markdownComponents}
            >
              {section.content}
            </ReactMarkdown>
          </motion.div>
        ))}
      </AnimatePresence>

      {/* Sources */}
      {report.sources && report.sources.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-8 p-4 rounded-lg bg-slate-900/50 border border-slate-700/50"
        >
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-white">
            <Link2 className="w-5 h-5" />
            Sources ({report.sources.length})
          </h3>
          <div className="space-y-2">
            {report.sources.map((source, idx) => (
              <SourceCard key={idx} source={source} index={idx} />
            ))}
          </div>
        </motion.div>
      )}

      {/* Metadata */}
      {report.metadata && (
        <div className="mt-6 pt-4 border-t border-slate-700/50 text-xs text-white">
          <div className="flex items-center gap-4">
            <span>Words: {report.metadata.wordCount.toLocaleString()}</span>
            <span>Sources: {report.metadata.sourcesCount}</span>
            <span>Generated: {new Date(report.generatedAt).toLocaleString()}</span>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Source card component
 */
interface SourceCardProps {
  source: Source;
  index: number;
}

function SourceCard({ source, index }: SourceCardProps) {
  return (
    <div className="p-3 rounded bg-slate-900/50 hover:bg-slate-900 transition-colors">
      <div className="flex items-start gap-3">
        <span className="text-xs font-mono text-white flex-shrink-0">[{index + 1}]</span>
        <div className="flex-1 min-w-0">
          <a
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-indigo-400 hover:text-indigo-300 hover:underline block truncate"
          >
            {source.title}
          </a>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <Badge variant="outline" className="text-xs">
              {source.type}
            </Badge>
            {source.date && (
              <span className="text-xs text-white">{source.date}</span>
            )}
            {source.authors && source.authors.length > 0 && (
              <span className="text-xs text-white">
                {source.authors.slice(0, 2).join(', ')}
                {source.authors.length > 2 && ' et al.'}
              </span>
            )}
          </div>
          {source.summary && (
            <p className="text-xs text-white mt-1 line-clamp-2">{source.summary}</p>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Empty state component
 */
interface EmptyStateProps {
  isGenerating: boolean;
}

function EmptyState({ isGenerating }: EmptyStateProps) {
  if (isGenerating) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center">
        <Loader2 className="w-12 h-12 text-indigo-400 mb-4 animate-spin" />
        <p className="text-white text-lg mb-2">Generating report...</p>
        <p className="text-white text-sm">
          The agent is synthesizing findings into a comprehensive report
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center h-full text-center">
      <FileQuestion className="w-16 h-16 text-white mb-4" />
      <p className="text-white text-lg mb-2">No research output yet</p>
      <p className="text-white text-sm">
        Start a research query to see results here
      </p>
    </div>
  );
}

/**
 * Custom markdown components with styling
 */
const markdownComponents = {
  h1: ({ node, ...props }: any) => (
    <h1 className="text-2xl font-bold mb-4 text-white" {...props} />
  ),
  h2: ({ node, ...props }: any) => (
    <h2 className="text-xl font-semibold mt-6 mb-3 text-white" {...props} />
  ),
  h3: ({ node, ...props }: any) => (
    <h3 className="text-lg font-medium mt-4 mb-2 text-white" {...props} />
  ),
  p: ({ node, ...props }: any) => (
    <p className="text-white leading-relaxed mb-4" {...props} />
  ),
  code: ({ node, inline, ...props }: any) =>
    inline ? (
      <code
        className="px-1.5 py-0.5 rounded bg-slate-900/80 text-cyan-400 text-sm font-mono"
        {...props}
      />
    ) : (
      <code
        className="block p-4 rounded-lg bg-slate-900 text-sm font-mono overflow-x-auto"
        {...props}
      />
    ),
  a: ({ node, ...props }: any) => (
    <a
      className="text-indigo-400 hover:text-indigo-300 underline decoration-indigo-500/30 hover:decoration-indigo-500 transition-colors"
      target="_blank"
      rel="noopener noreferrer"
      {...props}
    />
  ),
  ul: ({ node, ...props }: any) => (
    <ul className="list-disc list-inside space-y-2 mb-4 text-white" {...props} />
  ),
  ol: ({ node, ...props }: any) => (
    <ol className="list-decimal list-inside space-y-2 mb-4 text-white" {...props} />
  ),
  blockquote: ({ node, ...props }: any) => (
    <blockquote
      className="border-l-4 border-indigo-500 pl-4 italic text-white my-4"
      {...props}
    />
  ),
};
