/**
 * Custom React hook for WebSocket connection and real-time updates.
 * Handles connection lifecycle, event listeners, and automatic reconnection.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import type { Iteration, ResearchReport, ResearchUpdate, Source, WebSocketEventType } from '@/types';
import { API_ENDPOINTS } from '@/lib/constants';
import { useResearchStore } from '@/store/research-store';

/**
 * WebSocket connection status
 */
export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

/**
 * WebSocket hook options
 */
interface UseWebSocketOptions {
  sessionId: string | null;
  sessionUrl?: string | null;
  enabled?: boolean;
  onUpdate?: (update: ResearchUpdate) => void;
  onError?: (error: Error) => void;
  reconnect?: boolean;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

/**
 * WebSocket hook return type
 */
interface UseWebSocketReturn {
  status: ConnectionStatus;
  isConnected: boolean;
  error: Error | null;
  connect: () => void;
  disconnect: () => void;
  sendMessage: (event: string, data: any) => void;
}

type TransportMode = 'websocket' | 'sse';
const PHASE_PROGRESS: Record<string, number> = {
  starting: 0,
  thinking: 0.15,
  acting: 0.55,
  observing: 0.85,
  evaluating: 0.95,
  complete: 1,
};
const SSE_MAX_RETRIES = 2;

const deriveSourceType = (url: string): Source['type'] => {
  if (!url) return 'web';
  const normalized = url.toLowerCase();
  if (normalized.includes('arxiv')) return 'arxiv';
  if (normalized.includes('github')) return 'github';
  if (normalized.endsWith('.pdf')) return 'pdf';
  return 'web';
};

const normalizeSources = (raw: any): Source[] => {
  if (!raw) return [];
  if (!Array.isArray(raw)) return [];

  return raw.map((item, index) => {
    if (typeof item === 'string') {
      return {
        id: `source-${index + 1}`,
        title: item,
        url: item,
        type: deriveSourceType(item),
        relevanceScore: 0.5,
      };
    }

    const url = item.url ?? item.link ?? '';
    return {
      id: item.id ?? `source-${index + 1}`,
      title: item.title ?? url ?? `Source ${index + 1}`,
      url,
      type: deriveSourceType(url),
      date: item.date ?? item.published_date,
      authors: item.authors ?? [],
      relevanceScore: item.relevanceScore ?? item.relevance_score ?? 0.5,
      summary: item.summary ?? item.snippet ?? '',
    };
  });
};

const stripTrailingSources = (text: string): string => {
  if (!text) return text;
  const pattern = /\n+Sources(?:\s*\(\d+\))?:?[\s\S]*$/i;
  return text.replace(pattern, '\n').trimEnd();
};

const normalizeReportPayload = (
  payload: any,
  sourcePayload?: any,
): ResearchReport | null => {
  if (!payload) return null;

  const normalizedSources = normalizeSources(sourcePayload ?? payload?.sources);

  if (typeof payload === 'object' && payload.title && Array.isArray(payload.sections)) {
    return {
      ...payload,
      generatedAt: payload.generatedAt ? new Date(payload.generatedAt) : new Date(),
      sources: normalizedSources.length > 0 ? normalizedSources : payload.sources ?? [],
      metadata: {
        wordCount: payload.metadata?.wordCount ?? 0,
        sourcesCount:
          payload.metadata?.sourcesCount ?? (payload.sources?.length ?? normalizedSources.length),
        generationTime: payload.metadata?.generationTime ?? 0,
      },
    } as ResearchReport;
  }

  const rawText =
    typeof payload === 'string'
      ? payload
      : (() => {
          try {
            return JSON.stringify(payload, null, 2);
          } catch {
            return String(payload);
          }
        })();
  const text = normalizedSources.length > 0 ? stripTrailingSources(rawText) : rawText;

  const wordCount = text ? text.split(/\s+/).filter(Boolean).length : 0;

  return {
    title: 'Research Report',
    executiveSummary: text,
    sections: [],
    sources: normalizedSources,
    metadata: {
      wordCount,
      sourcesCount: normalizedSources.length,
      generationTime: 0,
    },
    generatedAt: new Date(),
  };
};

export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const {
    sessionId,
    enabled = true,
    onUpdate,
    onError,
    reconnect = true,
    reconnectAttempts = 5,
    reconnectDelay = 1000,
  } = options;

  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [error, setError] = useState<Error | null>(null);
  const [transport, setTransport] = useState<TransportMode>('websocket');
  const socketRef = useRef<WebSocket | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectCountRef = useRef(0);
  const sseReconnectCountRef = useRef(0);
  const [reconnectSignal, setReconnectSignal] = useState(0);
  const storeRef = useRef(useResearchStore.getState());
  const onUpdateRef = useRef(onUpdate);
  const onErrorRef = useRef(onError);
  const iterationMapRef = useRef<Record<number, string>>({});
  const iterationStartRef = useRef<Record<number, number>>({});

