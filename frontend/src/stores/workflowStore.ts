/**
 * Workflow Visualization State Store
 * Manages the state for the horizontal workflow chart showing research agent's ReAct pattern
 */

import { create } from 'zustand';

// ==================== TYPE DEFINITIONS ====================

export type NodeId = 'start' | 'think' | 'operate' | 'reflect' | 'evaluator' | 'finish';
export type NodeStatus = 'idle' | 'active' | 'completed' | 'error' | 'skipped';
export type EdgeId =
  | 'start->think'
  | 'think->operate'
  | 'operate->reflect'
  | 'reflect->evaluator'
  | 'evaluator->finish'
  | 'reflect->think';
export type EdgeStatus = 'idle' | 'active' | 'completed' | 'disabled';

export interface NodeState {
  status: NodeStatus;
  visitCount: number;
  currentVisitIteration: number;
  lastCompletedAt: string | null;
  showPulse: boolean;
  showGlow: boolean;
  errorMessage?: string;
  iterationBadge?: {
    show: boolean;
    count: number;
  };
  metadata?: {
    thought?: string;
    selectedTool?: string;
    tool?: string;
    provider?: string;
    duration?: number;
    startTime?: string;
    resultCount?: number;
    decision?: 'iterate' | 'finish' | 'pending';
    guardFeedback?: string;
    reportLength?: number;
    sourceCount?: number;
    observation?: string;
    evaluationScores?: {
      relevance?: number;
      accuracy?: number;
      completeness?: number;
      source_quality?: number;
    };
    evaluationDuration?: number;
  };
}

export interface EdgeState {
  status: EdgeStatus;
  showFlowAnimation: boolean;
  showPulse: boolean;
  lastTransitionAt: string | null;
  transitionCount: number;
  style: {
    strokeWidth: number;
    opacity: number;
    dashArray?: string;
  };
}

export interface ActionMetadata {
  eventType: string;
  iteration: number;
  nodeId: string;
  timestamp: string;
  data: Record<string, any>;
  live?: {
    startTime: number;
    expectedDuration?: number;
  };
}

export interface SessionStats {
  toolsExecuted: number;
  resultsFound: number;
  totalCost: number;
  totalTokens: number;
  sessionDuration: number;
  startTime: string;
  endTime?: string;
}

// Base event interface
interface BaseWorkflowEvent {
  timestamp: string;
  iteration?: number;
  nodeId?: string;
  edgeId?: string;
}

// Session lifecycle events
export interface SessionStartEvent extends BaseWorkflowEvent {
  type: 'session_start';
  data: {
    session_id: string;
    query: string;
    max_iterations: number;
  };
}

export interface SessionCompleteEvent extends BaseWorkflowEvent {
  type: 'session_complete';
  data: {
    status: 'completed' | 'incomplete' | 'failed';
    iterations: number;
    duration_seconds: number;
    total_tokens: number;
    total_cost_usd: number;
  };
}

export interface SessionFailedEvent extends BaseWorkflowEvent {
  type: 'session_failed';
  data: {
    error: string;
  };
}

// Iteration lifecycle events
export interface IterationStartEvent extends BaseWorkflowEvent {
  type: 'iteration_start';
  iteration: number;
  data: {
    iteration: number;
    mode?: 'normal' | 'auto_finish';
    timestamp?: string;
    message?: string;
  };
}

// Stage progression events
export interface ThoughtEvent extends BaseWorkflowEvent {
  type: 'thought';
  iteration: number;
  data: {
    thought: string;
    tokens_used?: number;
    provider?: string;
    latency_ms?: number;
  };
}

export interface ActionEvent extends BaseWorkflowEvent {
  type: 'action';
  iteration: number;
  data: {
    tool: string;
    parameters?: Record<string, any>;
  };
}

export interface ToolExecutionEvent extends BaseWorkflowEvent {
  type: 'tool_execution';
  iteration: number;
  data: {
    tool: string;
    duration_ms: number;
    success: boolean;
    result_summary: string;
    provider?: string;
    result_count?: number;
  };
}

export interface ObservationEvent extends BaseWorkflowEvent {
  type: 'observation';
  iteration: number;
  data: {
    observation: string;
  };
}

export interface FinishGuardEvent extends BaseWorkflowEvent {
  type: 'finish_guard';
  iteration: number;
  data: {
    approved: boolean;
    feedback: string;
    hint?: string;
  };
}

