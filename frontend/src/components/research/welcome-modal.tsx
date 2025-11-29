/**
 * Welcome Modal Component
 * Displays quick guide for first-time users on render.com deployment
 * Shows content from RENDER_POPUP.md on initial page load
 */

'use client';

import React, { useEffect, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

const STORAGE_KEY = 'research-agent-welcome-seen';

interface WelcomeModalProps {
  /** Force show modal regardless of localStorage */
  forceShow?: boolean;
}

/**
 * WelcomeModal displays a first-time user guide
 * Uses localStorage to track if user has seen the welcome popup
 */
export function WelcomeModal({ forceShow = false }: WelcomeModalProps) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    // Check if user has seen the welcome modal
    const hasSeenWelcome = localStorage.getItem(STORAGE_KEY);

    if (forceShow || !hasSeenWelcome) {
      // Small delay to ensure page is loaded
      const timer = setTimeout(() => {
        setOpen(true);
      }, 300);

      return () => clearTimeout(timer);
    }
  }, [forceShow]);

  const handleClose = () => {
    localStorage.setItem(STORAGE_KEY, 'true');
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => {
      if (!isOpen) handleClose();
    }}>
      <DialogContent
        className={cn(
          "max-w-[650px] max-h-[85vh] p-0 overflow-hidden",
          "bg-slate-900 border border-slate-700",
          "shadow-2xl"
        )}
        onEscapeKeyDown={handleClose}
      >
        {/* Custom Close Button */}
        <button
          onClick={handleClose}
          className="absolute right-4 top-4 z-10 rounded-lg p-2 opacity-70 transition-all hover:opacity-100 hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Close welcome guide"
        >
          <X className="h-5 w-5 text-slate-300" />
        </button>

        {/* Header */}
        <div className="bg-gradient-to-r from-slate-800 to-slate-900 px-8 py-6 border-b border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold text-white">
              Quick Guide
            </DialogTitle>
          </DialogHeader>
        </div>

        {/* Scrollable Content */}
        <div className="overflow-y-auto max-h-[calc(85vh-100px)] px-8 py-6 space-y-6 scrollbar-thin-dark">
          {/* Welcome Text */}
          <p className="text-base text-white leading-relaxed">
            This app is an <strong className="text-blue-400 font-semibold">Agentic AI Researcher</strong>: it plans, searches the web, reads sources, and writes a report for you. If you've used ChatGPT, this feels familiar—except the agent runs multiple steps and tools automatically.
          </p>

          {/* Mobile Notice */}
          <p className="text-sm text-center text-slate-300 font-semibold">
            For mobile devices, view this page in Landscape mode.
          </p>

          {/* Purpose Section */}
          <section>
            <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
              <span className="w-1 h-5 bg-blue-500 rounded-full"></span>
              Purpose
            </h2>
            <ul className="space-y-2 text-white ml-4">
              <li className="leading-relaxed">
                <strong className="text-white">For AI Developers & Risk Managers:</strong> learn the mechanics of Agentic AI solutions — how Traces capture reasoning, how objective vs. LLM-as-judge Evals behave, and whether the signals are reliable.
              </li>
              <li className="leading-relaxed">
                <strong className="text-white">For YOU:</strong> see the inner workings of agentic AI through the workflow animation and Traces while getting a concise research report.
              </li>
            </ul>
          </section>

          {/* How it works Section */}
          <section>
            <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
              <span className="w-1 h-5 bg-blue-500 rounded-full"></span>
              How it works
            </h2>
            <ul className="space-y-2 text-white ml-4 list-disc list-inside">
              <li className="leading-relaxed">You give a question or topic.</li>
              <li className="leading-relaxed">The agent creates a plan, searches the web, reads pages, and summarizes evidence.</li>
              <li className="leading-relaxed">It iterates until it has enough signal, then produces a structured report.</li>
            </ul>
          </section>

          {/* What you see Section */}
          <section>
            <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
              <span className="w-1 h-5 bg-blue-500 rounded-full"></span>
              What you see on the page
            </h2>
            <div className="space-y-3 ml-4">
              <div>
                <strong className="text-blue-400 font-semibold">Traces:</strong>{' '}
                <span className="text-white">
                  A live log of the agent's reasoning and actions (plans, searches, tool calls). Skim to see <em>why</em> it chose each step.
                </span>
              </div>
              <div>
                <strong className="text-blue-400 font-semibold">Research Output:</strong>{' '}
                <span className="text-white">
                  The final report—read this first. It includes findings, citations, and recommendations.
                </span>
              </div>
              <div>
                <strong className="text-blue-400 font-semibold">Evals / Quality Check:</strong>{' '}
                <span className="text-white">
                  A post-run self-review. It flags gaps or risks so you know how trustworthy the output is.
                </span>
              </div>
              <div>
                <strong className="text-blue-400 font-semibold">Metrics:</strong>{' '}
                <span className="text-white">
                  Tokens, cost, duration, and provider notes—helpful if you care about spend or performance.
                </span>
              </div>
            </div>
          </section>

          {/* How to use it Section */}
          <section>
            <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
              <span className="w-1 h-5 bg-blue-500 rounded-full"></span>
              How to use it
            </h2>
            <ol className="space-y-2 text-white ml-4 list-decimal list-inside">
              <li className="leading-relaxed">
                Enter a clear question (e.g., "Compare Claude Opus 4.5 vs Gemini 3 Pro for coding teams").
              </li>
              <li className="leading-relaxed">
                Let the agent run; watch Traces if you're curious.
              </li>
              <li className="leading-relaxed">
                Read the <strong className="text-blue-400">Research Output</strong>; check citations.
              </li>
              <li className="leading-relaxed">
                Glance at <strong className="text-blue-400">Evals</strong> for any warnings.
              </li>
              <li className="leading-relaxed">
                If needed, rerun with a narrower query or ask for a follow-up.
              </li>
            </ol>
          </section>

          {/* Tips Section */}
          <section className="pb-2">
            <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
              <span className="w-1 h-5 bg-blue-500 rounded-full"></span>
              Tips
            </h2>
            <ul className="space-y-2 text-white ml-4 list-disc list-inside">
              <li className="leading-relaxed">
                Provide specifics (model names, dates, constraints) for better searches.
              </li>
              <li className="leading-relaxed">
                If sources look thin, rerun with more precise wording or a smaller scope.
              </li>
              <li className="leading-relaxed">
                Traces are your transparency window—use them to judge credibility.
              </li>
            </ul>
          </section>

          {/* Call to Action */}
          <div className="pt-4 border-t border-slate-700">
            <button
              onClick={handleClose}
              className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors shadow-lg hover:shadow-xl"
            >
              Get Started
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
