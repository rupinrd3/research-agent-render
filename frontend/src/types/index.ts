/**
 * Core TypeScript types and interfaces for the Agentic Research Lab frontend.
 * These types match the backend API responses and WebSocket events.
 */

// ============================================================================
// Research Session Types
// ============================================================================

/**
 * Represents a complete research session
 */
export interface ResearchSession {
  id: string;
  query: string;
  status: SessionStatus;
  startTime: Date;
  endTime?: Date;
  websocketUrl?: string;
  iterations: Iteration[];
  finalReport?: ResearchReport;
  evaluation?: EndToEndEvaluation;
  metadata: SessionMetadata;
}

export type SessionStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

/**
 * Metadata about the research session
 */
export interface SessionMetadata {
  duration?: number; // in seconds
  totalTokens: number;
  totalCost: number;
  llmProvider: string;
  llmModel: string;
  iterationCount: number;
  toolCallsCount: number;
  maxIterations?: number;
}

// ============================================================================
// ReAct Iteration Types
// ============================================================================

/**
 * A single ReAct iteration (Thought -> Action -> Observation)
 */
export interface Iteration {
  id: string;
  index: number;
  mode?: 'normal' | 'auto_finish';
  status: IterationStatus;
  thought: Thought;
  action: Action;
  observation: Observation;
  evaluation?: PerStepEvaluation;
  duration: number; // milliseconds
  timestamp: Date;
}

export type IterationStatus = 'pending' | 'thinking' | 'acting' | 'observing' | 'evaluating' | 'complete' | 'failed';

/**
 * The "Thought" phase - Agent's reasoning
 */
export interface Thought {
  content: string;
  tokens: number;
  latency: number; // milliseconds
  timestamp: Date;
}

/**
 * The "Action" phase - Tool selection and execution
 */
export interface Action {
  toolName: string;
  toolParams: Record<string, any>;
  success: boolean;
  result?: ToolResult;
  error?: string;
  duration: number; // milliseconds
  timestamp: Date;
}

/**
 * Result from a tool execution
 */
export interface ToolResult {
  tool: string;
  data: any;
  summary: string;
  count: number;
  sources?: Source[];
}

/**
 * The "Observation" phase - Agent's interpretation of the action result
 */
export interface Observation {
  content: string;
  timestamp: Date;
}

// ============================================================================
// Evaluation Types
// ============================================================================

/**
 * Per-step evaluation (after each iteration)
 * Uses 0-10 scale for all scores
 */
export interface PerStepEvaluation {
  toolSelectionScore: number; // 0-10
  toolExecutionScore: number; // 0-10
  progressScore: number; // 0-10
  informationGain: number; // 0-10
  reasoning?: string;
}

/**
 * End-to-end evaluation (after research complete)
 * Uses 0-1 scale for all scores
 */
export interface EndToEndEvaluation {
  relevance: number; // 0-1
  accuracy: number; // 0-1
  completeness: number; // 0-1
  sourceQuality: number; // 0-1
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
}

// ============================================================================
// Research Report Types
// ============================================================================

/**
 * The final research report
 */
export interface ResearchReport {
  title: string;
  executiveSummary: string;
  sections: ReportSection[];
  sources: Source[];
  metadata: ReportMetadata;
  generatedAt: Date;
}

/**
 * A section within the research report
 */
export interface ReportSection {
  title: string;
  content: string;
  order: number;
}

/**
 * A source cited in the report
 */
export interface Source {
  id: string;
  title: string;
  url: string;
  type: SourceType;
  date?: string;
  authors?: string[];
  relevanceScore: number;
  summary?: string;
}

export type SourceType = 'web' | 'arxiv' | 'github' | 'pdf';

/**
 * Metadata about the report
 */
export interface ReportMetadata {
  wordCount: number;
  sourcesCount: number;
  generationTime: number; // milliseconds
}

// ============================================================================
// WebSocket Event Types
// ============================================================================

/**
 * Base interface for all WebSocket events
 */
export interface WebSocketEvent {
  type: WebSocketEventType;
  sessionId: string;
  timestamp: Date;
  data: any;
}

