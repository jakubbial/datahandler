# Frontend

React + TypeScript + Vite application managed with npm.

## Run with Compose

```bash
docker compose up frontend --build
```

The app is exposed on port `5173`. Requests to `/api` are proxied by Vite to the backend service.

## Build

```bash
npm install
npm run build
```
