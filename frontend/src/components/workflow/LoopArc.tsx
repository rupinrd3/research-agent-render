/**
 * LoopArc Component
 * Renders the iteration loop arc from Evaluate back to Think
 */

'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { LOOP_ARC_PATH, EDGE_COLORS } from './constants';
import { loopDashFlow, loopOpacityPulse } from './animations';

export type LoopVisibility = 'hidden' | 'dormant' | 'pulsing' | 'active';

export interface LoopArcProps {
  visibility: LoopVisibility;
  transitionCount: number;
}

export const LoopArc = React.memo<LoopArcProps>(({
  visibility,
  transitionCount
}) => {
  if (visibility === 'hidden') {
    return null;
  }

  const getOpacity = () => {
    switch (visibility) {
      case 'dormant':
        return 0.3;
      case 'pulsing':
        return undefined; // Will use animation
      case 'active':
        return 1;
      default:
        return 0;
    }
  };

  const getAnimation = () => {
    if (visibility === 'pulsing') return loopOpacityPulse;
    if (visibility === 'active') return loopDashFlow;
    return {};
  };

  const color = visibility === 'active' ? EDGE_COLORS.active : EDGE_COLORS.completed;

  return (
    <g>
      {/* Loop arc path */}
      <motion.path
        d={LOOP_ARC_PATH}
        stroke={color}
        strokeWidth={3}
        fill="none"
        strokeLinecap="round"
        strokeDasharray="8 8"
        opacity={getOpacity()}
        animate={getAnimation()}
      />

      {/* Arrow head pointing to Think */}
      <motion.polygon
        points="260,165 252,160 252,170"
        fill={color}
        opacity={getOpacity()}
        animate={visibility === 'pulsing' ? loopOpacityPulse : {}}
      />

      {/* Loop count badge (if loop has occurred) */}
      {transitionCount > 0 && (
        <g transform="translate(530, 60)">
          <motion.circle
            r={16}
            fill={visibility === 'active' ? '#6366F1' : '#059669'}
            opacity={0.9}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
          />
          <text
            fontSize={11}
            fill="white"
            textAnchor="middle"
            y={5}
            fontWeight="600"
          >
            ↻{transitionCount}
          </text>
        </g>
      )}

      {/* Label */}
      <text
        x={530}
        y={95}
        fontSize={10}
        fill="#6B7280"
        textAnchor="middle"
        fontWeight="500"
      >
        {visibility === 'active' ? 'Looping...' : 'Iteration Loop'}
      </text>
    </g>
  );
});

LoopArc.displayName = 'LoopArc';
