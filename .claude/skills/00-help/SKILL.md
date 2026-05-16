---
name: help
description: Context-aware guide for the PLC Datalink RFC1006 project. Tells you where you are, what's changed, and what to do next.
argument-hint: "optional question"
user-invocable: true
---

# Project Help Guide

You are a helpful assistant for the **PLC Datalink RFC1006** project — a Telegraf-based gateway that reads S7 PLC data points over RFC1006 and publishes them to MQTT, configured via an Angular UI backed by a Flask API and CouchDB.

## When Invoked

### Step 1: Read the Current State

Run these in parallel:
1. `git status` and `git log --oneline -5` — uncommitted work and recent history
2. `ls backend/src/ backend/src/services/` — backend layout
3. `ls frontend/src/app/` — frontend layout
4. `ls database/config/` — database config
5. `ls .github/workflows/` — CI status (if present)
6. If `docs/features/` exists: `ls docs/features/` to see in-flight feature scopes
7. If `architecture/decisions/` exists: `ls architecture/decisions/` to see ADRs

### Step 2: Determine What the User Likely Needs

**If the user asked a "where am I / what next" question:**
- Summarize current branch, recent commits, and any uncommitted changes
- Point to the next reasonable skill

**If the user described a change they want to make:**

| Type of change | Suggested skill |
|---|---|
| New feature, breaking API change, new container | `/requirements` then `/architecture` |
| Significant design decision | `/architecture` |
| New endpoint, service change, Telegraf integration | `/backend` |
| New UI screen, form, list, modal | `/frontend` |
| CouchDB schema, config, or init change | `/database` |
| Validating a change before shipping | `/qa` |
| Build / push / pull images, run the stack | `/deploy` |
| Container logs, restart, supervisord, backup, troubleshooting | `/operations` |
| Wrapping up work for a commit | `/commit` |

### Step 3: Answer Common Questions

- "What skills are available?" → list the table below
- "How do I add a new PLC tag type?" → `/backend` (parser/model) + `/frontend` (form validation) + update README
- "How do I add a new endpoint?" → `/backend` (route + OpenAPI) + `/frontend` (service) + curl test in `backend/test/`
- "How do I deploy this?" → see `/deploy`; local uses `dc-plc-datalink-rfc1006-local.yml`, production pulls from ACR via `dc-plc-datalink-rfc1006-acr.yml`
- "Where are the screenshots in the README from?" → `images/image-{0..4}.png`

## Output Format

Always respond with this structure:

### Current Project Status
_One line on branch + uncommitted work + recent commit_

### Where Things Live
_Brief pointer to the relevant area (backend / frontend / database / docker)_

### Recommended Next Step
_The single most important thing to do next, with the exact command_

### Available Skills

| Skill | Command | When to Use |
|-------|---------|-------------|
| Help | `/help` | This guide |
| Requirements | `/requirements` | Scope a non-trivial feature or change |
| Architecture | `/architecture` | Record a structural design decision (ADR) |
| Backend | `/backend` | Python/Flask routes, services, models, OpenAPI, Telegraf integration |
| Frontend | `/frontend` | Angular components, services, models, modals |
| Database | `/database` | CouchDB schema, config, init script changes |
| QA | `/qa` | Validate API with curl, UI in browser, PLC→MQTT end-to-end |
| Deploy | `/deploy` | Build / push / pull images, run docker-compose |
| Operations | `/operations` | Container logs, restart, supervisord, CouchDB backup |
| Commit | `/commit` | Review changes, update CHANGELOG, commit with confirmation |

## Important
- Be concise and actionable
- Always give the exact command to run
- Reference specific file paths from the project tree
- Focus on: "Here's where you are, here's what to do next"
