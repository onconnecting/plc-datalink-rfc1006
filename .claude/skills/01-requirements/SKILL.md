---
name: requirements
description: Scope a new feature, change, or bug for the PLC Datalink RFC1006 project. Capture use case, acceptance criteria, and impact across backend, frontend, database, and Telegraf — without prescribing implementation.
argument-hint: "feature name or one-line description of the change"
user-invocable: true
---

# Requirements & Scoping

## Role
You scope a change to the PLC Datalink RFC1006 platform. Your output is a short, structured feature note that captures **what** is changing, **why**, and **which parts of the system** are affected — not how to implement it.

## When to Use
- Adding a new PLC tag data type
- Adding a new REST endpoint or changing an existing one
- Adding a new UI screen or significantly changing an existing one
- Changing the MQTT payload shape or the CouchDB document schema
- Adding a new container, port, or external dependency

**Skip this skill for trivial changes** (typo fixes, log level tweaks, single-line bug fixes). Go straight to `/backend`, `/frontend`, or `/database`.

## Before Starting
1. `git status` and `git log --oneline -5` — understand the current branch state
2. `ls docs/features/ 2>/dev/null` — check for related in-flight scopes
3. `ls architecture/decisions/ 2>/dev/null` — check for ADRs that constrain this work
4. `git branch --show-current` — note the current branch

## Workflow

### Phase 0 — Discovery
Use `AskUserQuestion` to clarify:
- **What is the trigger?** Bug, customer request, internal cleanup, new PLC model?
- **Who benefits?** Plant operator, integrator, developer, ops?
- **What is the smallest version that delivers value?** (Avoid gold-plating.)
- **Does this break existing consumers?** (MQTT subscribers, API clients, stored CouchDB docs)
- **Acceptance criteria** — how will we know it's done? List 2–5 concrete checks.

### Phase 1 — Determine the Affected Areas
Map the change to components. For each, mark **Yes / No / Maybe**:

| Area | Touched? | Notes |
|---|---|---|
| `backend/src/routes.py` | | new/changed endpoint? |
| `backend/src/plc_datalink_rfc1006_model.py` | | data model change? |
| `backend/src/services/` | | which service file? |
| `backend/openapi/plc_datalink_rfc1006_api.yml` | | API spec update? |
| `backend/config/dynamic_startup_telegraf.sh` | | Telegraf rendering change? |
| `backend/config/example-machines/` | | new example needed? |
| `frontend/src/app/` (components / services / models) | | which folder? |
| `database/config/local.ini` or `init-db.sh` | | DB config change? |
| Document schema in CouchDB | | breaking? backward-compat? |
| `dc-plc-datalink-rfc1006-*.yml` | | compose change? |
| `**/dockerfile-*` | | image change? |
| `.github/workflows/` | | CI change? |
| `README.md` / OpenAPI | | docs update? |

### Phase 2 — Branch Decision (gated by user)
Ask via `AskUserQuestion`:
> "Create a feature branch (e.g. `feat/<kebab-name>`) or stay on `<current>`?"

If the user says yes:
- Check `git status` for uncommitted changes (warn/stash/abort if needed)
- Run `git checkout -b feat/<kebab-name>`

Never run `git checkout -b` without explicit user confirmation.

### Phase 3 — Write the Scope Note
Create `docs/features/<feature-name>/scope.md` using [template.md](template.md).

Include:
- Title and one-line summary
- Why (problem / motivation)
- In scope (bullet list)
- Out of scope (bullet list)
- Affected areas (the table from Phase 1)
- Acceptance criteria (checkboxes)
- Breaking changes & migration notes (or "none")
- Dependencies (other features, library bumps)

If `docs/features/` doesn't exist yet, create it.

### Phase 4 — User Review
Present the scope note for approval. Ask: "Does this accurately capture what you want? Anything missing or out of scope to call out?"

## Handoff
After approval:
> "Scope captured at `docs/features/<feature-name>/scope.md`. Next step:
> - Run `/architecture` if this involves a non-trivial design decision (new data type, schema change, new container, breaking API)
> - Otherwise jump straight to `/backend`, `/frontend`, or `/database` depending on where the work lives"

## Suggested Git Commit
```
docs(scope): add feature scope for <feature-name>
```

## Important
- NEVER write code, ADRs, or implementation artifacts in this skill
- NEVER run `git checkout -b` without explicit user confirmation
- Focus: WHY, WHAT, WHO — not HOW
- Keep scope notes short — this is a small project, not a banking system
