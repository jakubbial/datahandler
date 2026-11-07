# Repository-wide instructions for AI coding agents

## Project structure
- `frontend/` is the React + TypeScript + Vite application.
- `backend/` is the FastAPI + Python application.
- Keep changes within the relevant application unless the task requires a cross-cutting change.
- Before editing, inspect the existing files and follow the conventions already established in the codebase.

## Development environment
- Development takes place in GitHub Codespaces. Use the appropriate frontend or backend dev container when available.
- Do not invent run, build, lint, or test commands. Check the repository documentation and project configuration first; if commands are not defined, say so.

## Git and pull requests
- Use branch names with a short description and one of these prefixes: `feature/`, `bugfix/`, `hotfix/`, `chore/`, `docs/`, or `refactor/`.
- Use Conventional Commits for commit messages and pull request titles.
- Pull requests are squash-merged; keep the PR title suitable as the resulting commit message.

## Change quality
- Make the smallest change that fully addresses the request. Avoid unrelated refactors and new dependencies unless necessary.
- Preserve existing APIs and behavior unless the task explicitly asks to change them.
- Update relevant documentation and tests when behavior changes. Run available checks relevant to the files changed, and report checks that could not be run.
- Never claim a check passed unless it was actually run and passed.
- Do not add secrets, credentials, or real user data. Treat external input as untrusted and follow the security practices already used in the project.

## Area-specific guidance
- For work under `frontend/`, read `frontend/AGENTS.md`.
- For work under `backend/`, read `backend/AGENTS.md`.
- For changes spanning both areas, read both files.