  useEffect(() => {
    const unsubscribe = useResearchStore.subscribe((state) => {
      storeRef.current = state;
    });
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    onUpdateRef.current = onUpdate;
  }, [onUpdate]);

  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  const sessionWsUrl = options.sessionUrl ?? null;

  useEffect(() => {
    reconnectCountRef.current = 0;
    sseReconnectCountRef.current = 0;
    iterationMapRef.current = {};
    iterationStartRef.current = {};
    setTransport('websocket');
  }, [sessionId]);

  const getMaxIterations = () => {
    const store = storeRef.current;
    return (
      store.activityState?.maxIterations ??
      store.currentSession?.metadata.maxIterations ??
      store.settings.maxIterations ??
      1
    );
  };

  const computeProgress = (iterationNumber: number, phase: string) => {
    const maxIterations = getMaxIterations();
    if (!maxIterations || maxIterations <= 0) {
      return 0;
    }
    const normalizedPhase = PHASE_PROGRESS[phase] ?? 0;
    const completed = Math.max(iterationNumber - 1, 0);
    const normalized = (completed + normalizedPhase) / maxIterations;
    return Math.min(100, Math.max(0, normalized * 100));
  };

  const computeElapsedSeconds = (timestamp: Date) => {
    const store = storeRef.current;
    const session = store.currentSession;
    if (!session?.startTime) {
      return store.activityState?.elapsed ?? 0;
    }
    const start =
      session.startTime instanceof Date
        ? session.startTime
        : new Date(session.startTime);
    return Math.max(0, Math.round((timestamp.getTime() - start.getTime()) / 1000));
  };

  const ensureIterationEntry = (iterationNumber: number, timestamp: Date, mode?: string) => {
    const normalizedNumber = iterationNumber > 0 ? iterationNumber : 1;
    const existing = iterationMapRef.current[normalizedNumber];
    const store = storeRef.current;
    const normalizedMode = mode === 'auto_finish' ? 'auto_finish' : 'normal';
    if (existing) {
      if (normalizedMode === 'auto_finish') {
        store.updateIteration(existing, { mode: normalizedMode });
      }
      return existing;
    }
    const iterationId = `${sessionId || 'session'}-iter-${normalizedNumber}`;
    iterationMapRef.current[normalizedNumber] = iterationId;
    const baseIteration: Iteration = {
      id: iterationId,
      index: normalizedNumber,
      mode: normalizedMode,
      status: 'pending',
      thought: {
        content: '',
        tokens: 0,
        latency: 0,
        timestamp,
      },
      action: {
        toolName: '',
        toolParams: {},
        success: false,
        duration: 0,
        timestamp,
      },
      observation: {
        content: '',
        timestamp,
      },
      duration: 0,
      timestamp,
    };
    store.addIteration(baseIteration);
    return iterationId;
  };

  const getIterationById = (iterationId: string): Iteration | undefined => {
    const store = storeRef.current;
    return store.iterations.find((iter) => iter.id === iterationId);
  };

