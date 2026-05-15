# ADR-0001: Backend Application Entrypoint Layout

**Status:** Accepted
**Date:** 2026-05-15
**Scope:** [docs/features/project-structure-best-practices/scope.md](../../docs/features/project-structure-best-practices/scope.md)

## Context
The Flask backend's application object (`app`) and all initialization (logging handlers, CORS, dotenv loading, route registration, Telegraf service bootstrap) lived in `backend/src/init.py`. Two issues:

1. **Confusing naming next to `__init__.py`.** `backend/src/__init__.py` exists (empty, 0 bytes) and is Python's standard package marker. Having a non-magic sibling called `init.py` reads like a typo of `__init__.py` and forces every new contributor to verify which one is actually loaded.
2. **Imports across the codebase still need to reference the entrypoint.** Gunicorn is wired in via `backend/config/supervisord.conf` as `src.init:app`; tests, future scripts, and ad-hoc REPL sessions repeat the unfamiliar path.

Two options were considered for cleaning this up.

## Decision
Rename `backend/src/init.py` to `backend/src/app.py`. Keep `backend/src/__init__.py` empty.

The Gunicorn target in `backend/config/supervisord.conf` becomes `src.app:app`. The Dockerfile copies `src/` as a directory, so no Dockerfile change is required for the rename itself.

## Alternatives Considered
- **Option A — Merge `init.py` into `__init__.py` (Flask app-factory pattern).**
  - Pros: idiomatic for Flask; imports become `from src import app` or via a `create_app()` factory.
  - Cons: `__init__.py` then has side effects on package import — a known foot-gun (importing the package starts handlers, opens log files, reads `.env`). It also requires either committing fully to a factory pattern (`create_app()`) or keeping the side-effects-on-import we already have. The factory rewrite is wider than this scope.
- **Option B — Rename to `backend/src/app.py` (chosen).**
  - Pros: discoverable; matches the most common Flask tutorial convention; `__init__.py` stays free of side effects; one-line change in `supervisord.conf`; no callers in the tracked source besides supervisord.
  - Cons: not the "purest" app-factory pattern. Acceptable here because the app is small and there is no need to instantiate multiple Flask apps (no tests yet that would benefit from a factory).

## Consequences
**Positive**
- Naming no longer collides visually with `__init__.py`
- Single, obvious entrypoint at `backend/src/app.py`
- Refactor to a proper `create_app()` factory remains possible as a future ADR without re-litigating the file name

**Negative / Trade-offs**
- Module-level side effects on import remain (logging handlers registered, dotenv loaded, Telegraf service constructed). Not addressed in this ADR.

**Migration / Compatibility**
- One operational change: `backend/config/supervisord.conf` must point Gunicorn at `src.app:app`. Rolling deploys must rebuild the backend image — there is no in-place runtime migration.
- No external consumers reference the module path; only Gunicorn does.
- Backward compatibility shim (e.g. `init.py` re-exporting `app`) is **not** introduced — there is no out-of-tree code to support.

## References
- Scope: [docs/features/project-structure-best-practices/scope.md](../../docs/features/project-structure-best-practices/scope.md) (Phase B)
- Touch points: `backend/config/supervisord.conf`, `.claude/rules/backend.md`
