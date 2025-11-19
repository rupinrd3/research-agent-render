/**
 * Global state management using Zustand.
 * Manages research sessions, iterations, and real-time updates.
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type {
  ResearchSession,
  Iteration,
  ResearchReport,
  ActivityState,
  ToolOutputSummary,
  Settings,
  LoadingState,
  HistoryItem,
  MetricsState,
} from '@/types';
import { DEFAULT_SETTINGS, SETTINGS_VERSION } from '@/lib/constants';

const createBaselineActivityState = (
  maxIterations: number = DEFAULT_SETTINGS.maxIterations,
): ActivityState => ({
  currentPhase: 'starting',
  currentIteration: 0,
  currentActivity: 'Initializing research session...',
  progress: 0,
  elapsed: 0,
  estimatedTimeRemaining: 0,
  maxIterations,
  latestUpdate: {
    id: Date.now().toString(),
    message: 'Awaiting updates...',
    timestamp: new Date(),
  },
});

/**
 * Research store state interface
 */
interface ResearchState {
  // Current session
  currentSession: ResearchSession | null;
  isResearching: boolean;
  loadingState: LoadingState;
  error: string | null;

  // Iterations
  iterations: Iteration[];
  expandedIteration: string | null;

  // Activity state (for center panel)
  activityState: ActivityState | null;
  toolOutputs: ToolOutputSummary[];

  // Report
  report: ResearchReport | null;
  isGeneratingReport: boolean;

  // Settings
  settings: Settings;
  settingsVersion: number;

  // History
  history: HistoryItem[];

  // Metrics
  metrics: MetricsState;

  // Actions - Session management
  startResearch: (query: string) => Promise<void>;
  stopResearch: () => void;
  resetSession: () => void;
  setCurrentSession: (session: ResearchSession | null) => void;

  // Actions - Iterations
  addIteration: (iteration: Iteration) => void;
  updateIteration: (id: string, updates: Partial<Iteration>) => void;
  setExpandedIteration: (id: string | null) => void;

  // Actions - Activity
  updateActivityState: (state: Partial<ActivityState>) => void;
  addToolOutput: (output: ToolOutputSummary) => void;
  clearToolOutputs: () => void;

  // Actions - Report
  setReport: (report: ResearchReport | null) => void;
  appendReportChunk: (chunk: string) => void;

  // Actions - Settings
  updateSettings: (settings: Partial<Settings>) => void;
  setResearching: (value: boolean) => void;

  // Actions - History
  addHistoryItem: (item: HistoryItem) => void;
  removeHistoryItem: (id: string) => void;
  clearHistory: () => void;

  // Actions - Metrics
  setMetrics: (metrics: MetricsState) => void;
  fetchMetricsSummary: () => Promise<void>;

  // Actions - Error handling
  setError: (error: string | null) => void;
  clearError: () => void;
}

/**
 * Create the research store
 */