  const publishActivityUpdate = (
    phase: keyof typeof PHASE_PROGRESS | 'starting' | 'failed',
    iterationNumber: number,
    activityMessage: string,
    updateId: string,
    latestMessage: string,
    timestamp: Date,
  ) => {
    const store = storeRef.current;
    store.updateActivityState({
      currentPhase: phase,
      currentIteration: Math.max(iterationNumber, 0),
      currentActivity: activityMessage,
      progress: computeProgress(iterationNumber, phase),
      elapsed: computeElapsedSeconds(timestamp),
      maxIterations: getMaxIterations(),
      latestUpdate: {
        id: updateId,
        message: latestMessage,
        timestamp,
      },
    });
  };

  const handleResearchUpdate = useCallback((update: ResearchUpdate) => {
    const store = storeRef.current;
    if (!store) return;

    const onUpdateCb = onUpdateRef.current;
    if (onUpdateCb) {
      onUpdateCb(update);
    }

    const timestamp = new Date();
    const resolveIterationNumber = () => {
      if (typeof update.iteration === 'number') {
        return update.iteration;
      }
      if (store.activityState?.currentIteration) {
        return store.activityState.currentIteration;
      }
      const lastIteration = store.iterations[store.iterations.length - 1];
      return lastIteration?.index ?? 1;
    };

    const publish = (
      phase: keyof typeof PHASE_PROGRESS | 'starting' | 'failed',
      iterationNumber: number,
      activityMessage: string,
      message?: string,
    ) => {
      publishActivityUpdate(
        phase,
        iterationNumber,
        activityMessage,
        update.id ?? `${phase}-${timestamp.getTime()}`,
        message ?? activityMessage,
        timestamp,
      );
    };

    switch (update.type) {
      case 'session_start':
        iterationMapRef.current = {};
        iterationStartRef.current = {};
        publish('starting', 0, 'Session started', update.message ?? 'Session started');
        break;

      case 'iteration_start': {
        if (update.iteration !== undefined) {
          const mode = update.data?.mode as string | undefined;
          const iterationId = ensureIterationEntry(update.iteration, timestamp, mode);
          iterationStartRef.current[update.iteration] = timestamp.getTime();
          store.updateIteration(iterationId, {
            status: 'thinking',
            timestamp,
          });
          const iterationLabel =
            mode === 'auto_finish'
              ? 'Auto-finish final report'
              : `Starting iteration ${update.iteration}`;
          publish(
            'thinking',
            update.iteration,
            iterationLabel,
            update.message ?? iterationLabel,
          );
        }
        break;
      }

      case 'thought':
      case 'thought_generated': {
        const iterationNumber = resolveIterationNumber();
        const iterationId = ensureIterationEntry(iterationNumber, timestamp);
        const rawThought: string | undefined = update.data?.thought;
        const normalizedThought =
          rawThought && rawThought.trim().length > 0
            ? rawThought
            : update.message ?? '';
        store.updateIteration(iterationId, {
          status: 'thinking',
          thought: {
            content: normalizedThought,
            tokens: update.data?.tokens_used ?? 0,
            latency: Math.round(update.data?.latency_ms ?? 0),
            timestamp,
          },
          timestamp,
        });
        publish(
          'thinking',
          iterationNumber,
          'Agent is reasoning...',
          update.message ?? 'Agent is reasoning...',
        );
        break;
      }

      case 'action':
      case 'action_executing': {
        const iterationNumber = resolveIterationNumber();
        const iterationId = ensureIterationEntry(iterationNumber, timestamp);
        const currentIteration = getIterationById(iterationId);
        const toolName = update.data?.tool ?? update.message ?? 'action';
        store.updateIteration(iterationId, {
          status: 'acting',
          action: {
            ...(currentIteration?.action ?? {
              toolName: '',
              toolParams: {},
              success: true,
              duration: 0,
              timestamp,
            }),
            toolName,
            toolParams: update.data?.parameters ?? {},
            success: true,
            timestamp,
          },
          timestamp,
        });
        publish(
          'acting',
          iterationNumber,
          `Selecting ${toolName}`,
          update.message ?? `Selecting ${toolName}`,
        );
        break;
      }

      case 'tool_execution':
      case 'action_complete': {
        const iterationNumber = resolveIterationNumber();
        const iterationId = ensureIterationEntry(iterationNumber, timestamp);
        const currentIteration = getIterationById(iterationId);
        const toolName = update.data?.tool ?? currentIteration?.action.toolName ?? 'tool';
        const summary = update.data?.result_summary ?? update.message ?? 'Tool execution complete';
        const durationMs = Math.round(
          update.data?.duration_ms ?? currentIteration?.action.duration ?? 0,
        );

        store.updateIteration(iterationId, {
          status: 'observing',
          action: {
            ...(currentIteration?.action ?? {
              toolName,
              toolParams: {},
              success: true,
              duration: durationMs,
              timestamp,
            }),
            toolName,
            success: update.data?.success ?? true,
            duration: durationMs,
            result: {
              tool: toolName,
              summary,
              data: update.data,
              count:
                update.data?.results?.length ??
                update.data?.result_count ??
                update.data?.total_found ??
                0,
            },
            timestamp,
          },
          timestamp,
        });

        store.addToolOutput({
          id: `${iterationId}-tool-${timestamp.getTime()}`,
          tool: toolName,
          resultsCount:
            update.data?.results?.length ??
            update.data?.result_count ??
            0,
          summaries: [
            {
              title: toolName,
              summary,
              relevance: 0,
            },
          ],
          timestamp,
        });

        publish(
          'observing',
          iterationNumber,
          `Analyzing ${toolName} results`,
          summary,
        );
        break;
      }

      case 'observation':
      case 'observation_generated': {
        const iterationNumber = resolveIterationNumber();
        const iterationId = ensureIterationEntry(iterationNumber, timestamp);
        const observationText = update.data?.observation ?? update.message ?? 'Observation recorded';
        const startTime = iterationStartRef.current[iterationNumber];
        const duration = startTime ? timestamp.getTime() - startTime : undefined;
        store.updateIteration(iterationId, {
          observation: {
            content: observationText,
            timestamp,
          },
          status: 'complete',
          duration: duration ?? getIterationById(iterationId)?.duration ?? 0,
          timestamp,
        });
        publish('complete', iterationNumber, 'Observation recorded', observationText);
        break;
      }

      case 'evaluation_complete':
        publish(
          'evaluating',
          resolveIterationNumber(),
          update.message ?? 'Running evaluation',
          update.message ?? 'Running evaluation',
        );
        break;

      case 'iteration_complete':
        if (update.data?.iteration) {
          const iterationId = ensureIterationEntry(update.data.iteration, timestamp);
          store.updateIteration(iterationId, {
            status: 'complete',
            timestamp,
          });
        }
        break;

      case 'report_chunk':
        if (update.data?.chunk) {
          store.appendReportChunk(update.data.chunk);
        }
        break;

      case 'finish': {
        const iterationNumber =
          typeof update.iteration === 'number'
            ? update.iteration
            : (update.data?.iteration as number) ?? resolveIterationNumber() + 1;
        const iterationId = ensureIterationEntry(iterationNumber, timestamp);
        const finishSummary = update.data?.message ?? update.message ?? 'Final report generated';
        const observationText =
          update.data?.summary ??
          update.data?.report_preview ??
          'Final report synthesized from collected evidence.';

        store.updateIteration(iterationId, {
          status: 'complete',
          action: {
            toolName: 'finish',
            toolParams: {},
            success: true,
            duration: 0,
            timestamp,
            result: {
              tool: 'finish',
              summary: finishSummary,
              data: update.data,
              count: 1,
            },
          },
          observation: {
            content: observationText,
            timestamp,
          },
          timestamp,
        });

        publish('complete', iterationNumber, 'Finalizing report', finishSummary);

        if (update.data?.report) {
          const normalizedReport = normalizeReportPayload(update.data.report, update.data?.sources);
          if (normalizedReport) {
            store.setReport(normalizedReport);
          }
        }
        break;
      }

      case 'report_complete': {
        if (update.data?.report) {
          const normalizedReport = normalizeReportPayload(update.data.report, update.data?.sources);
          if (normalizedReport) {
            store.setReport(normalizedReport);
          }
        }
        break;
      }

      case 'completion':
      case 'session_complete': {
        const completionPayload = update.data?.session ?? update.data?.result;

        // Extract report
        if (completionPayload?.report) {
          const normalizedReport = normalizeReportPayload(
            completionPayload.report,
            completionPayload.sources,
          );
          if (normalizedReport) {
            store.setReport(normalizedReport);
          }
        }

        // Extract metrics
        if (completionPayload?.metrics) {
          const metricsData = completionPayload.metrics;

          // Calculate tool success rate
          let toolSuccesses = 0;
          let toolTotal = 0;
          if (metricsData.tool_metrics) {
            Object.values(metricsData.tool_metrics).forEach((metrics: any) => {
              toolSuccesses += metrics.success_count || 0;
              toolTotal += metrics.execution_count || 0;
            });
          }

          // Build current run metrics
          const currentMetrics = {
            iterationLatencyAvg: metricsData.avg_iteration_duration * 1000, // s to ms
            iterationLatencies: metricsData.iterations?.map((i: any) => i.duration * 1000) || [],
            toolExecutionTimes: {} as Record<string, number>,
            endToEndSeconds: metricsData.total_duration_seconds,
            totalTokens: metricsData.total_tokens_used,
            totalCostUsd: metricsData.total_cost || 0,
            iterationsToCompletion: metricsData.total_iterations || 0,
            toolSuccessRate: toolTotal > 0 ? toolSuccesses / toolTotal : 0,
            evaluation: completionPayload.evaluation || {
              relevance: 0,
              accuracy: 0,
              completeness: 0,
              sourceQuality: 0,
              strengths: [],
              weaknesses: [],
              recommendations: [],
            },
          };

          // Extract tool times
          if (metricsData.tool_metrics) {
            Object.entries(metricsData.tool_metrics).forEach(([tool, metrics]: [string, any]) => {
              currentMetrics.toolExecutionTimes[tool] = metrics.avg_duration_seconds * 1000;
            });
          }

          // Set current metrics
          store.setMetrics({
            current: currentMetrics,
            inception: store.metrics.inception, // Keep existing
          });

          // Fetch historical metrics
          store.fetchMetricsSummary();
        }

        if (completionPayload?.id) {
          store.setCurrentSession(completionPayload);
        }
        store.setResearching(false);
        publish(
          'complete',
          getMaxIterations(),
          'Research completed',
          update.message ?? 'Research completed',
        );
        const latestSession = useResearchStore.getState().currentSession;
        if (latestSession) {
          store.addHistoryItem({
            id: latestSession.id,
            query: latestSession.query,
            status: 'completed',
            createdAt: latestSession.startTime,
            duration: latestSession.metadata.duration,
          });
        }
        break;
      }

      case 'progress_update':
        store.updateActivityState({
          currentPhase: update.data?.status ?? 'running',
          currentActivity: update.message ?? 'Processing...',
          progress: update.data?.progress ?? store.activityState?.progress ?? 0,
          latestUpdate: {
            id: update.id,
            message: update.message ?? 'Progress update',
            timestamp,
          },
        });
        break;

      case 'session_failed':
        store.setResearching(false);
        publish(
          'failed',
          resolveIterationNumber(),
          update.message ?? 'Session failed',
          update.message ?? 'Session failed',
        );
        store.setError(update.data?.error || 'Research session failed');
        break;

      case 'error': {
        const errorMessage = update.data?.error || update.message || 'Unknown error';
        store.setError(errorMessage);
        store.setResearching(false);
        const onErrorCb = onErrorRef.current;
        if (onErrorCb) {
          onErrorCb(new Error(errorMessage));
        }
        break;
      }
    }
  }, []);

