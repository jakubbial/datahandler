# Repository-wide instructions for AI coding agents

## Project structure
- `frontend/` is the React + TypeScript + Vite application.
- `backend/` is the FastAPI + Python application.
- Keep changes within the relevant application unless the task requires a cross-cutting change.
- Before editing, inspect the existing files and follow the conventions already established in the codebase.

## Repository map
- `frontend/src/pages/` contains pages; `frontend/src/components/` contains reusable UI components.
- `frontend/src/api/` contains API clients; `frontend/src/hooks/` contains data-loading and state hooks.
- `frontend/src/utils/` contains frontend helpers; `frontend/src/App.tsx` defines application routes.
- `backend/app/routers/` contains API endpoints; `backend/app/*_service.py` contains service logic and caches.
- `backend/app/bdl_client.py` handles BDL API requests; `backend/app/main.py` configures the application.
- `backend/tests/` contains backend tests; `docker-compose.yml` configures development services.

## Development environment
- Development takes place in GitHub Codespaces. Use the appropriate frontend or backend dev container when available.
- Do not invent run, build, lint, or test commands. Check the repository documentation and project configuration first; if commands are not defined, say so.

## BDL API rate limits
- The BDL API (`https://bdl.stat.gov.pl/api/v1`) enforces request limits per client. Exceeding them returns HTTP 429 with `Retry-After` and blocks access for hours, for both agents and the running application.

  | Window | Anonymous | With `BDL_CLIENT_ID` key |
  |---|---|---|
  | 1 second | 5 | 10 |
  | 15 minutes | 100 | 500 |
  | 12 hours | 1,000 | 5,000 |
  | 7 days | 10,000 | 50,000 |

- The key is shared by agents, developers, and the backend. Use it sparingly; treat every live request as a cost.
- Prefer existing knowledge first: `docs/bdl-api-guide.md`, the OpenAPI spec, tests with mocked responses, and `backend/logs/bdl-monitoring.log`.
- When a live request is necessary, make the smallest one: a single resource, specific IDs and years, a narrow `unit-level` or `unit-parent-id`, and a small `page-size`. Do not crawl subject trees, iterate over all units or variables, or fetch every page.
- Never run loops, scripts, or load tests against the live API. Tests must mock BDL (for example with `httpx.MockTransport`) and never call it.
- Check `X-Rate-Limit-Remaining` when you make a live request. Stop on HTTP 429, do not retry before `Retry-After` expires, and report it to the user.
- Never print, log, or commit the `BDL_CLIENT_ID` value; read it from the environment only.

## Git and pull requests
- Use branch names with a short description and one of these prefixes: `feature/`, `bugfix/`, `hotfix/`, `chore/`, `docs/`, or `refactor/`.
- Use Conventional Commits for commit messages and pull request titles.
- Pull requests are squash-merged; keep the PR title suitable as the resulting commit message.

## Language
- Everything in the code must be in English: identifiers, file names, route paths, comments, user-facing UI text, log and error messages, and tests.

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
