# Agentic Research Lab - Frontend

Modern Next.js frontend for the Agentic AI Research solution with real-time ReAct architecture visualization.

## Features

- 🎨 **Modern UI**: Dark theme with glassmorphism effects and smooth animations
- ⚡ **Real-time Updates**: WebSocket integration for live research progress
- 📊 **Three-Panel Layout**:
  - ReAct Trace Timeline (left)
  - Current Activity Panel (center)
  - Research Output Panel (right)
- 🔄 **State Management**: Zustand for efficient global state
- 🎭 **Animations**: Framer Motion for smooth transitions
- 📝 **Markdown Rendering**: Rich research reports with syntax highlighting
- 🎯 **TypeScript**: Full type safety throughout the application

## Tech Stack

- **Framework**: Next.js 14+ with App Router
- **Language**: TypeScript
- **Styling**: TailwindCSS + Custom CSS
- **State**: Zustand
- **Real-time**: Socket.IO Client
- **Animations**: Framer Motion
- **UI Components**: Radix UI + Custom Components
- **Markdown**: React Markdown + Remark GFM

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js app router pages
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Main research page
│   │   └── globals.css        # Global styles
│   ├── components/            # React components
│   │   ├── ui/               # Reusable UI primitives
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── progress.tsx
│   │   │   └── textarea.tsx
│   │   └── research/         # Research-specific components
│   │       ├── header.tsx
│   │       ├── query-input.tsx
│   │       ├── react-trace-timeline.tsx
│   │       ├── current-activity-panel.tsx
│   │       └── research-output-panel.tsx
│   ├── hooks/                 # Custom React hooks
│   │   └── use-websocket.ts  # WebSocket connection hook
│   ├── lib/                   # Utility functions
│   │   ├── utils.ts          # General utilities
│   │   └── constants.ts      # App constants
│   ├── store/                 # Zustand state stores
│   │   └── research-store.ts # Research state management
│   └── types/                 # TypeScript type definitions
│       └── index.ts          # All type definitions
├── public/                    # Static assets
├── package.json              # Dependencies
├── tsconfig.json            # TypeScript configuration
├── tailwind.config.js       # TailwindCSS configuration
├── next.config.js           # Next.js configuration
└── .env.local.example       # Environment variables template
```

## Installation

### Prerequisites

- Node.js 18+ and npm/yarn/pnpm
- Backend server running on http://localhost:8000

### Setup Steps

1. **Install Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure Environment**
   ```bash
   cp .env.local.example .env.local
   ```

   Edit `.env.local`:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_WS_URL=ws://localhost:8000
   ```

3. **Run Development Server**
   ```bash
   npm run dev
   ```

   Frontend will be available at http://localhost:3000

4. **Build for Production** (optional)
   ```bash
   npm run build
   npm start
   ```

## Component Documentation

### Main Components

#### **Header** (`components/research/header.tsx`)
- Application branding with gradient logo
- Navigation controls (Settings, History)
- User profile placeholder

#### **QueryInput** (`components/research/query-input.tsx`)
- Multi-line textarea with character limit (1000 chars)
- Example query suggestions (6 pre-defined queries)
- Real-time validation
- Keyboard shortcut (Ctrl+Enter to submit)

#### **ReactTraceTimeline** (`components/research/react-trace-timeline.tsx`)
- Left panel showing complete reasoning trace
- Collapsible iterations
- Color-coded phases:
  - 🧠 **Thought** (purple): Agent reasoning
  - ⚡ **Action** (cyan): Tool selection
  - ✓ **Execution** (green/red): Tool execution status
  - 👁️ **Observation** (emerald): Result interpretation
  - 📊 **Evaluation** (amber): Quality metrics

#### **CurrentActivityPanel** (`components/research/current-activity-panel.tsx`)
- Center panel showing real-time activity
- Agent status with animated icon
- Progress bar with ETA
- Latest update messages
- Tool output summaries

#### **ResearchOutputPanel** (`components/research/research-output-panel.tsx`)
- Right panel displaying final report
- Markdown rendering with syntax highlighting
- Source citations with metadata
- Export options (Copy, Download, Share)

### Custom Hooks

#### **useWebSocket** (`hooks/use-websocket.ts`)
Manages WebSocket connections for real-time updates.

```tsx
const { isConnected, status } = useWebSocket({
  sessionId: currentSession?.id,
  sessionUrl: currentSession?.websocketUrl,
  enabled: isResearching,
  onUpdate: handleUpdate,
  onError: handleError,
});
```

Features:
- Automatic connection management
- Reconnection with exponential backoff
- Event handling for research updates
- Integration with Zustand store

### State Management

#### **useResearchStore** (`store/research-store.ts`)
Global state management using Zustand.

```tsx
const {
  currentSession,
  isResearching,
  iterations,
  activityState,
  toolOutputs,
  report,
  startResearch,
  stopResearch,
} = useResearchStore();
```

State includes:
- Current research session
- Iterations array
- Activity state
- Tool outputs
- Final report
- Settings
- History

## Styling

### Theme
- **Base**: Dark slate theme (slate-900, slate-800)
- **Accent**: Indigo-purple gradient
- **Effects**: Glassmorphism, smooth transitions

### Custom Utilities
- `.glass`: Glassmorphism effect with backdrop blur
- `.gradient-text`: Gradient text effect
- `.shimmer`: Loading shimmer animation
- `.pulse-glow`: Pulsing glow effect
- `.scrollbar-thin`: Custom scrollbar styling

## Real-time Updates

The frontend receives real-time updates via WebSocket:

1. **Session Events**: `session_start`, `session_complete`
2. **Iteration Events**: `iteration_start`, `iteration_complete`
3. **Phase Events**: `thought_generated`, `action_executing`, `observation_generated`
4. **Report Events**: `report_chunk`, `report_complete`
5. **Error Events**: `error`

Each event updates the corresponding part of the UI automatically.

## Example Queries

The application includes 6 pre-configured example queries:

1. **Multimodal LLMs**: Latest advances in vision-language models
2. **RAG vs Fine-tuning**: Comparison for domain-specific applications
3. **Quantum Computing**: Recent breakthroughs and applications
4. **Edge AI**: Challenges and solutions for edge deployment
5. **Web3 Development**: Frameworks and best practices
6. **LLM Agents**: ReAct and other agent architectures

## Development

### Code Style
- **Comprehensive docstrings**: All components and functions documented
- **Human-readable code**: Clear naming and structure
- **Function size limits**: Small, focused functions
- **No mega files**: Logical component separation

### Type Safety
All components are fully typed with TypeScript. See `src/types/index.ts` for complete type definitions.

### Animations
Animations use Framer Motion with predefined variants:
- `fadeInUp`: Elements entering from bottom
- `stagger`: Sequential child animations
- `pulse`: Continuous pulsing for active elements
- `shimmer`: Loading state animation

## Troubleshooting

### WebSocket Connection Issues
- Ensure backend is running on correct port
- Check CORS settings in backend
- Verify `NEXT_PUBLIC_WS_URL` in `.env.local`

### Build Errors
```bash
# Clear Next.js cache
rm -rf .next
npm run build
```

### Type Errors
```bash
# Run type check
npm run type-check
```

## Performance

- **Code Splitting**: Automatic with Next.js App Router
- **Lazy Loading**: Components loaded on demand
- **Optimized Re-renders**: Zustand selectors prevent unnecessary updates
- **WebSocket Throttling**: Updates batched for smooth UI

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## License

This project is part of the Agentic Research Lab educational platform.

## Contributing

See the main project README for contribution guidelines.

## Support

For issues and questions, please check the main project documentation or create an issue in the repository.