  const buildWebSocketUrl = useCallback((targetSessionId: string, explicitUrl?: string) => {
    if (explicitUrl) {
      if (explicitUrl.startsWith('ws')) {
        return explicitUrl;
      }
      if (explicitUrl.startsWith('/')) {
        const base = API_ENDPOINTS.WS_URL || API_ENDPOINTS.BASE_URL;
        const normalizedBase = base.startsWith('http')
          ? base.replace(/^http/, 'ws')
          : base;
        const trimmed = normalizedBase.endsWith('/')
          ? normalizedBase.slice(0, -1)
          : normalizedBase;
        return `${trimmed}${explicitUrl}`;
      }
    }
    const base = API_ENDPOINTS.WS_URL || API_ENDPOINTS.BASE_URL;
    const normalizedBase = base.startsWith('http')
      ? base.replace(/^http/, 'ws')
      : base;
    const trimmed = normalizedBase.endsWith('/')
      ? normalizedBase.slice(0, -1)
      : normalizedBase;
    return `${trimmed}/ws/${targetSessionId}`;
  }, []);

  const normalizeServerEvent = useCallback(
    (payload: any): ResearchUpdate | null => {
      const sessionIdFromPayload = payload.session_id ?? payload.sessionId;
      const type = payload.type as WebSocketEventType | undefined;

      if (!sessionIdFromPayload || !type) {
        return null;
      }

      const timestamp = payload.timestamp
        ? new Date(payload.timestamp)
        : new Date();

      const data = payload.data ?? payload.result ?? payload;

      return {
        id: payload.id ?? `${type}-${timestamp.getTime()}`,
        type,
        sessionId: sessionIdFromPayload,
        iteration: data?.iteration ?? payload.iteration,
        phase: data?.currentPhase,
        message: payload.message ?? data?.message ?? type,
        data,
        timestamp,
      };
    },
    []
  );

