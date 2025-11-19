/**
 * Workflow Visualization Constants
 * Defines positions, colors, and layout constants
 */

import type { NodeId } from '@/stores/workflowStore';

// Node positions for desktop layout
export const NODE_POSITIONS: Record<NodeId, { x: number; y: number }> = {
  start: { x: 80, y: 200 },
  think: { x: 260, y: 200 },
  operate: { x: 480, y: 200 },
  reflect: { x: 700, y: 200 },
  evaluator: { x: 920, y: 200 },
  finish: { x: 1120, y: 200 }
};

// Node dimensions
export const NODE_RADIUS = 42;
export const NODE_SPACING = 180;

// Layout breakpoints
export const BREAKPOINTS = {
  DESKTOP: 1200,
  TABLET: 768,
  MOBILE: 0
};

// Layout configurations
export const LAYOUTS = {
  FULL_HORIZONTAL: {
    nodeSpacing: 150,
    nodeRadius: 35,
    containerWidth: 1200,
    showAllMetadata: true
  },
  COMPACT_CHIP: {
    nodeSpacing: 80,
    nodeRadius: 24,
    containerWidth: 700,
    showCondensedLabels: true
  },
  SCROLLABLE_STRIP: {
    nodeSpacing: 120,
    nodeRadius: 32,
    snapToActiveNode: true,
    showNavigationDots: true
  }
};

// Node state colors
export const NODE_COLORS = {
  idle: {
    from: '#E5E7EB',
    to: '#D1D5DB',
    text: '#6B7280'
  },
  active: {
    from: '#6366F1',
    to: '#8B5CF6',
    text: '#FFFFFF'
  },
  completed: {
    from: '#10B981',
    to: '#059669',
    text: '#FFFFFF'
  },
  error: {
    from: '#EF4444',
    to: '#DC2626',
    text: '#FFFFFF'
  },
  skipped: {
    from: '#F3F4F6',
    to: '#E5E7EB',
    text: '#9CA3AF'
  }
};

// Edge state colors
export const EDGE_COLORS = {
  idle: '#D1D5DB',
  active: '#6366F1',
  completed: '#10B981',
  disabled: '#E5E7EB'
};

// Node labels and sublabels
export const NODE_LABELS: Record<NodeId, { label: string; sublabel: string }> = {
  start: { label: 'Start', sublabel: 'Query Received' },
  think: { label: 'Think', sublabel: 'Reasoning' },
  operate: { label: 'Execute', sublabel: 'Select · Run · Process' },
  reflect: { label: 'Reflect', sublabel: 'Observe & Decide' },
  evaluator: { label: 'Evaluator Agent', sublabel: 'Quality Check' },
  finish: { label: 'Finish', sublabel: 'Final Report' }
};

// Loop arc path (quadratic Bezier curve from reflect to think)
export const LOOP_ARC_PATH = 'M 700 165 Q 500 80 260 165';

export const REACT_GROUP_BOUNDS = {
  x: NODE_POSITIONS.think.x - 120,
  y: 65,
  width: NODE_POSITIONS.reflect.x - NODE_POSITIONS.think.x + 240,
  height: 270
};

// Animation durations (in seconds)
export const ANIMATION_DURATIONS = {
  NODE_PULSE: 2,
  EXECUTE_ROTATION: 3,
  FLOWING_PARTICLES: 1.5,
  LOOP_DASH: 1.5,
  TRANSITION: 0.5,
  COMPLETION: 0.6
};

// Z-index layers
export const Z_INDEX = {
  EDGES: 1,
  LOOP_ARC: 2,
  NODES: 3,
  BADGES: 4
};
