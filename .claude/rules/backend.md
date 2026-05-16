---
paths:
  - "backend/**"
---

# Backend (Python / Flask) Rules

The backend is a Flask REST API that manages machine configurations in CouchDB and orchestrates Telegraf processes (one per machine) via supervisord.

## Layout
```
backend/
├── src/
│   ├── app.py                             # Flask app + logging (Gunicorn target: src.app:app)
│   ├── routes.py                          # All HTTP endpoints (configure_routes)
│   ├── plc_datalink_rfc1006_model.py      # Dataclass-based config model
│   └── services/
│       ├── couchdb_service.py             # CouchDB CRUD
│       ├── machine_configuration_service.py  # Telegraf config file rendering
│       └── telegraf_service.py            # supervisord process control
├── config/
│   ├── backend-entrypoint.sh              # Container entrypoint
│   ├── dynamic_startup_telegraf.sh        # Telegraf process launcher
│   ├── supervisord.conf                   # supervisord rules
│   ├── env.example                        # Env file template (built into image as /app/.env)
│   └── example-machines/                  # Sample Telegraf configs
├── openapi/plc_datalink_rfc1006_api.yml   # OpenAPI 3 spec (served at /swagger)
├── pyproject.toml                         # Project metadata + tool config (ruff, pytest)
├── requirements.txt                       # Runtime deps (authoritative for Docker build; mirror of pyproject deps)
├── test/
│   ├── curl/                              # Shell scripts that hit the running stack
│   └── scripts/                           # Python helpers / dev utilities
└── Dockerfile
```

## Coding Standards
- Python 3 with type hints where useful
- Use dataclasses for incoming/outgoing config models (see `plc_datalink_rfc1006_model.py` pattern)
- Logger: use `logging.getLogger('application_logger')` — do not create new loggers
- Catch `HTTPError` (from `requests`) separately from generic `Exception` — preserve CouchDB status codes
- Return JSON with consistent shape: `{"message": ...}` on success, `{"error": ...}` on failure
- Always include the HTTP status code as the second tuple element in `jsonify` returns

## Endpoint Conventions
- Use kebab-style URL segments but stick to the existing prefix style (`/config/...`, `/machine/...`)
- Use query parameters for single-resource lookups (`machine_name=...`)
- Use JSON body for create/update operations
- Validate required fields and return `400` with a specific error message
- Use `404` for missing resources, `409` for conflicts (e.g. machine running, doc revision conflict)

## Service Boundaries
- `routes.py` handles HTTP — no business logic
- `couchdb_service.py` is the only module that talks to CouchDB
- `telegraf_service.py` is the only module that talks to supervisord
- `machine_configuration_service.py` is the only module that writes Telegraf config files

## OpenAPI Spec
- Every new route, parameter, or response shape must be reflected in `backend/openapi/plc_datalink_rfc1006_api.yml`
- The Swagger UI is mounted at `/swagger` (see `routes.py`)
- Do not break existing operation IDs without a deprecation note

## Quality Standards
- Test endpoints with the existing curl scripts in `backend/test/` and add new ones for new endpoints
- Confirm CouchDB error paths (404, 409) propagate correctly
- Keep `requirements.txt` minimal — do not add libraries that duplicate existing capability
