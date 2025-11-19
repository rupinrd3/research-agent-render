/**
 * WorkflowChart Component
 * Main container that assembles all workflow visualization components
 */

'use client';

import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { useWorkflowStore } from '@/stores/workflowStore';
import { WorkflowNode } from './WorkflowNode';
import { ConnectionLine } from './ConnectionLine';
import { LoopArc, type LoopVisibility } from './LoopArc';
import { NODE_POSITIONS, NODE_LABELS, REACT_GROUP_BOUNDS } from './constants';
import type { NodeId } from '@/stores/workflowStore';

export interface WorkflowChartProps {
  className?: string;
}

const NODE_ORDER: NodeId[] = ['start', 'think', 'operate', 'reflect', 'evaluator', 'finish'];

export const WorkflowChart: React.FC<WorkflowChartProps> = ({ className }) => {
  const { nodes, edges, iteration, sessionId } = useWorkflowStore();

  // Calculate workflow progress based on iteration and stage completion
  // Progress should NEVER go backwards, even when looping
  const workflowProgress = useMemo(() => {
    // If finish is completed, we're at 100%
    if (nodes.finish.status === 'completed') {
      return 100;
    }

    const maxIterations = iteration.max || 10;
    const currentIteration = iteration.current || 1;

    // 90% of progress comes from iterations, 10% from finish
    // Each iteration contributes: 90% / maxIterations
    const progressPerIteration = 90 / maxIterations;

    // Base progress from completed iterations
    // (current - 1) because current iteration is in progress
    const baseProgress = Math.max(0, (currentIteration - 1)) * progressPerIteration;

    // Progress within current iteration based on active/completed stage
    // Stage weights within an iteration cycle
    const stageWeights: Record<string, number> = {
      start: 0.0,
      think: 0.25,
      operate: 0.65,
      reflect: 0.9,
      finish: 0.0
    };

    // Find the furthest active or completed stage in current iteration
    let stageProgress = 0;
    const stageOrder: NodeId[] = ['think', 'operate', 'reflect'];

    for (const nodeId of stageOrder) {
      const node = nodes[nodeId];
      if (node.status === 'active' || node.status === 'completed') {
        stageProgress = Math.max(stageProgress, stageWeights[nodeId] || 0);
      }
    }

    // Current iteration contribution
    const iterationProgress = stageProgress * progressPerIteration;

    // Total progress
    const totalProgress = Math.min(90, baseProgress + iterationProgress);

    return Math.round(totalProgress);
  }, [nodes, iteration]);

  // Determine loop arc visibility
  const loopVisibility: LoopVisibility = useMemo(() => {
    const loopEdge = edges['reflect->think'];
    const reflectNode = nodes.reflect;
    const finishNode = nodes.finish;

    // Hidden if finish is completed (workflow done)
    if (finishNode.status === 'completed') {
      return 'hidden';
    }

    // Hidden until first iteration reaches evaluate
    if (iteration.current === 1 && reflectNode.visitCount === 0) {
      return 'hidden';
    }

    // Active when loop edge is active
    if (loopEdge.status === 'active') {
      return 'active';
    }

    // Pulsing when reflect is active (deciding)
    if (reflectNode.status === 'active') {
      return 'pulsing';
    }

    // Dormant after first loop
    if (loopEdge.transitionCount >= 1) {
      return 'dormant';
    }

    return 'hidden';
  }, [edges, nodes.reflect, nodes.finish, iteration.current]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className={className}
    >
      {/* Iteration badge */}
      <div className="flex items-center justify-between mb-4 px-4">
        <div className="flex items-center gap-4">
          <div className="text-sm text-gray-400">
            <span className="font-semibold text-white">
              Iteration {iteration.current}
            </span>
            <span className="text-gray-500"> / {iteration.max}</span>
          </div>
          {iteration.totalCompleted > 0 && (
            <div className="text-xs text-gray-300 bg-gray-800 px-2 py-1 rounded">
              {iteration.totalCompleted} loop{iteration.totalCompleted > 1 ? 's' : ''} completed
            </div>
          )}
        </div>
        {sessionId && (
          <div className="text-xs text-gray-500">
            Session: {sessionId.substring(0, 8)}
          </div>
        )}
      </div>

      {/* SVG Canvas */}
      <div className="bg-black border border-gray-800 rounded-lg shadow-sm overflow-hidden">
        <svg
          width="100%"
          height="400"
          viewBox="0 0 1300 400"
          className="w-full"
          preserveAspectRatio="xMidYMid meet"
        >
          <defs>
            {/* Shadow filter */}
            <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
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
            <linearGradient id="reactGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#312e81" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#1e1b4b" stopOpacity="0.5" />
            </linearGradient>
          </defs>

          {/* ReAct grouping box */}
          <g>
            <rect
              x={REACT_GROUP_BOUNDS.x}
              y={REACT_GROUP_BOUNDS.y}
              width={REACT_GROUP_BOUNDS.width}
              height={REACT_GROUP_BOUNDS.height}
              rx={24}
              fill="url(#reactGradient)"
              fillOpacity={0.2}
              stroke="#312e81"
              strokeWidth={1}
            />
            <text
              x={REACT_GROUP_BOUNDS.x + REACT_GROUP_BOUNDS.width / 2}
              y={REACT_GROUP_BOUNDS.y + 24}
              fill="#ffffff"
              fontSize="16"
              textAnchor="middle"
            >
              ReAct Agent
            </text>
          </g>
          {/* Render edges first (lower z-index) */}
          <g className="edges">
            <ConnectionLine
              from={NODE_POSITIONS.start}
              to={NODE_POSITIONS.think}
              state={edges['start->think']}
            />
            <ConnectionLine
              from={NODE_POSITIONS.think}
              to={NODE_POSITIONS.operate}
              state={edges['think->operate']}
            />
            <ConnectionLine
              from={NODE_POSITIONS.operate}
              to={NODE_POSITIONS.reflect}
              state={edges['operate->reflect']}
            />
            <ConnectionLine
              from={NODE_POSITIONS.reflect}
              to={NODE_POSITIONS.evaluator}
              state={edges['reflect->evaluator']}
            />
            <ConnectionLine
              from={NODE_POSITIONS.evaluator}
              to={NODE_POSITIONS.finish}
              state={edges['evaluator->finish']}
            />
          </g>

          {/* Loop arc */}
          <LoopArc
            visibility={loopVisibility}
            transitionCount={edges['reflect->think'].transitionCount}
          />

          {/* Render nodes (higher z-index) */}
          <g className="nodes">
            {NODE_ORDER.map((nodeId) => {
              const { label, sublabel } = NODE_LABELS[nodeId];
              return (
                <WorkflowNode
                  key={nodeId}
                  id={nodeId}
                  label={label}
                  sublabel={sublabel}
                  state={nodes[nodeId]}
                  position={NODE_POSITIONS[nodeId]}
                />
              );
            })}
          </g>
        </svg>
      </div>

      {/* Progress bar */}
      <div className="mt-4 px-4">
        <div className="flex items-center gap-3">
          <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-indigo-500 to-purple-500"
              initial={{ width: '0%' }}
              animate={{
                width: `${workflowProgress}%`
              }}
              transition={{ duration: 0.5, ease: 'easeOut' as const }}
            />
          </div>
          <span className="text-xs font-medium text-gray-300 min-w-[45px] text-right">
            {workflowProgress}%
          </span>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 px-4 flex items-center gap-4 text-xs text-gray-400">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-gradient-to-br from-gray-200 to-gray-300" />
          <span>Idle</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 animate-pulse" />
          <span>Active</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-gradient-to-br from-green-500 to-green-600" />
          <span>Completed</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-gradient-to-br from-red-500 to-red-600" />
          <span>Error</span>
        </div>
      </div>
    </motion.div>
  );
};
