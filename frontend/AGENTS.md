# Frontend agent instructions

Read the repository-root `AGENTS.md` as well as this file before changing frontend code.

## Scope and stack
- Frontend source belongs in `frontend/`; the project is described as React, TypeScript, and Vite.
- Keep frontend-only changes in this directory unless the task requires a shared or backend change.
- Inspect the existing project configuration and follow its patterns; do not assume dependencies, scripts, or directory conventions that are not present.

## Implementation guidance
- Prefer clear, typed React and TypeScript code consistent with the surrounding components and project conventions.
- Keep UI, state, and API concerns aligned with existing patterns; do not introduce a new framework or state-management dependency without a clear need.
- Consider loading, empty, error, and success states when changing user-facing flows.
- Add or update tests if a test setup exists. Run the relevant checks defined by the project and report anything unavailable.