export const useResearchStore = create<ResearchState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        currentSession: null,
        isResearching: false,
        loadingState: 'idle',
        error: null,

        iterations: [],
        expandedIteration: null,

        activityState: null,
        toolOutputs: [],

        report: null,
        isGeneratingReport: false,

        settings: DEFAULT_SETTINGS,
        settingsVersion: SETTINGS_VERSION,

        history: [],

        metrics: {
          current: null,
          inception: null,
        },

        // Session management actions
        startResearch: async (query: string) => {
          try {
            const { settings } = get();
            set({
              isResearching: true,
              loadingState: 'loading',
              error: null,
              iterations: [],
              toolOutputs: [],
              report: null,
              activityState: {
                ...createBaselineActivityState(settings.maxIterations),
                latestUpdate: {
                  id: Date.now().toString(),
                  message: 'Starting research...',
                  timestamp: new Date(),
                },
              },
            });
            const response = await fetch(
              `${process.env.NEXT_PUBLIC_API_URL}/api/research/start`,
              {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  query,
                  config: {
                    llm: {
                      provider: settings.llmProvider,
                      model: settings.llmModel,
                      temperature: settings.temperature,
                    },
                    research: {
                      max_iterations: settings.maxIterations,
                    },
                  },
                }),
              }
            );

            if (!response.ok) {
              throw new Error('Failed to start research session');
            }

            const data = await response.json();

            set({
              currentSession: {
                id: data.session_id,
                query,
                status: 'running',
                startTime: new Date(),
                websocketUrl: data.websocket_url || `/ws/${data.session_id}`,
                iterations: [],
                metadata: {
                  totalTokens: 0,
                  totalCost: 0,
                  llmProvider: settings.llmProvider,
                  llmModel: settings.llmModel,
                  iterationCount: 0,
                  toolCallsCount: 0,
                  maxIterations: settings.maxIterations,
                },
              },
              loadingState: 'success',
            });
          } catch (error) {
            set({
              error: error instanceof Error ? error.message : 'Failed to start research',
              isResearching: false,
              loadingState: 'error',
            });
          }
        },

        setResearching: (value) => {
          set({ isResearching: value });
        },

        stopResearch: () => {
          set({ isResearching: false });
          const session = get().currentSession;
          if (session) {
            set({
              currentSession: {
                ...session,
                status: 'cancelled',
                endTime: new Date(),
              },
            });
          }
        },

        resetSession: () => {
          set({
            currentSession: null,
            isResearching: false,
            iterations: [],
            expandedIteration: null,
            activityState: null,
            toolOutputs: [],
            report: null,
            isGeneratingReport: false,
            error: null,
            loadingState: 'idle',
          });
        },

        setCurrentSession: (session) => {
          set((state) => ({
            currentSession: session,
            isResearching:
              session && session.status === 'running' ? state.isResearching : false,
          }));
        },

        // Iteration actions
        addIteration: (iteration) => {
          set((state) => ({
            iterations: [...state.iterations, iteration],
            currentSession: state.currentSession
              ? {
                  ...state.currentSession,
                  iterations: [...state.currentSession.iterations, iteration],
                  metadata: {
                    ...state.currentSession.metadata,
                    iterationCount: state.iterations.length + 1,
                  },
                }
              : null,
          }));
        },

        updateIteration: (id, updates) => {
          set((state) => ({
            iterations: state.iterations.map((iter) =>
              iter.id === id ? { ...iter, ...updates } : iter
            ),
          }));
        },

        setExpandedIteration: (id) => {
          set({ expandedIteration: id });
        },

        // Activity actions
        updateActivityState: (updates) => {
          set((state) => {
            const baseline =
              state.activityState ??
              createBaselineActivityState(state.settings.maxIterations);
            const nextLatestUpdate = updates.latestUpdate
              ? {
                  ...baseline.latestUpdate,
                  ...updates.latestUpdate,
                  timestamp:
                    updates.latestUpdate.timestamp instanceof Date
                      ? updates.latestUpdate.timestamp
                      : updates.latestUpdate.timestamp
                      ? new Date(updates.latestUpdate.timestamp)
                      : baseline.latestUpdate.timestamp,
                }
              : baseline.latestUpdate;

            return {
              activityState: {
                ...baseline,
                ...updates,
                maxIterations:
                  updates.maxIterations ?? baseline.maxIterations,
                latestUpdate: nextLatestUpdate,
              },
            };
          });
        },

        addToolOutput: (output) => {
          set((state) => ({
            toolOutputs: [...state.toolOutputs, output],
          }));
        },

        clearToolOutputs: () => {
          set({ toolOutputs: [] });
        },

        // Report actions
        setReport: (report) => {
          set({ report, isGeneratingReport: report === null });
        },

        appendReportChunk: (chunk) => {
          set((state) => {
            if (!state.report) {
              // Create initial report structure
              return {
                report: {
                  title: 'Research Report',
                  executiveSummary: chunk,
                  sections: [],
                  sources: [],
                  metadata: {
                    wordCount: chunk.split(/\s+/).length,
                    sourcesCount: 0,
                    generationTime: 0,
                  },
                  generatedAt: new Date(),
                },
                isGeneratingReport: true,
              };
            }

            // Append to existing report
            return {
              report: {
                ...state.report,
                executiveSummary: state.report.executiveSummary + chunk,
                metadata: {
                  ...state.report.metadata,
                  wordCount:
                    state.report.metadata.wordCount + chunk.split(/\s+/).length,
                },
              },
            };
          });
        },

        // Settings actions
        updateSettings: (updates) => {
          set((state) => ({
            settings: { ...state.settings, ...updates },
            settingsVersion: SETTINGS_VERSION,
          }));
        },

        // History actions
        addHistoryItem: (item) => {
          set((state) => ({
            history: [item, ...state.history].slice(0, 50), // Keep last 50
          }));
        },

        removeHistoryItem: (id) => {
          set((state) => ({
            history: state.history.filter((item) => item.id !== id),
          }));
        },

        clearHistory: () => {
          set({ history: [] });
        },

        // Metrics actions
        setMetrics: (metrics) => {
          set({ metrics });
        },

        fetchMetricsSummary: async () => {
          try {
            const response = await fetch(
              `${process.env.NEXT_PUBLIC_API_URL}/api/metrics/summary`
            );

            if (!response.ok) {
              throw new Error('Failed to fetch metrics');
            }

            const data = await response.json();

            set((state) => ({
              metrics: {
                current: state.metrics.current, // Keep current
                inception: {
                  totalSessions: data.inception.total_sessions,
                  completedSessions: data.inception.completed_sessions,
                  iterationLatencyMedian: data.inception.iteration_latency_median_ms,
                  endToEndMedian: data.inception.end_to_end_median_seconds,
                  tools: data.inception.tools,
                  avgTokens: data.inception.avg_tokens,
                  avgCostUsd: data.inception.avg_cost_usd,
                  avgIterations: data.inception.avg_iterations,
                  toolSuccessRate: data.inception.tool_success_rate,
                  sessionSuccessRate: data.inception.session_success_rate,
                  providerFailoverRate: data.inception.provider_failover_rate,
                  relevanceAvg: data.inception.relevance_avg,
                  accuracyAvg: data.inception.accuracy_avg,
                  completenessAvg: data.inception.completeness_avg,
                  sourceQualityAvg: data.inception.source_quality_avg,
                },
              },
            }));
          } catch (error) {
            console.error('Failed to fetch metrics summary:', error);
            // Set error state for UI to display
            set((state) => ({
              metrics: {
                current: state.metrics.current,
                inception: null, // Clear on error
              },
            }));
          }
        },

        // Error handling
        setError: (error) => {
          set({ error, loadingState: 'error' });
        },

        clearError: () => {
          set({ error: null });
        },
      }),
      {
        name: 'research-storage',
        partialize: (state) => ({
          settings: state.settings,
          history: state.history,
        }),
        version: SETTINGS_VERSION,
        migrate: (persistedState: any, version) => {
          if (!persistedState) {
            return persistedState;
          }
          if (version === SETTINGS_VERSION) {
            return persistedState;
          }
          return {
            ...persistedState,
            settings: DEFAULT_SETTINGS,
          };
        },
      }
    ),
    { name: 'ResearchStore' }
  )
);

/**
 * Selectors for optimized component re-renders
 */
export const useIsResearching = () => useResearchStore((state) => state.isResearching);
export const useCurrentSession = () => useResearchStore((state) => state.currentSession);
export const useIterations = () => useResearchStore((state) => state.iterations);
export const useActivityState = () => useResearchStore((state) => state.activityState);
export const useReport = () => useResearchStore((state) => state.report);
export const useSettings = () => useResearchStore((state) => state.settings);
export const useHistory = () => useResearchStore((state) => state.history);
export const useMetrics = () => useResearchStore((state) => state.metrics);
