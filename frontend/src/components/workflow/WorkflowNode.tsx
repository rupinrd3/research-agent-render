/**
 * WorkflowNode Component
 * Renders individual stages of the workflow with state-based styling and animations
 */

'use client';

import React from 'react';
import { motion } from 'framer-motion';
import {
  Play,
  Brain,
  Menu,
  Settings,
  GitBranch,
  Flag,
  CheckCircle,
  AlertCircle,
  type LucideIcon
} from 'lucide-react';
import type { NodeState, NodeId } from '@/stores/workflowStore';
import { NODE_COLORS, NODE_LABELS, NODE_RADIUS } from './constants';
import { pulseAnimation, completionAnimation, errorShakeAnimation } from './animations';

const NODE_ICONS: Record<NodeId, LucideIcon> = {
  start: Play,
  think: Brain,
  operate: Settings,
  reflect: GitBranch,
  evaluator: Menu,
  finish: Flag
};

export interface WorkflowNodeProps {
  id: NodeId;
  label: string;
  sublabel: string;
  state: NodeState;
  position: { x: number; y: number };
  radius?: number;
}

export const WorkflowNode = React.memo<WorkflowNodeProps>(({
  id,
  label,
  sublabel,
  state,
  position,
  radius = NODE_RADIUS
}) => {
  const Icon = NODE_ICONS[id];
  const colors = NODE_COLORS[state.status];

  // Check if execute icon should rotate
  const shouldRotate = id === 'operate' && state.status === 'active';

  return (
    <g transform={`translate(${position.x}, ${position.y})`}>
      {/* Main node circle */}
      <defs>
        <linearGradient id={`gradient-${id}-${state.status}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={colors.from} />
          <stop offset="100%" stopColor={colors.to} />
        </linearGradient>

        {/* Glow filter for active state */}
        <filter id={`glow-${id}`} x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="4" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>

        {/* Drop shadow filter */}
        <filter id={`shadow-${id}`} x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur in="SourceAlpha" stdDeviation="3" />
          <feOffset dx="0" dy="2" result="offsetblur" />
          <feComponentTransfer>
            <feFuncA type="linear" slope="0.2" />
          </feComponentTransfer>
          <feMerge>
            <feMergeNode />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Animated wrapper for pulse effect */}
      <motion.g
        animate={
          state.status === 'error'
            ? errorShakeAnimation
            : state.showPulse && state.status === 'active'
            ? { scale: [1, 1.05, 1] }
            : {}
        }
        transition={
          state.showPulse && state.status === 'active'
            ? { duration: 2, repeat: Infinity, ease: 'easeInOut' as const }
            : state.status === 'error'
            ? { duration: 0.5, ease: 'easeInOut' as const }
            : {}
        }
      >
        <circle
          r={radius}
          fill={`url(#gradient-${id}-${state.status})`}
          filter={state.showGlow ? `url(#glow-${id})` : `url(#shadow-${id})`}
        />
      </motion.g>

      {/* Icon */}
      <foreignObject
        x={-12}
        y={-12}
        width={24}
        height={24}
        className="pointer-events-none"
      >
        <div className="flex items-center justify-center w-full h-full">
          <Icon
            size={20}
            color={colors.text}
            className={shouldRotate ? 'animate-spin' : ''}
            style={{
              animationDuration: shouldRotate ? '3s' : undefined
            }}
          />
        </div>
      </foreignObject>

      {/* Iteration badge (top-right) */}
      {state.iterationBadge?.show && (
        <g transform={`translate(${radius - 12}, ${-radius + 12})`}>
          <motion.circle
            r={12}
            fill="#059669"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
          />
          <text
            fontSize={10}
            fill="white"
            textAnchor="middle"
            y={4}
            fontWeight="600"
          >
            ×{state.iterationBadge.count}
          </text>
        </g>
      )}

      {/* State indicator (bottom-right) */}
      {state.status === 'completed' && (
        <g transform={`translate(${radius - 10}, ${radius - 10})`}>
          <motion.circle
            r={10}
            fill="white"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={completionAnimation.transition}
          />
          <foreignObject x={-8} y={-8} width={16} height={16}>
            <div className="flex items-center justify-center w-full h-full">
              <CheckCircle size={14} className="text-green-600" />
            </div>
          </foreignObject>
        </g>
      )}

      {state.status === 'error' && (
        <g transform={`translate(${radius - 10}, ${radius - 10})`}>
          <circle r={10} fill="white" />
          <foreignObject x={-8} y={-8} width={16} height={16}>
            <div className="flex items-center justify-center w-full h-full">
              <AlertCircle size={14} className="text-red-600" />
            </div>
          </foreignObject>
        </g>
      )}

      {/* Labels */}
      <text
        y={radius + 24}
        fontSize={14}
        fill="#FFFFFF"
        textAnchor="middle"
        fontWeight="600"
      >
        {label}
      </text>
      <text
        y={radius + 42}
        fontSize={12}
        fill="#FFFFFF"
        textAnchor="middle"
      >
        {sublabel}
      </text>

      {/* Error message tooltip (if applicable) */}
      {state.errorMessage && (
        <g transform={`translate(0, ${radius + 50})`}>
          <rect
            x={-80}
            y={0}
            width={160}
            height={40}
            rx={4}
            fill="#FEE2E2"
            stroke="#DC2626"
            strokeWidth={1}
          />
          <foreignObject x={-75} y={5} width={150} height={30}>
            <div className="text-xs text-red-700 text-center leading-tight p-1">
              {state.errorMessage.substring(0, 50)}
              {state.errorMessage.length > 50 ? '...' : ''}
            </div>
          </foreignObject>
        </g>
      )}
    </g>
  );
});

WorkflowNode.displayName = 'WorkflowNode';