export interface FinishEvent extends BaseWorkflowEvent {
  type: 'finish';
  iteration: number;
  data: {
    report: string;
    sources?: string[];
    report_length: number;
    num_sources: number;
  };
}

export interface EvaluatorStartEvent extends BaseWorkflowEvent {
  type: 'evaluator_start';
  data: {
    message?: string;
  };
}

export interface EvaluatorCompleteEvent extends BaseWorkflowEvent {
  type: 'evaluator_complete';
  data: {
    message?: string;
    duration_seconds?: number;
    scores?: {
      relevance?: number;
      accuracy?: number;
      completeness?: number;
      source_quality?: number;
    };
  };
}

// Control events
export interface ToolBlockedEvent extends BaseWorkflowEvent {
  type: 'tool_blocked';
  iteration: number;
  data: {
    tool: string;
    reason: string;
  };
}

export interface ErrorEvent extends BaseWorkflowEvent {
  type: 'error';
  iteration?: number;
  data: {
    error: string;
    node?: string;
  };
}

// Discriminated union of all event types
export type WorkflowEvent =
  | SessionStartEvent
  | SessionCompleteEvent
  | SessionFailedEvent
  | IterationStartEvent
  | ThoughtEvent
  | ActionEvent
  | ToolExecutionEvent
  | ObservationEvent
  | FinishGuardEvent
  | FinishEvent
  | EvaluatorStartEvent
  | EvaluatorCompleteEvent
  | ToolBlockedEvent
  | ErrorEvent;

export interface WorkflowState {
  sessionId: string;
  query: string;
  iteration: {
    current: number;
    max: number;
    totalCompleted: number;
  };
  loopingFromEvaluate: boolean;
  nodes: {
    start: NodeState;
    think: NodeState;
    operate: NodeState;
    reflect: NodeState;
    evaluator: NodeState;
    finish: NodeState;
  };
  edges: Record<EdgeId, EdgeState>;
  currentAction: ActionMetadata | null;
  stats: SessionStats;
  eventHistory: WorkflowEvent[];
  pendingFinish?: {
    reportLength?: number;
    sourceCount?: number;
  };
}

// ==================== INITIAL STATE ====================

const initialNodeState: NodeState = {
  status: 'idle',
  visitCount: 0,
  currentVisitIteration: 0,
  lastCompletedAt: null,
  showPulse: false,
  showGlow: false,
  iterationBadge: { show: false, count: 0 },
  metadata: {}
};

const initialEdgeState: EdgeState = {
  status: 'idle',
  showFlowAnimation: false,
  showPulse: false,
  lastTransitionAt: null,
  transitionCount: 0,
  style: {
    strokeWidth: 3,
    opacity: 0.3
  }
};

const EDGE_IDS: EdgeId[] = [
  'start->think',
  'think->operate',
  'operate->reflect',
  'reflect->evaluator',
  'evaluator->finish',
  'reflect->think'
];

const setActiveEdgeFlow = (
  edges: Record<EdgeId, EdgeState>,
  targetEdge?: EdgeId
) => {
  EDGE_IDS.forEach((edgeId) => {
    const edge = edges[edgeId];
    if (!edge) return;
    edges[edgeId] = {
      ...edge,
      showFlowAnimation: targetEdge === edgeId
    };
  });
};


const initialState: WorkflowState = {
  sessionId: '',
  query: '',
  loopingFromEvaluate: false,
  iteration: { current: 0, max: 10, totalCompleted: 0 },
  nodes: {
    start: { ...initialNodeState },
    think: { ...initialNodeState },
    operate: { ...initialNodeState },
    reflect: { ...initialNodeState },
    evaluator: { ...initialNodeState },
    finish: { ...initialNodeState }
  },
  edges: {
    'start->think': { ...initialEdgeState },
    'think->operate': { ...initialEdgeState },
    'operate->reflect': { ...initialEdgeState },
    'reflect->evaluator': { ...initialEdgeState },
    'evaluator->finish': { ...initialEdgeState },
    'reflect->think': { ...initialEdgeState }
  },
  currentAction: null,
  stats: {
    toolsExecuted: 0,
    resultsFound: 0,
    totalCost: 0,
    totalTokens: 0,
    sessionDuration: 0,
    startTime: new Date().toISOString()
  },
  eventHistory: [],
  pendingFinish: undefined
};

// ==================== STATE REDUCER ====================

