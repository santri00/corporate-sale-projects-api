# A Python API Example

A FastAPI service as a demo for the idea of managing corporate sales **projects** and the
**clients** they belong to. Storage is MongoDB via [Beanie](https://beanie-odm.dev/);
the whole `Project` aggregate (workflow, team, financials, logistics, design
services, corporate gifting) is stored as a single document.

Base path for every endpoint: **`/corporate-sales/v1`**

## Requirements

- Python 3.11+
- MongoDB 7 (a `docker-compose.yml` is provided for local use)

## Setup

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# POSIX:    source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

## Run

### Whole stack in Docker (API + MongoDB)

```bash
docker compose up --build
```

Brings up `mongo` (`:27017`) and `api` (`:8000`). The `api` container waits for
Mongo's health check before starting and connects via `MONGO_URI=mongodb://mongo:27017`.

### Local API with Dockerised MongoDB (live reload for development)

```bash
docker compose up -d mongo
uvicorn app.main:app --reload
```

- Interactive docs: http://localhost:8000/docs
- Health check: `GET /corporate-sales/v1/health`

## Test

Tests use `mongomock-motor` (in-process) — **no MongoDB server needed**:

```bash
pytest
```

## Endpoints

| Method & path | Description |
|---|---|
| `POST   /clients` | Create a client |
| `GET    /clients` | List clients — `page`, `size`, `companyName`, `clientType`, `region` |
| `GET    /clients/{client_id}` | Get a client |
| `PATCH  /clients/{client_id}` | Partial update |
| `GET    /clients/{client_id}/projects` | Paginated projects for a client |
| `POST   /projects` | Create a project (requires an existing `clientId`) |
| `GET    /projects` | List / search — see query params below |
| `GET    /projects/{project_id}` | Full project aggregate |
| `PATCH  /projects/{project_id}/workflow` | Status / triggers / `deliveryNeedByDate` |
| `PATCH  /projects/{project_id}/financials` | Budget, sales, quote/order numbers, billing |

### `GET /projects` query parameters

| Param | Default | Notes |
|---|---|---|
| `page` | `1` | |
| `size` | `20` | 1–100 |
| `clientName` | – | case-insensitive partial match on the client's `companyName` |
| `clientId` | – | exact match |
| `dateFrom` / `dateTo` | – | inclusive; `422` if `dateFrom > dateTo` |
| `dateField` | `createdAt` | `createdAt` \| `deliveryNeedByDate` \| `closedAt` |
| `status` / `projectType` / `priority` | – | exact enum match |
| `sort` | `-createdAt` | `createdAt`, `projectName`, `priority`, `status` (prefix `-` for desc) |

List responses are wrapped:

```json
{ "items": [ ... ], "pagination": { "page": 1, "size": 20, "total": 137, "pages": 7 } }
```

`GET /projects` items are a lightweight `ProjectSummary`; the full nested
aggregate is returned only by `GET /projects/{project_id}`.

## Workflow state machine

States: `NEW`, `HOLD`, `QUOTE_REQUESTED`, `PRODUCT_FINALIZED`, `COMPLETE`, `CANCELLED`

| From | Allowed to |
|---|---|
| `NEW` | `QUOTE_REQUESTED`, `HOLD`, `CANCELLED` |
| `QUOTE_REQUESTED` | `PRODUCT_FINALIZED`, `HOLD`, `CANCELLED` |
| `PRODUCT_FINALIZED` | `COMPLETE`, `HOLD`, `CANCELLED` |
| `HOLD` | resume to the state it was held from; or `CANCELLED` |
| `COMPLETE` / `CANCELLED` | terminal |

An **explicit** `status` in `PATCH .../workflow` that violates the table returns
`409`. Automation-driven advances (below) are applied only when legal, otherwise
the trigger flag is stored and the status is left unchanged.

### Automation (enabled)

- `isQuoteRequested` false→true while `NEW` ⇒ advance to `QUOTE_REQUESTED`
- `isProductFinalized` false→true while `QUOTE_REQUESTED` ⇒ advance to `PRODUCT_FINALIZED`
- `requiresDesignServices` false→true ⇒ create an empty `designServices` sub-document
  (toggling it back to false keeps the data)
- reaching `COMPLETE` ⇒ set `project.closedAt` and `financials.projectCloseDate` (if unset)
- reaching `CANCELLED` ⇒ set `project.closedAt` (if unset)

## `PATCH .../financials` array handling

`quoteIds` and `orderNumbers` honour `?arrayMode=`:

- `replace` (default) — overwrite with the supplied array
- `append` — union, de-duplicated
- `remove` — drop the supplied values

Scalar fields always replace.

## v1 trade-offs / notes

- **Money** (`budget`, `totalSale`) is stored as `float`. Switch to
  `bson.Decimal128` before this handles real invoicing.
- **`deliveryNeedByDate`** is stored as an ISO-8601 date string; range queries on
  it rely on lexical ordering of ISO strings. The default and best-tested range
  field is `createdAt`.
- No authentication (per spec). `app/api/deps.py` is where an auth dependency
  would attach.
- Indexes are not declared yet — add them on `Project.clientId`,
  `Project.createdAt` and `Client.companyName` for production.

## Layout

```
app/
  main.py                 app factory + lifespan (Beanie init)
  core/config.py          settings
  core/db.py              init_database(client=None)
  errors.py               AppError -> HTTP mapping
  models/                 Beanie documents + embedded value objects
  schemas/                request / response models (camelCase)
  services/
    workflow_rules.py     transition table + automation
    clients.py
    projects.py
  api/deps.py             pagination + project filter dependencies
  api/v1/router.py        mounts /corporate-sales/v1
  api/v1/routes_*.py
tests/
```
