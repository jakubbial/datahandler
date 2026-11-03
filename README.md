# DataHandler

DataHandler: briefly check open databases.

## Running

Development happens only in GitHub Codespaces. When creating a codespace, choose
the `frontend` or `backend` dev container configuration. The configurations and
run commands will be added in a later stage.

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
