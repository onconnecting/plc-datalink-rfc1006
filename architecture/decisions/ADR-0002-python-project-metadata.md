# ADR-0002: Python Project Metadata via pyproject.toml

**Status:** Accepted
**Date:** 2026-05-15
**Scope:** [docs/features/project-structure-best-practices/scope.md](../../docs/features/project-structure-best-practices/scope.md)

## Context
The backend declares its runtime dependencies in `backend/requirements.txt` (six packages: `python-dotenv`, `requests`, `Flask`, `flask_cors`, `gunicorn`, `flask-swagger-ui`). The Docker image installs from that file at build time:

```dockerfile
COPY requirements.txt ./
RUN /venv/bin/pip install -r requirements.txt
```

This works, but it gives us no place to declare project metadata (name, version, Python version constraint), no place to declare development-only tooling (lint, format, test), and no place to configure tools like Ruff or Pytest. As Phase C of the structure cleanup, the project gains pre-commit hooks (ruff lint + format), a CI lint job, and the option to run a small test suite. Each of these needs a configuration home.

## Decision
Introduce `backend/pyproject.toml` (PEP 621) alongside `requirements.txt`. The `pyproject.toml` declares:

- Project metadata (name, version, description, Python version)
- Runtime dependencies (mirroring `requirements.txt`)
- An `[project.optional-dependencies.dev]` group for `ruff` and `pytest`
- Tool configuration: `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.pytest.ini_options]`

`requirements.txt` is **kept as the authoritative input for the Docker build**. The Dockerfile remains unchanged. `pyproject.toml` is used for local development workflows (`pip install -e .`), CI lint/test jobs, and tooling configuration.

The two files must be kept in sync manually for now (six entries; trivial). A future ADR may flip the build to install from `pyproject.toml` directly once the team is comfortable.

## Alternatives Considered
- **Option A — Replace `requirements.txt` with `pyproject.toml` only.**
  - Pros: single source of truth.
  - Cons: requires modifying the Dockerfile and re-validating the image build. Higher blast radius for what is otherwise a tooling-cleanup change. Deferred.
- **Option B — Keep `requirements.txt` only, put tool config in separate files (`ruff.toml`, `pytest.ini`).**
  - Pros: smallest change.
  - Cons: fragments tool config across multiple files; misses the chance to declare a `dev` extras group; runs against PEP 518/621 conventions that most Python tooling now expects.
- **Option C — Adopt Poetry / PDM / uv.**
  - Pros: lockfiles, modern dependency resolution.
  - Cons: introduces a new build tool into the Docker image and the developer workflow. Out of scope for a tooling cleanup.

## Consequences
**Positive**
- Tool configuration (Ruff, Pytest) has a conventional home
- A `dev` extras group lets contributors `pip install -e .[dev]` to pull lint/test tools without polluting the runtime image
- Project metadata becomes machine-readable

**Negative / Trade-offs**
- Two dependency declarations to keep in sync (`requirements.txt` and `[project.dependencies]`)
- New contributors may be unsure which is canonical — the answer is documented in this ADR and in `backend/pyproject.toml` comments

**Migration / Compatibility**
- Docker build is unaffected
- Local dev: `pip install -r requirements.txt` continues to work; `pip install -e .[dev]` becomes available
- CI gains a lint workflow that installs from `pyproject.toml`'s `dev` extras

## References
- Scope: [docs/features/project-structure-best-practices/scope.md](../../docs/features/project-structure-best-practices/scope.md) (Phase C)
- PEP 621 — Storing project metadata in pyproject.toml
- Touch points: `backend/pyproject.toml`, `.pre-commit-config.yaml`, `.github/workflows/lint.yml`
