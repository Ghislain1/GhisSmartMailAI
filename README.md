# GhisSmartMailAI

Smart mail AI project with a FastAPI backend and a React (Vite) frontend.

## Repository structure

- `backend/` - FastAPI service managed with [uv](https://docs.astral.sh/uv/) (`app/` modules: `api`, `core`, `db`, `models`, `services`, `agents`, `mcp`; `tests/`)
- `frontend/` - React + Vite web app (`src/`)
- `docs/` - project documentation (architecture, API, prompts)
- `mcp-servers/` - MCP server components
- `n8n/` - n8n workflows/integration assets
- `.github/workflows/` - CI/CD and automation workflows
- `.opencode/` - opencode agent configuration

## Getting started

### Prerequisites

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Node.js and npm

### Environment

Copy the example environment file and adjust as needed:

```bash
cp .env.example .env
```

### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

Health check: `GET /health` -> `{"status":"ok"}`

Run tests:

```bash
cd backend
uv run pytest
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Build / preview:

```bash
npm run build
npm run preview
```

### Docker

Build and run the full stack (backend + frontend):

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000 (`/health`)

Stop:

```bash
docker compose down
```

## Documentation

- [Architecture](docs/architecture.md)
- [API](docs/api.md)
- [Agent prompts](docs/agent-prompts.md)
