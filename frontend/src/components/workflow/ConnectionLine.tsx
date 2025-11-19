/**
 * ConnectionLine Component
 * Renders animated connections between workflow nodes
 */

'use client';

import React from 'react';
import { motion } from 'framer-motion';
import type { EdgeState } from '@/stores/workflowStore';
import { EDGE_COLORS, NODE_RADIUS } from './constants';
import { flowingParticlesAnimation, edgeDrawAnimation } from './animations';

export interface ConnectionLineProps {
  from: { x: number; y: number };
  to: { x: number; y: number };
  state: EdgeState;
}

export const ConnectionLine = React.memo<ConnectionLineProps>(({
  from,
  to,
  state
}) => {
  const color = EDGE_COLORS[state.status];

  // Calculate arrow head position and angle
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const angle = Math.atan2(dy, dx);
  const distance = Math.sqrt(dx * dx + dy * dy);
  const arrowLength = 8;

  // Node radius - we'll adjust endpoints to touch the edge of nodes
  const nodeRadius = NODE_RADIUS;

  // Start from edge of source node
  const adjustedFrom = {
    x: from.x + (nodeRadius / distance) * dx,
    y: from.y + (nodeRadius / distance) * dy
  };

  // End at edge of target node (accounting for arrow)
  const adjustedTo = {
    x: to.x - ((nodeRadius + arrowLength) / distance) * dx,
    y: to.y - ((nodeRadius + arrowLength) / distance) * dy
  };

  // Arrow head at target node edge
  const arrowTip = {
    x: to.x - (nodeRadius / distance) * dx,
    y: to.y - (nodeRadius / distance) * dy
  };

  return (
    <g>
      {/* Base line */}
      <motion.line
        x1={adjustedFrom.x}
        y1={adjustedFrom.y}
        x2={adjustedTo.x}
        y2={adjustedTo.y}
        stroke={color}
        strokeWidth={state.style.strokeWidth}
        strokeLinecap="round"
        opacity={state.style.opacity}
        strokeDasharray={state.style.dashArray}
        {...edgeDrawAnimation}
      />

      {/* Flowing animation overlay (when active) */}
      {state.showFlowAnimation && (
        <motion.line
          x1={adjustedFrom.x}
          y1={adjustedFrom.y}
          x2={adjustedTo.x}
          y2={adjustedTo.y}
          stroke={color}
          strokeWidth={state.style.strokeWidth + 1}
          strokeLinecap="round"
          strokeDasharray="10 20"
          opacity={0.8}
          animate={flowingParticlesAnimation}
        />
      )}

      {/* Arrow head */}
      <motion.polygon
        points={`
          ${arrowTip.x},${arrowTip.y}
          ${arrowTip.x - arrowLength * Math.cos(angle - Math.PI / 6)},${
            arrowTip.y - arrowLength * Math.sin(angle - Math.PI / 6)
          }
          ${arrowTip.x - arrowLength * Math.cos(angle + Math.PI / 6)},${
            arrowTip.y - arrowLength * Math.sin(angle + Math.PI / 6)
          }
        `}
        fill={color}
        opacity={state.style.opacity}
      />
    </g>
  );
});

ConnectionLine.displayName = 'ConnectionLine';
