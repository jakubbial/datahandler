# Backend agent instructions

Read the repository-root `AGENTS.md` as well as this file before changing backend code.

## Scope and stack
- Backend source belongs in `backend/`; the project is described as a FastAPI application written in Python.
- Keep backend-only changes in this directory unless the task requires a shared or frontend change.
- Inspect the existing project configuration and follow its patterns; do not assume dependencies, scripts, or directory conventions that are not present.

## Implementation guidance
- Follow the existing FastAPI structure, Python style, and dependency-injection patterns.
- Validate and constrain external input at the application boundary. Avoid exposing secrets or sensitive data in responses and logs.
- Preserve existing API contracts unless the task explicitly requests a change; update relevant documentation and tests when they do change.
- Add or update tests if a test setup exists. Run the relevant checks defined by the project and report anything unavailable.
