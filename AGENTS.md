# Repository Guidelines

## Project Structure & Module Organization
The backend (`backend/`) hosts the FastAPI orchestrator and research agents. Core logic sits in `backend/app/agents`, `tools`, `llm`, and `api`, while shared utilities, tracing, and database helpers stay adjacent. Runtime artifacts (`research.db`, exported reports) and top-level settings (`config.yaml`) also live here. The frontend (`frontend/`) is a Next.js workspace: pages in `src/app`, shared components in `src/components`, global state in `src/store`, typed DTOs in `src/types`, and static assets in `public/`.

## Build, Test, and Development Commands
Backend essentials:
- `cd backend && python -m venv venv && source venv/bin/activate`
- `pip install -r requirements.txt`
- `uvicorn app.api.main:app --reload --port 8000`
- `python main.py` for CLI-only runs
Frontend essentials:
- `cd frontend && npm install`
- `npm run dev` (http://localhost:3000)
- `npm run build && npm start` for prod smoke

## Coding Style & Naming Conventions
Python: run `black`, `isort`, `flake8`, and `mypy` before committing; keep snake_case for functions/files, PascalCase for models, and suffix new orchestrators with `Agent` or `Tool`. Prefer explicit typing and async/await over callbacks. Frontend: TypeScript with 2-space indent, ESLint via `npm run lint`, Tailwind utilities for styling, PascalCase React components, and kebab-case route folders.

## Testing Guidelines
Back-end tests rely on pytest + pytest-asyncio. Add suites under `backend/tests` or near the module, keep names `test_<feature>.py`, and target ≥80% coverage via `pytest --cov=app`. Fast regressions: `python validate_fixes.py` (end-to-end flow) and `python test_imports.py` (environment sanity). Front-end work should at least pass `npm run lint` and `npm run type-check`; add component tests or Playwright specs when touching interactive flows.

## Commit & Pull Request Guidelines
Use Conventional Commits (`feat:`, `fix:`, `chore:`) written in the imperative. Every PR needs a summary, linked issue, reproduction + verification notes, and screenshots/GIFs for UI deltas. Confirm `pytest`, `validate_fixes.py`, `npm run lint`, and `npm run build` (when applicable) before requesting review, and update docs (`GETTING_STARTED.md`, `QUICK_START.md`, or config samples) whenever behavior, schema, or commands change.

## Security & Configuration Tips
Copy `backend/.env.example` to `.env`, provide only the API keys you need, and never commit secrets or `research.db`. Derive `config.yaml` from `config.example.yaml`, double-check provider fallback order, and document any new LLM/tool scopes. When integrating external sources, route requests through the helpers in `app/tools` and emit tracing data via `app/tracing` to avoid leaking raw credentials in logs.
