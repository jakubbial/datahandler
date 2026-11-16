# Frontend

React + TypeScript + Vite application managed with npm.

## Run with Compose

```bash
docker compose up frontend --build
```

The app is exposed on port `3100`. Requests to `/api` are proxied by Vite to the backend service.

In Codespaces, the dev server starts automatically. Open the forwarded port `3100`
in VS Code's Ports panel instead of starting a second server on the same port.

## Manual development server

If the server is not already running, run these commands from the repository root:

```bash
cd frontend
npm ci
npm run dev
```

If `npm ci` reports `EACCES` for a Codespaces dependency volume owned by `root`,
restore ownership from `frontend/` and retry:

```bash
sudo chown -hR "$(id -u):$(id -g)" node_modules
npm ci
```

## Build

```bash
npm install
npm run build
```
