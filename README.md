# DataHandler

DataHandler: briefly check open databases.

## Running in GitHub Codespaces

Development runs in a single GitHub Codespace using Docker Compose. The repository contains a shared devcontainer setup and a Compose file that starts the backend and frontend together.

### Start environment

```bash
docker compose up --build
```

Then open:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000/docs

This project keeps the backend and frontend in separate application directories while sharing one Codespace and one Compose configuration.

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
