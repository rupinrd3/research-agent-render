/**
 * Constants and configuration values for the Agentic Research Lab frontend
 */

import type { ExampleQuery } from '@/types';

/**
 * API endpoints
 */
export const API_ENDPOINTS = {
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  WS_URL: process.env.NEXT_PUBLIC_WS_URL || '',
  RESEARCH: '/api/research',
  HISTORY: '/api/history',
  CONFIG: '/api/config',
  EXPORT: '/api/export',
} as const;

/**
 * WebSocket events
 */
export const WS_EVENTS = {
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  ERROR: 'error',
  RESEARCH_UPDATE: 'research_update',
  SESSION_START: 'session_start',
  ITERATION_COMPLETE: 'iteration_complete',
  REPORT_CHUNK: 'report_chunk',
  SESSION_COMPLETE: 'session_complete',
} as const;

/**
 * Example research queries for user inspiration
 */
export const EXAMPLE_QUERIES: ExampleQuery[] = [
  {
    id: '1',
    title: 'Multimodal LLMs',
    query: 'What are the latest advances in multimodal large language models, particularly vision-language models?',
    category: 'AI/ML',
    estimatedDuration: '3-5 min',
  },
  {
    id: '2',
    title: 'RAG vs Fine-tuning',
    query: 'Compare Retrieval-Augmented Generation (RAG) and fine-tuning approaches for domain-specific LLM applications',
    category: 'AI/ML',
    estimatedDuration: '4-6 min',
  },
  {
    id: '3',
    title: 'Quantum Computing',
    query: 'Explain recent breakthroughs in quantum computing and their potential applications in cryptography',
    category: 'Quantum',
    estimatedDuration: '5-7 min',
  },
  {
    id: '4',
    title: 'Edge AI',
    query: 'What are the current challenges and solutions for deploying AI models on edge devices?',
    category: 'AI/ML',
    estimatedDuration: '3-5 min',
  },
  {
    id: '5',
    title: 'Web3 Development',
    query: 'Overview of Web3 development frameworks and best practices for building decentralized applications',
    category: 'Blockchain',
    estimatedDuration: '4-6 min',
  },
  {
    id: '6',
    title: 'LLM Agents',
    query: 'How do LLM-based autonomous agents work, and what are the most effective architectures like ReAct?',
    category: 'AI/ML',
    estimatedDuration: '4-6 min',
  },
];

/**
 * Default settings
 */
export const DEFAULT_SETTINGS = {
  llmProvider: 'openrouter' as const,
  llmModel: 'nvidia/llama-3.3-nemotron-super-49b-v1.5',
  temperature: 0.7,
  maxIterations: 10,
  apiKeys: {
    openai: '',
    gemini: '',
    openrouter: '',
  },
};

/**
 * Tool icons mapping
 */
export const TOOL_ICONS = {
  web_search: 'Search',
  arxiv_search: 'FileText',
  github_search: 'Github',
  pdf_parser: 'FileUp',
} as const;

/**
 * Tool colors mapping for UI
 */
export const TOOL_COLORS = {
  web_search: 'cyan',
  arxiv_search: 'purple',
  github_search: 'orange',
  pdf_parser: 'emerald',
} as const;

/**
 * Status colors mapping
 */
export const STATUS_COLORS = {
  pending: 'slate',
  running: 'indigo',
  completed: 'green',
  failed: 'red',
  cancelled: 'yellow',
} as const;

/**
 * Iteration phase labels
 */
export const PHASE_LABELS = {
  pending: 'Waiting',
  thinking: 'Thinking',
  acting: 'Executing',
  observing: 'Observing',
  evaluating: 'Evaluating',
  complete: 'Complete',
  failed: 'Failed',
} as const;

/**
 * Animation durations (in milliseconds)
 */
export const ANIMATION_DURATION = {
  FAST: 150,
  NORMAL: 300,
  SLOW: 500,
  VERY_SLOW: 1000,
} as const;

/**
 * Transition presets for Framer Motion
 */
export const TRANSITIONS = {
  spring: {
    type: 'spring',
    stiffness: 200,
    damping: 20,
  },
  smooth: {
    type: 'tween',
    ease: 'easeInOut',
    duration: 0.3,
  },
  bounce: {
    type: 'spring',
    stiffness: 300,
    damping: 15,
  },
} as const;

/**
 * Maximum values for various inputs
 */
export const MAX_VALUES = {
  QUERY_LENGTH: 1000,
  ITERATIONS: 20,
  TEMPERATURE: 1.0,
  MIN_TEMPERATURE: 0.0,
} as const;

/**
 * Local storage keys
 */
export const STORAGE_KEYS = {
  SETTINGS: 'agentic-research-lab:settings',
  RECENT_QUERIES: 'agentic-research-lab:recent-queries',
  THEME: 'agentic-research-lab:theme',
  API_KEYS: 'agentic-research-lab:api-keys',
} as const;

/**
 * Error messages
 */
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error. Please check your connection and try again.',
  API_ERROR: 'An error occurred while communicating with the server.',
  WEBSOCKET_ERROR: 'WebSocket connection failed. Real-time updates may not work.',
  INVALID_QUERY: 'Please enter a valid research query.',
  MISSING_API_KEY: 'API key is required. Please configure it in settings.',
  SESSION_NOT_FOUND: 'Research session not found.',
  EXPORT_FAILED: 'Failed to export the research report.',
} as const;

/**
 * Success messages
 */
export const SUCCESS_MESSAGES = {
  RESEARCH_STARTED: 'Research session started successfully!',
  RESEARCH_COMPLETED: 'Research completed successfully!',
  COPIED_TO_CLIPBOARD: 'Copied to clipboard!',
  SETTINGS_SAVED: 'Settings saved successfully!',
  EXPORT_COMPLETE: 'Report exported successfully!',
} as const;

/**
 * Score thresholds
 */
export const SCORE_THRESHOLDS = {
  EXCELLENT: 9,
  VERY_GOOD: 8,
  GOOD: 7,
  FAIR: 6,
  AVERAGE: 5,
} as const;

/**
 * Supported export formats
 */
export const EXPORT_FORMATS = [
  { value: 'markdown', label: 'Markdown (.md)', icon: 'FileText' },
  { value: 'pdf', label: 'PDF Document (.pdf)', icon: 'FileDown' },
  { value: 'word', label: 'Word Document (.docx)', icon: 'FileText' },
  { value: 'html', label: 'HTML (.html)', icon: 'Globe' },
  { value: 'json', label: 'JSON (.json)', icon: 'Code' },
] as const;

/**
 * LLM Provider options
 */
export const LLM_PROVIDERS = [
  { value: 'openai', label: 'OpenAI', models: ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo'] },
  { value: 'gemini', label: 'Google Gemini', models: ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-1.5-pro'] },
  {
    value: 'openrouter',
    label: 'OpenRouter',
    models: [
      'deepseek/deepseek-r1-0528:free',
      'minimax/minimax-m2:free',
      'meta-llama/llama-3.3-70b-instruct:free',
      'nvidia/llama-3.3-nemotron-super-49b-v1.5',
    ],
  },
] as const;

/**
 * Pagination defaults
 */
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 10,
  PAGE_SIZE_OPTIONS: [10, 25, 50, 100],
} as const;

/**
 * Persisted settings schema version
 */
export const SETTINGS_VERSION = 3;
