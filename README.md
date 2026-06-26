# AI Assistant Code

Ticket-based AI coding assistant — submit tasks, AI agents execute them, results come back with diffs.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Frontend Setup

```bash
cd frontend
npm install
```

## Run

Backend:
```bash
uvicorn app.main:app --reload
```

Frontend (in another terminal):
```bash
cd frontend
npm run dev
```

- Frontend: [http://localhost:5173](http://localhost:5173)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Login

The frontend has a lightweight role gate:

- User login: enter any FE/QA name. The user workspace only shows tickets created with that name.
- Admin login: enter an admin name and passphrase. Default passphrase is `admin`.

To change the admin passphrase for the dev UI:

```bash
VITE_ADMIN_PASSWORD="your-passphrase" npm run dev
```

## Agent Execution

By default the app runs agents in dry-run mode, so tickets, queueing, logs, and chat can be tested without changing code.

```bash
APP_REPOSITORY_PATH=/path/to/your/backend/project
APP_AGENT_EXECUTION_ENABLED=true
APP_CODEX_COMMAND="codex exec"
APP_CODEX_PRO_COMMAND="codex exec"
APP_ANTIGRAVITY_COMMAND="antigravity"
APP_GEMINI_FLASH_COMMAND="gemini"
```

To expose multiple project scopes in the UI:

```bash
APP_PROJECTS="Backend=/path/to/backend,Admin API=/path/to/admin-api,Mobile API=/path/to/mobile-api"
```

If `APP_PROJECTS` is not set, the UI shows one default project from `APP_REPOSITORY_PATH`.

Flow:

- `question` runs immediately and does not enter the code-change queue.
- `request` and `issue` with `low` or `medium` complexity enter the single-worker queue.
- `hard` complexity becomes `review_required` until the backend admin approves it.
- Executed code-change tickets get a branch name like `ai-ticket/<id>-<title>` and store agent output plus `git diff` in the admin log.

## Test

```bash
pytest -v
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tickets/` | Create ticket |
| GET | `/api/tickets/` | List tickets |
| GET | `/api/tickets/{id}` | Get ticket |
| PATCH | `/api/tickets/{id}` | Update ticket |
| DELETE | `/api/tickets/{id}` | Soft delete ticket |
