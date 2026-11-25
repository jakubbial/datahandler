# Frontend

React + TypeScript + Vite application managed with npm.

## Run with Compose

```bash
docker compose up frontend --build
```

The app is exposed on port `3100`. Requests to `/api` are proxied by Vite to the backend service.

In Codespaces, the dev server starts automatically. Open the forwarded port `3100`
in VS Code's Ports panel instead of starting a second server on the same port.

## Local Data Bank browser

The `/local-data-bank` page browses the backend `GET /subjects` tree
(category → group → subject). The current position is kept in the URL as
`id-slug` segments, for example `/local-data-bank/K15-ceny/G186-ceny-w-rolnictwie`.
Only the id before the first `-` is used; the slug is readable decoration and is
corrected automatically. Responses are cached in memory per `parent_id` for the
browser session to avoid duplicate requests.

Selecting a subject with variables loads its variables from `GET /variables`
(cached in memory per `subject_id`). Variables are grouped by the part of the
name before the first ` - ` and can be filtered by name. The selected variable
is kept in the `variable` query parameter, for example
`/local-data-bank/K15-ceny/G186-ceny-w-rolnictwie/P3183-...?variable=288616`.
For territorial data, select years (up to 30) and press Load data. By default,
the request covers all voivodeships and is limited to one BDL page. If the
results need more than one page, select a voivodeship to narrow the request.
For levels 6 and above, an optional county filter narrows it further. Filters
are sent to BDL before downloading data; for level 2, the loaded voivodeships
can also be filtered locally without another request. A dash marks missing
values and values whose attribute is not 1. Each reported value includes its
attribute explanation (and symbol when available). Measure and last-update
metadata are displayed above the results, including empty results. Unknown
dictionary IDs are shown explicitly rather than guessed. The data endpoint returns
`{ measureUnit: { id, name }, lastUpdate, units }`, not a bare units array.

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