  const buildEventStreamUrl = useCallback(
    (targetSessionId: string, explicitUrl?: string) => {
      const normalizeBase = (base: string) => {
        if (!base) {
          return '';
        }
        return base.endsWith('/') ? base.slice(0, -1) : base;
      };

      const appendStream = (url: string) =>
        url.endsWith('/stream') ? url : `${url}/stream`;

      const fallbackOrigin =
        typeof window !== 'undefined' ? window.location.origin : '';
      const resolvedBase = API_ENDPOINTS.BASE_URL || fallbackOrigin;
      const baseHttp = normalizeBase(resolvedBase);

      if (explicitUrl) {
        if (explicitUrl.startsWith('ws')) {
          const httpUrl = explicitUrl.replace(/^ws/i, 'http');
          return appendStream(httpUrl);
        }
        if (explicitUrl.startsWith('/')) {
          return appendStream(`${baseHttp}${explicitUrl}`);
        }
        return appendStream(explicitUrl);
      }

      return appendStream(`${baseHttp}/ws/${targetSessionId}`);
    },
    []
  );

  useEffect(() => {
    if (transport !== 'websocket') {
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
      return;
    }

    if (!sessionId || !enabled) {
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      setStatus('disconnected');
      return;
    }

    setStatus('connecting');
    setError(null);

    const wsUrl = buildWebSocketUrl(sessionId, sessionWsUrl ?? undefined);
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      setStatus('connected');
      setError(null);
      reconnectCountRef.current = 0;
    };

    socket.onerror = (err) => {
      const wsError =
        err instanceof Event
          ? new Error('WebSocket connection error')
          : (err as Error);
      setStatus('error');
      setError(wsError);
      const onErrorCb = onErrorRef.current;
      if (onErrorCb) {
        onErrorCb(wsError);
      }
    };

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        const normalized = normalizeServerEvent(payload);
        if (normalized) {
          handleResearchUpdate(normalized);
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message', err);
      }
    };

