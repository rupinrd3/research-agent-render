/**
 * Workflow Animation Variants
 * Framer Motion animation configurations
 */

// Active node pulse animation
export const pulseAnimation = {
  scale: [1, 1.05, 1],
  filter: [
    'drop-shadow(0 0 0 rgba(99, 102, 241, 0))',
    'drop-shadow(0 0 20px rgba(99, 102, 241, 0.6))',
    'drop-shadow(0 0 0 rgba(99, 102, 241, 0))'
  ],
  transition: {
    duration: 2,
    repeat: Infinity,
    ease: 'easeInOut' as const
  }
};

// Node completion animation
export const completionAnimation = {
  scale: [1, 1.2, 1],
  transition: {
    duration: 0.6,
    ease: 'easeOut' as const
  }
};

// Flowing particles on edges
// Animation flows FORWARD in the direction of the line (from → to)
export const flowingParticlesAnimation = {
  strokeDashoffset: [0, -30],  // Changed from [-30, 0] to [0, -30] for forward flow
  transition: {
    duration: 1.5,
    repeat: Infinity,
    ease: 'linear' as const
  }
};

// Edge color transition
export const edgeColorTransition = (targetColor: string) => ({
  stroke: targetColor,
  transition: {
    duration: 0.5,
    ease: 'easeInOut' as const
  }
});

// Loop arc dash flow (when active)
export const loopDashFlow = {
  strokeDashoffset: [0, -24],
  transition: {
    duration: 1.5,
    repeat: Infinity,
    ease: 'linear' as const
  }
};

// Loop arc opacity pulse (when evaluating)
export const loopOpacityPulse = {
  opacity: [0.3, 0.6, 0.3],
  transition: {
    duration: 2,
    repeat: Infinity,
    ease: 'easeInOut' as const
  }
};

// Node entrance animation
export const nodeEntranceAnimation = {
  initial: { opacity: 0, scale: 0.8 },
  animate: { opacity: 1, scale: 1 },
  transition: { duration: 0.3 }
};

// Edge draw animation
export const edgeDrawAnimation = {
  initial: { pathLength: 0 },
  animate: { pathLength: 1 },
  transition: { duration: 0.5 }
};

// Error shake animation
export const errorShakeAnimation = {
  x: [0, -10, 10, -10, 10, 0],
  transition: {
    duration: 0.5,
    ease: 'easeInOut' as const
  }
};

// Badge pop-in animation
export const badgePopInAnimation = {
  initial: { scale: 0, opacity: 0 },
  animate: { scale: 1, opacity: 1 },
  transition: { type: 'spring', stiffness: 300, damping: 20 }
};

// Glow effect animation
export const glowAnimation = {
  boxShadow: [
    '0 0 20px rgba(99, 102, 241, 0.4)',
    '0 0 40px rgba(168, 85, 247, 0.6)',
    '0 0 20px rgba(99, 102, 241, 0.4)'
  ],
  transition: {
    duration: 2,
    repeat: Infinity,
    ease: 'easeInOut' as const
  }
};
