# Repository Guidelines

## Project Structure & Module Organization
- Backend lives in `backend/` with FastAPI orchestrator and research agents under `backend/app/agents`, tools in `app/tools`, LLM plumbing in `app/llm`, and API routes in `app/api`. Shared utilities, tracing, and database helpers sit beside these modules.
- Frontend is Next.js in `frontend/`: pages in `src/app`, shared components in `src/components`, global state in `src/store`, DTOs in `src/types`, and static assets in `public/`.
- Runtime artifacts such as `research.db`, exported reports, and top-level settings (`config.yaml`) remain in the repo root alongside docs and configs.

## Build, Test, and Development Commands
- Backend setup: `cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt`.
- Backend run: `uvicorn app.api.main:app --reload --port 8000` for the API; `python main.py` for CLI-only runs.
- Frontend setup: `cd frontend && npm install`.
- Frontend run: `npm run dev` (http://localhost:3000); production smoke: `npm run build && npm start`.

## Coding Style & Naming Conventions
- Python: prefer async/await, snake_case for functions/files, PascalCase for models, and suffix new orchestrators with `Agent` or `Tool`. Format with `black` and `isort`; lint with `flake8`; type-check with `mypy`.
- TypeScript/React: 2-space indent, PascalCase components, kebab-case route folders. Use Tailwind utilities for styling. Run `npm run lint` and `npm run type-check` before pushing.

## Testing Guidelines
- Backend: pytest + pytest-asyncio. Add suites under `backend/tests` or near the feature using `test_<feature>.py`. Target ≥80% coverage via `pytest --cov=app`. Fast checks: `python validate_fixes.py` (E2E) and `python test_imports.py` (env sanity).
- Frontend: ensure `npm run lint` and `npm run type-check` pass; add component or Playwright tests for interactive flows.

## Commit & Pull Request Guidelines
- Use Conventional Commits (`feat:`, `fix:`, `chore:`) in imperative form.
- Every PR: concise summary, linked issue, reproduction steps, verification notes, and screenshots/GIFs for UI changes. Confirm `pytest`, `validate_fixes.py`, `npm run lint`, and `npm run build` as applicable. Update docs (`GETTING_STARTED.md`, `QUICK_START.md`, config samples) when behavior or commands change.

## Security & Configuration Tips
- Copy `backend/.env.example` to `.env`; supply only required keys and never commit secrets or `research.db`.
- Derive `config.yaml` from `config.example.yaml`. Route external integrations through helpers in `app/tools` and emit tracing via `app/tracing` to avoid leaking credentials.
