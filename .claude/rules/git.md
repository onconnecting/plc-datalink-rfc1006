# Git Conventions

## Commit Format
```
type(area): description
```

## Types
| Type | Use for |
|---|---|
| `feat` | new feature or capability |
| `fix` | bug fix or correction |
| `refactor` | restructuring without behavior change |
| `test` | adding or updating tests |
| `docs` | documentation only (README, ADRs, API spec, CHANGELOG) |
| `chore` | tooling, build scripts, dependency bumps |
| `ci` | GitHub Actions, Dockerfile, supervisord, nginx config |

## Areas
`backend` · `frontend` · `database` · `telegraf` · `docker` · `api` · `ci` · `docs` · `architecture`

## Examples
```
feat(backend): add endpoint for reading machine state history
fix(frontend): correct PLC address validation in create-configuration form
feat(telegraf): support DT (date-time) tag type in PLC address parser
refactor(backend): extract Telegraf config rendering into helper module
docs(api): document /machine/online response shape
chore(docker): bump base image to python:3.12-slim
ci(github): add docker build matrix for backend, frontend, database
test(backend): add curl-based regression test for config/update
```

## Rules
- NEVER commit credentials, API keys, or `.env` files
- NEVER commit `backend/.venv/` (it's a virtual environment, not source)
- NEVER commit large binaries other than the existing screenshots in `images/`
- NEVER commit without a meaningful message
- One logical change per commit — do not bundle unrelated changes (e.g. backend fix + frontend feature)
- Reference the feature scope (`docs/features/<name>/`) or issue number in the commit body if applicable
- Keep the subject line under 72 characters; put detail in the body