export type WebSocketEventType =
  | 'session_start'
  | 'iteration_start'
  | 'thought_generated'
  | 'thought'
  | 'action_executing'
  | 'action'
  | 'action_complete'
  | 'tool_execution'
  | 'observation_generated'
  | 'observation'
  | 'evaluation_complete'
  | 'iteration_complete'
  | 'report_chunk'
  | 'report_complete'
  | 'finish'
  | 'session_complete'
  | 'completion'
  | 'session_failed'
  | 'progress_update'
  | 'error';

/**
 * Research update event (sent via WebSocket)
 */
export interface ResearchUpdate {
  id: string;
  type: WebSocketEventType;
  sessionId: string;
  iteration?: number;
  phase?: IterationStatus;
  message?: string;
  data?: any;
  timestamp: Date;
}

// ============================================================================
// UI State Types
// ============================================================================

/**
 * Current activity state (for the center panel)
 */
export interface ActivityState {
  currentPhase: string;
  currentIteration: number;
  currentActivity: string;
  progress: number; // 0-100
  elapsed: number; // seconds
  estimatedTimeRemaining: number; // seconds
  maxIterations: number;
  latestUpdate: {
    id: string;
    message: string;
    timestamp: Date;
  };
}

/**
 * Tool output summary (for the center panel)
 */
export interface ToolOutputSummary {
  id: string;
  tool: string;
  resultsCount: number;
  summaries: {
    title: string;
    summary: string;
    relevance: number;
    url?: string;
  }[];
  timestamp: Date;
}

// ============================================================================
// API Request/Response Types
// ============================================================================

/**
 * Request to start a new research session
 */
export interface StartResearchRequest {
  query: string;
  config?: {
    llm?: {
      provider?: string;
      model?: string;
      temperature?: number;
    };
    research?: {
      max_iterations?: number;
    };
  };
}

/**
 * Response from starting a research session
 */
export interface StartResearchResponse {
  sessionId: string;
  message: string;
}

/**
 * Settings configuration
 */
export interface Settings {
  llmProvider: 'openai' | 'gemini' | 'openrouter';
  llmModel: string;
  temperature: number;
  maxIterations: number;
  apiKeys: {
    openai?: string;
    gemini?: string;
    openrouter?: string;
  };
}

/**
 * History item for past research sessions
 */
export interface HistoryItem {
  id: string;
  query: string;
  status: SessionStatus;
  createdAt: Date;
  duration?: number;
  overallScore?: number;
}

// ============================================================================
// Utility Types
// ============================================================================

/**
 * Loading state
 */
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

/**
 * API error response
 */
export interface APIError {
  message: string;
  code?: string;
  details?: any;
}

/**
 * Export format options
 */
export type ExportFormat = 'markdown' | 'pdf' | 'word' | 'html' | 'json';

/**
 * Example query
 */
export interface ExampleQuery {
  id: string;
  title: string;
  query: string;
  category: string;
  estimatedDuration?: string;
}

// ============================================================================
// Metrics Types
// ============================================================================

/**
 * Current run metrics
 */
export interface CurrentRunMetrics {
  // Latency
  iterationLatencyAvg: number; // ms
  iterationLatencies: number[]; // ms array
  toolExecutionTimes: Record<string, number>; // tool -> avg ms
  endToEndSeconds: number;

  // Token & Cost
  totalTokens: number;
  totalCostUsd: number;

  // Agent Behavior
  iterationsToCompletion: number;
  toolSuccessRate: number; // 0-1

  // Evaluation
  evaluation: EndToEndEvaluation;
}

/**
 * Historical aggregate metrics
 */
export interface InceptionMetrics {
  totalSessions: number;
  completedSessions: number;

  // Latency (medians)
  iterationLatencyMedian: number; // ms
  endToEndMedian: number; // seconds
  tools: Record<string, number>; // tool -> median ms

  // Token & Cost (averages)
  avgTokens: number;
  avgCostUsd: number;

  // Agent Behavior
  avgIterations: number;
  toolSuccessRate: number; // 0-1

  // Reliability
  sessionSuccessRate: number; // 0-1
  providerFailoverRate: number; // 0-1

  // Quality (averages, 0-1)
  relevanceAvg: number;
  accuracyAvg: number;
  completenessAvg: number;
  sourceQualityAvg: number;
}

/**
 * Metrics state
 */
export interface MetricsState {
  current: CurrentRunMetrics | null;
  inception: InceptionMetrics | null;
}