    socket.onclose = () => {
      if (socketRef.current === socket) {
        socketRef.current = null;
      }
      setStatus('disconnected');

      if (
        enabled &&
        reconnect &&
        reconnectCountRef.current < reconnectAttempts
      ) {
        reconnectCountRef.current += 1;
        const delay = reconnectDelay * reconnectCountRef.current;
        reconnectTimerRef.current = setTimeout(() => {
          setReconnectSignal((signal) => signal + 1);
        }, delay);
      } else if (enabled && reconnect) {
        sseReconnectCountRef.current = 0;
        setTransport('sse');
      }
    };

    return () => {
      socket.onopen = null;
      socket.onclose = null;
      socket.onerror = null;
      socket.onmessage = null;
      if (
        socket.readyState === WebSocket.OPEN ||
        socket.readyState === WebSocket.CONNECTING
      ) {
        socket.close();
      }
      if (socketRef.current === socket) {
        socketRef.current = null;
      }
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
    };
  }, [
    sessionId,
    enabled,
    reconnect,
    reconnectAttempts,
    reconnectDelay,
    reconnectSignal,
    handleResearchUpdate,
    buildWebSocketUrl,
    normalizeServerEvent,
    sessionWsUrl,
    transport,
  ]);

  useEffect(() => {
    if (transport !== 'sse') {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      return;
    }

    if (typeof EventSource === 'undefined') {
      setTransport('websocket');
      return;
    }

    if (!sessionId || !enabled) {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      setStatus('disconnected');
      return;
    }

    setStatus('connecting');
    setError(null);

    const streamUrl = buildEventStreamUrl(sessionId, sessionWsUrl ?? undefined);
    const eventSource = new EventSource(streamUrl);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setStatus('connected');
      setError(null);
      sseReconnectCountRef.current = 0;
    };

    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        const normalized = normalizeServerEvent(payload);
        if (normalized) {
          handleResearchUpdate(normalized);
        }
      } catch (err) {
        console.error('Failed to parse SSE message', err);
      }
    };

    eventSource.onerror = () => {
      const sseError = new Error('EventSource connection error');
      setError(sseError);
      setStatus('error');
      const onErrorCb = onErrorRef.current;
      if (onErrorCb) {
        onErrorCb(sseError);
      }
      eventSource.close();

      if (!enabled || !reconnect) {
        setTransport('websocket');
        return;
      }

      sseReconnectCountRef.current += 1;
      const sseRetryLimit = Math.max(
        1,
        Math.min(reconnectAttempts, SSE_MAX_RETRIES),
      );

      if (sseReconnectCountRef.current >= sseRetryLimit) {
        sseReconnectCountRef.current = 0;
        setTransport('websocket');
        setReconnectSignal((signal) => signal + 1);
        return;
      }

      const delay = reconnectDelay * sseReconnectCountRef.current;
      reconnectTimerRef.current = setTimeout(() => {
        setReconnectSignal((signal) => signal + 1);
      }, delay);
    };

    return () => {
      eventSource.onopen = null;
      eventSource.onmessage = null;
      eventSource.onerror = null;
      eventSource.close();
      if (eventSourceRef.current === eventSource) {
        eventSourceRef.current = null;
      }
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
    };
  }, [
    transport,
    sessionId,
    enabled,
    reconnect,
    reconnectDelay,
    reconnectAttempts,
    reconnectSignal,
    handleResearchUpdate,
    normalizeServerEvent,
    buildEventStreamUrl,
    sessionWsUrl,
  ]);

  const connect = useCallback(() => {
    if (!sessionId) {
      return;
    }
    setTransport('websocket');
    reconnectCountRef.current = 0;
    sseReconnectCountRef.current = 0;
    setReconnectSignal((signal) => signal + 1);
  }, [sessionId]);

  const disconnect = useCallback(() => {
    reconnectCountRef.current = reconnectAttempts;
    sseReconnectCountRef.current = reconnectAttempts;
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setTransport('websocket');
    setStatus('disconnected');
  }, [reconnectAttempts]);

  const sendMessage = useCallback((event: string, data: any) => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket is not connected. Message not sent.');
      return;
    }

    const payload = JSON.stringify({ type: event, data });
    socketRef.current.send(payload);
  }, []);

  return {
    status,
    isConnected: status === 'connected',
    error,
    connect,
    disconnect,
    sendMessage,
  };
}
