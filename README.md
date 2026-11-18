# DataHandler

DataHandler: briefly check open databases.

## Development with GitHub Codespaces

The project uses one Codespace and Docker Compose to run the React/Vite frontend and FastAPI backend together. No database or Docker-in-Docker is required.

Create a Codespace from the repository and select the `datahandler` dev container. Compose starts both services automatically. The editor connects to the frontend container with Node.js and npm available, and the repository is mounted at `/workspaces/datahandler`.

The editor container also has Python 3.12 and Poetry, so backend code can be edited, linted and tested without switching containers. When the Codespace is created, backend dependencies are installed in Poetry's virtual environment outside the repository. A stable link at `/home/node/.venvs/backend` lets Pylance, Ruff and the VS Code test explorer use it. The backend service has its own environment and does not share the editor's. From the editor terminal:

```bash
cd backend
poetry run pytest
poetry run ruff check .
poetry run ruff format --check .
```

Uvicorn in the backend service reloads on file changes; call new endpoints at `http://backend:8100/...` from the editor terminal or through Swagger UI.

### Services and ports

- Frontend: port `3100`
- Backend API: port `8100`
- Swagger UI: `http://localhost:8100/docs`
- Health endpoint: `http://localhost:8100/health`

The frontend calls `/api/health`; Vite proxies `/api` requests to the backend service on the Compose network. This avoids browser CORS configuration during development.

### Useful commands

Run in the Codespace terminal:

```bash
docker compose up --build        # build and start both services
docker compose logs -f           # follow service logs
docker compose restart backend   # restart one service
docker compose down              # stop the services
```

Compose also starts automatically when the Codespace is created. For normal work, use the forwarded Vite port; you do not need to run `docker compose up` a second time.

### Dependency changes

- Backend: edit `backend/pyproject.toml`; the backend startup command runs `poetry install`. Run `cd backend && poetry install --with dev` to update the editor's Poetry environment as well.
- Frontend: edit `frontend/package.json`; the frontend startup command runs `npm install`. `node_modules` is kept in a named Compose volume.
- Frontend API base URL: see `frontend/.env.example`; Compose sets `VITE_API_BASE_URL=/api`.

## CI

GitHub Actions builds the frontend and runs backend tests on pushes and pull requests.

## Conventions

### Branches

Use a prefix and a short description, for example `feature/add-file-upload`.
Allowed prefixes: `feature/`, `bugfix/`, `hotfix/`, `chore/`, `docs/`, `refactor/`.

### Commits and pull requests

The project uses [Conventional Commits](https://www.conventionalcommits.org/).
Only squash merge is allowed. The pull request title becomes the commit message,
so it must follow Conventional Commits, and the pull request description is kept
in the history.

## Agent files

`AGENTS.md` contains instructions for AI coding agents. Like workflows and dev
container configuration, it is treated as code: it requires review and is
covered by CODEOWNERS.