export function workflowReducer(
  state: WorkflowState,
  event: WorkflowEvent
): WorkflowState {
  const newState: WorkflowState = {
    ...state,
    nodes: { ...state.nodes },
    edges: { ...state.edges },
    stats: { ...state.stats },
    eventHistory: [...state.eventHistory],
    pendingFinish: state.pendingFinish
  };

  switch (event.type) {
    case 'session_start':
      // Reset entire state for new session
      return {
        sessionId: event.data.session_id || '',
        query: event.data.query || '',
        loopingFromEvaluate: false,
        iteration: {
          current: 0,
          max: event.data.max_iterations || 10,
          totalCompleted: 0
        },
        nodes: {
          start: { ...initialNodeState },
          think: { ...initialNodeState },
          operate: { ...initialNodeState },
          reflect: { ...initialNodeState },
          evaluator: { ...initialNodeState },
          finish: { ...initialNodeState }
        },
        edges: {
          'start->think': { ...initialEdgeState },
          'think->operate': { ...initialEdgeState },
          'operate->reflect': { ...initialEdgeState },
          'reflect->evaluator': { ...initialEdgeState },
          'evaluator->finish': { ...initialEdgeState },
          'reflect->think': { ...initialEdgeState }
        },
        currentAction: null,
        stats: {
          toolsExecuted: 0,
          resultsFound: 0,
          totalCost: 0,
          totalTokens: 0,
          sessionDuration: 0,
          startTime: event.timestamp
        },
        pendingFinish: undefined,
        eventHistory: [event]
      };

    case 'iteration_start': {
      const requestedIteration = event.data?.iteration || state.iteration.current + 1;
      const iterationNumber = Math.max(1, requestedIteration);
      const mode = event.data?.mode || 'normal';
      const timestamp = new Date().toISOString();

      if (state.nodes.reflect.status === 'active') {
        newState.nodes.reflect = {
          ...state.nodes.reflect,
          status: 'completed',
          showPulse: false,
          lastCompletedAt: timestamp,
          metadata: {
            ...state.nodes.reflect.metadata,
            decision: state.nodes.reflect.metadata?.decision || 'iterate'
          }
        };
      }

      if (state.edges['operate->reflect'].status === 'active') {
        newState.edges['operate->reflect'] = {
          ...state.edges['operate->reflect'],
          status: 'completed',
          showFlowAnimation: false
        };
      }

      newState.iteration = {
        ...state.iteration,
        current: iterationNumber
      };
      newState.loopingFromEvaluate = false;

      if (mode === 'auto_finish') {
        newState.nodes.reflect = {
          ...state.nodes.reflect,
          status: 'active',
          showPulse: true
        };
        setActiveEdgeFlow(newState.edges, undefined);
        newState.eventHistory = [...state.eventHistory, event];
        return newState;
      }

      const downstreamNodes: NodeId[] = ['operate', 'reflect', 'evaluator', 'finish'];
      downstreamNodes.forEach((nodeId) => {
        newState.nodes[nodeId] = {
          ...state.nodes[nodeId],
          status: 'idle',
          showPulse: false,
          errorMessage: undefined,
          metadata: {}
        };
      });

      const downstreamEdges: EdgeId[] = [
        'think->operate',
        'operate->reflect',
        'reflect->evaluator',
        'evaluator->finish',
        'reflect->think'
      ];
      downstreamEdges.forEach((edgeId) => {
        const existing = state.edges[edgeId];
        newState.edges[edgeId] = {
          ...existing,
          status: existing.status === 'disabled' ? 'disabled' : 'idle',
          showFlowAnimation: false
        };
      });

      newState.nodes.think = {
        ...state.nodes.think,
        status: 'active',
        visitCount: state.nodes.think.visitCount + 1,
        currentVisitIteration: newState.iteration.current,
        showPulse: true,
        iterationBadge: {
          show: state.nodes.think.visitCount + 1 > 1,
          count: state.nodes.think.visitCount + 1
        }
      };

      if (iterationNumber > 1) {
        newState.edges['reflect->think'] = {
          ...state.edges['reflect->think'],
          status: 'active',
          showFlowAnimation: true,
          transitionCount: state.edges['reflect->think'].transitionCount + 1
        };
        newState.edges['start->think'] = {
          ...state.edges['start->think'],
          status: 'completed',
          showFlowAnimation: false
        };
        setActiveEdgeFlow(newState.edges, 'reflect->think');
      } else {
        newState.edges['start->think'] = {
          ...state.edges['start->think'],
          status: 'active',
          showFlowAnimation: true,
          transitionCount: state.edges['start->think'].transitionCount + 1
        };
        newState.edges['reflect->think'] = {
          ...state.edges['reflect->think'],
          status: 'disabled',
          showFlowAnimation: false
        };
        setActiveEdgeFlow(newState.edges, 'start->think');
      }

      newState.eventHistory = [...state.eventHistory, event];
      return newState;
    }

    case 'thought':
      {
        const iterationForEvent = event.iteration ?? state.iteration.current;
        const animateEdge = iterationForEvent === state.iteration.current;

        newState.nodes.think = {
          ...state.nodes.think,
          status: 'completed',
          showPulse: false,
          lastCompletedAt: new Date().toISOString(),
          metadata: { ...state.nodes.think.metadata, thought: event.data.thought }
        };
        newState.nodes.operate = {
          ...state.nodes.operate,
          status: 'active',
          visitCount: state.nodes.operate.visitCount + 1,
          currentVisitIteration: state.iteration.current,
          showPulse: true,
          iterationBadge: {
            show: state.nodes.operate.visitCount + 1 > 1,
            count: state.nodes.operate.visitCount + 1
          }
        };
        newState.edges['start->think'] = {
          ...state.edges['start->think'],
          status: 'completed',
          showFlowAnimation: false
        };
        if (state.edges['reflect->think'].status === 'active') {
          newState.edges['reflect->think'] = {
            ...state.edges['reflect->think'],
            status: 'completed',
            showFlowAnimation: false
          };
        }
        newState.edges['think->operate'] = {
          ...state.edges['think->operate'],
          status: 'active',
          showFlowAnimation: animateEdge,
          transitionCount: state.edges['think->operate'].transitionCount + 1
        };
        if (animateEdge) {
          setActiveEdgeFlow(newState.edges, 'think->operate');
        }
        newState.eventHistory = [...state.eventHistory, event];
        return newState;
      }

    case 'action':
      {
        const timestamp = new Date().toISOString();

        if (state.nodes.reflect.status === 'active') {
          newState.nodes.reflect = {
            ...state.nodes.reflect,
            status: 'completed',
            showPulse: false,
            lastCompletedAt: timestamp,
            metadata: {
              ...state.nodes.reflect.metadata,
              decision: state.nodes.reflect.metadata?.decision || 'iterate'
            }
          };
        }

        newState.nodes.operate = {
          ...state.nodes.operate,
          status: 'active',
          showPulse: true,
          metadata: {
            ...state.nodes.operate.metadata,
            selectedTool: event.data.tool,
            tool: event.data.tool,
            startTime: timestamp
          }
        };
        newState.eventHistory = [...state.eventHistory, event];
        return newState;
      }

    case 'tool_execution':
      {
        const success = event.data.success !== false;

        newState.nodes.operate = {
          ...state.nodes.operate,
          status: success ? 'completed' : 'error',
          showPulse: false,
          lastCompletedAt: new Date().toISOString(),
          errorMessage: success ? undefined : event.data.result_summary,
          metadata: {
            ...state.nodes.operate.metadata,
            provider: event.data.provider,
            duration: event.data.duration_ms ? event.data.duration_ms / 1000 : undefined
          }
        };

        if (success) {
          newState.nodes.reflect = {
            ...state.nodes.reflect,
            status: 'active',
            visitCount: state.nodes.reflect.visitCount + 1,
            currentVisitIteration: state.iteration.current,
            showPulse: true,
            iterationBadge: {
              show: state.nodes.reflect.visitCount + 1 > 1,
              count: state.nodes.reflect.visitCount + 1
            },
            metadata: {
              ...state.nodes.reflect.metadata,
              resultCount: event.data.result_count,
              decision: 'pending'
            }
          };
        }

        newState.edges['think->operate'] = {
          ...state.edges['think->operate'],
          status: success ? 'completed' : 'disabled',
          showFlowAnimation: false
        };
        if (success) {
          newState.edges['operate->reflect'] = {
            ...state.edges['operate->reflect'],
            status: 'active',
            showFlowAnimation: true,
            transitionCount: state.edges['operate->reflect'].transitionCount + 1
          };
          setActiveEdgeFlow(newState.edges, 'operate->reflect');
        } else {
          newState.edges['operate->reflect'] = {
            ...state.edges['operate->reflect'],
            status: 'disabled',
            showFlowAnimation: false
          };
          setActiveEdgeFlow(newState.edges, undefined);
        }
        newState.stats = {
          ...state.stats,
          toolsExecuted: state.stats.toolsExecuted + 1,
          resultsFound: state.stats.resultsFound + (event.data.result_count || 0)
        };
        newState.eventHistory = [...state.eventHistory, event];
        return newState;
      }

    case 'observation':
      newState.nodes.reflect = {
        ...state.nodes.reflect,
        metadata: {
          ...state.nodes.reflect.metadata,
          observation: event.data.observation
        }
      };
      newState.eventHistory = [...state.eventHistory, event];
      return newState;

    case 'finish_guard':
      {
        const iterationForEvent = event.iteration ?? state.iteration.current;
        const animateEdge = iterationForEvent === state.iteration.current;

        if (state.edges['operate->reflect'].status === 'active') {
          newState.edges['operate->reflect'] = {
            ...state.edges['operate->reflect'],
            status: 'completed',
            showFlowAnimation: false
          };
        }

        if (event.data.approved) {
          newState.loopingFromEvaluate = false;
          newState.nodes.reflect = {
            ...state.nodes.reflect,
            status: 'completed',
            showPulse: false,
            lastCompletedAt: new Date().toISOString(),
            metadata: {
              ...state.nodes.reflect.metadata,
              decision: 'finish',
              guardFeedback: event.data.feedback
            }
          };
          newState.edges['reflect->think'] = {
            ...state.edges['reflect->think'],
            status: 'disabled',
            showFlowAnimation: false
          };
          newState.edges['reflect->evaluator'] = {
            ...state.edges['reflect->evaluator'],
            status: 'active',
            showFlowAnimation: animateEdge,
            transitionCount: state.edges['reflect->evaluator'].transitionCount + 1
          };
          if (animateEdge) {
            setActiveEdgeFlow(newState.edges, 'reflect->evaluator');
          }
        } else {
          newState.loopingFromEvaluate = true;
          newState.iteration = {
            ...state.iteration,
            current: state.iteration.current + 1,
            totalCompleted: state.iteration.totalCompleted + 1
          };
          newState.nodes.reflect = {
            ...state.nodes.reflect,
            status: 'completed',
            showPulse: false,
            lastCompletedAt: new Date().toISOString(),
            metadata: {
              ...state.nodes.reflect.metadata,
              decision: 'iterate',
              guardFeedback: event.data.feedback
            }
          };
          newState.nodes.think = {
            ...state.nodes.think,
            status: 'active',
            visitCount: state.nodes.think.visitCount + 1,
            currentVisitIteration: newState.iteration.current,
            showPulse: true,
            iterationBadge: {
              show: true,
              count: state.nodes.think.visitCount + 1
            }
          };
          newState.nodes.operate = { ...state.nodes.operate, status: 'idle', showPulse: false };

          newState.edges['reflect->think'] = {
            ...state.edges['reflect->think'],
            status: 'active',
            showFlowAnimation: true,
            transitionCount: state.edges['reflect->think'].transitionCount + 1
          };
          setActiveEdgeFlow(newState.edges, 'reflect->think');
          newState.edges['start->think'] = {
            ...state.edges['start->think'],
            showFlowAnimation: false
          };
          newState.edges['think->operate'] = {
            ...state.edges['think->operate'],
            status: 'idle',
            showFlowAnimation: false
          };
          newState.edges['operate->reflect'] = {
            ...state.edges['operate->reflect'],
            status: 'idle',
            showFlowAnimation: false
          };
        }
        newState.eventHistory = [...state.eventHistory, event];
        return newState;
      }

    case 'evaluator_start':
      newState.nodes.reflect = {
        ...state.nodes.reflect,
        showPulse: false
      };
      newState.nodes.evaluator = {
        ...state.nodes.evaluator,
        status: 'active',
        showPulse: true,
        visitCount: state.nodes.evaluator.visitCount + 1,
        currentVisitIteration: state.iteration.current,
        iterationBadge: {
          show: state.nodes.evaluator.visitCount + 1 > 1,
          count: state.nodes.evaluator.visitCount + 1
        },
        metadata: {
          ...state.nodes.evaluator.metadata,
          startTime: new Date().toISOString()
        }
      };
      newState.edges['reflect->evaluator'] = {
        ...state.edges['reflect->evaluator'],
        status: 'active',
        showFlowAnimation: true,
        transitionCount: state.edges['reflect->evaluator'].transitionCount + 1
      };
      setActiveEdgeFlow(newState.edges, 'reflect->evaluator');
      newState.eventHistory = [...state.eventHistory, event];
      return newState;

    case 'evaluator_complete':
      newState.nodes.evaluator = {
        ...state.nodes.evaluator,
        status: 'completed',
        showPulse: false,
        lastCompletedAt: new Date().toISOString(),
        metadata: {
          ...state.nodes.evaluator.metadata,
          evaluationDuration: event.data.duration_seconds,
          evaluationScores: event.data.scores
        }
      };
      newState.nodes.finish = {
        ...state.nodes.finish,
        status: 'completed',
        showPulse: false,
        lastCompletedAt: new Date().toISOString(),
        metadata: {
          reportLength: newState.pendingFinish?.reportLength,
          sourceCount: newState.pendingFinish?.sourceCount
        }
      };
      newState.pendingFinish = undefined;
      newState.edges['evaluator->finish'] = {
        ...state.edges['evaluator->finish'],
        status: 'completed',
        showFlowAnimation: true,
        transitionCount: state.edges['evaluator->finish'].transitionCount + 1
      };
      setActiveEdgeFlow(newState.edges, undefined);
      newState.eventHistory = [...state.eventHistory, event];
      return newState;

    case 'finish':
      {
        const timestamp = new Date().toISOString();
        (['think', 'operate', 'reflect'] as NodeId[]).forEach((nodeId) => {
          const prev = state.nodes[nodeId];
          newState.nodes[nodeId] = {
            ...prev,
            status: 'completed',
            showPulse: false,
            lastCompletedAt: timestamp,
            metadata:
              nodeId === 'reflect'
                ? {
                    ...prev.metadata,
                    decision: prev.metadata?.decision || 'finish'
                  }
                : prev.metadata
          };
        });

        ['think->operate', 'operate->reflect'].forEach((edgeId) => {
          const edge = state.edges[edgeId as EdgeId];
          newState.edges[edgeId as EdgeId] = {
            ...edge,
            status: 'completed',
            showFlowAnimation: false
          };
        });

        const reflectEdge = state.edges['reflect->evaluator'];
        if (reflectEdge.status === 'idle' || reflectEdge.status === 'disabled') {
          newState.edges['reflect->evaluator'] = {
            ...reflectEdge,
            status: 'active',
            showFlowAnimation: true
          };
          setActiveEdgeFlow(newState.edges, 'reflect->evaluator');
        }

        newState.pendingFinish = {
          reportLength: event.data.report_length,
          sourceCount: event.data.num_sources
        };
        newState.eventHistory = [...state.eventHistory, event];
        return newState;
      }

    case 'error':
      // Find active node and mark as error
      const activeNodeId = (Object.entries(state.nodes).find(
        ([_, node]) => node.status === 'active'
      )?.[0] || 'operate') as NodeId;

      newState.nodes[activeNodeId] = {
        ...state.nodes[activeNodeId],
        status: 'error',
        showPulse: false,
        errorMessage: event.data.error || 'An error occurred'
      };
      newState.eventHistory = [...state.eventHistory, event];
      return newState;

    case 'session_complete':
      newState.stats = {
        ...state.stats,
        endTime: new Date().toISOString(),
        sessionDuration: event.data.duration_seconds || 0,
        totalTokens: event.data.total_tokens || state.stats.totalTokens,
        totalCost: event.data.total_cost_usd || state.stats.totalCost
      };
      newState.eventHistory = [...state.eventHistory, event];
      return newState;

    case 'session_failed':
      newState.eventHistory = [...state.eventHistory, event];
      return newState;

    default:
      console.warn('Unknown event type:', event.type);
      return state;
  }
}

// ==================== ZUSTAND STORE ====================

interface WorkflowStore extends WorkflowState {
  handleEvent: (event: WorkflowEvent) => void;
  reset: () => void;
}

export const useWorkflowStore = create<WorkflowStore>((set) => ({
  ...initialState,

  handleEvent: (event: WorkflowEvent) => {
    set((state) => workflowReducer(state, event));
  },

  reset: () => set(initialState)
}));
