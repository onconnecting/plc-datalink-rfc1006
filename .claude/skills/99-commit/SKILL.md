---
name: commit
description: Review git changes for the PLC Datalink RFC1006 project, update CHANGELOG.md, then ask for confirmation before committing. Always requires explicit user approval before running git commit.
argument-hint: "optional commit message or scope hint"
user-invocable: true
---

# Commit Assistant

## Role
You prepare a git commit for the user: inspect what changed, write a CHANGELOG entry, propose a commit message — and then **wait for explicit confirmation** before executing `git add` and `git commit`.

You NEVER commit without the user saying yes.

## Workflow

### Step 1: Inspect Changes

Run these commands in parallel to understand the current state:

```bash
git status
git diff --stat
git diff
git log --oneline -5
```

Read the output carefully:
- Which files were modified, added, or deleted? Which area do they belong to (backend / frontend / database / docker / docs)?
- What is the purpose of the changes? (new feature, fix, refactor, docs, ci, …)
- Are there any files that should NOT be committed? (`.env`, `backend/.venv/`, `*.key`, `certs/`)

### Step 2: Check for Secrets

```bash
git diff | grep -iE "(password|secret|api[_-]?key|token|private[_-]?key|BEGIN |COUCHDB_PASSWORD=|MQTT_PASSWORD=)" || echo "No secrets found"
```

If secrets are found: **STOP immediately**. Tell the user which file and line. Do NOT proceed.

The compose files contain the dev default `COUCHDB_PASSWORD=password` — that's known dev-only and may stay. Any other credential in the diff is a red flag.

### Step 3: Check Documentation Accuracy

If user-visible behavior changed (UI fields, REST endpoints, PLC address format, MQTT payload), `README.md` should reflect it. Quick check:

1. List what changed: `git diff --name-only`
2. If `backend/openapi/plc_datalink_rfc1006_api.yml` changed, confirm `README.md` API Definition section still matches
3. If `frontend/src/app/` changed, confirm the README screenshots/descriptions are still accurate (note in commit body if `images/` needs refreshing)

Update `README.md` with the Edit tool before staging if drift is found.

### Step 4: Update CHANGELOG.md

If `CHANGELOG.md` doesn't exist yet, create it with a [Keep a Changelog](https://keepachangelog.com/) style header.

1. Read the current `CHANGELOG.md`
2. Determine the correct section:
   - If a `## [Unreleased] — YYYY-MM-DD` block exists with today's date: add to it
   - If the existing block has an older date: insert a new `## [Unreleased] — YYYY-MM-DD` block above it with today's date
   - Always include the date — never write `## [Unreleased]` without a date
3. Write a concise changelog entry:
   - Use present-tense imperative ("Add", "Fix", "Update" — not "Added")
   - Group by type: `Added`, `Changed`, `Fixed`, `Removed`, `Security`
   - Reference file paths where relevant
4. Use the Edit tool to update `CHANGELOG.md` — do NOT skip this step

### Step 5: Propose Commit

Present a clear summary to the user:

---
**Changed files:**
```
<list from git status>
```

**CHANGELOG entry added:**
```
<the entry you wrote>
```

**Proposed commit message:**
```
type(area): short description (max 72 chars)

<optional body referencing scope note / ADR / issue>

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

**Files to stage:**
```
<list of files to git add — never .env, backend/.venv/, *.key, *.pem>
```

---

> **Please confirm:** Shall I run this commit? (yes / no / adjust)

### Step 6: Wait for Confirmation

**STOP HERE.** Do not run `git add` or `git commit` until the user explicitly confirms.

Accepted confirmations: "yes", "y", "ok", "do it", "commit", "ja", "j", "mach es"

If the user says "adjust" or requests changes: adjust the message or staged files, then show the updated proposal again and wait again.

If the user says "no" or "nein": abort. Do not commit anything.

### Step 7: Execute Commit (only after confirmation)

```bash
git add <specific files — never git add -A or git add .>
git commit -m "$(cat <<'EOF'
type(area): short description

<optional body>

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git status
```

After the commit: show the commit hash and summary.

## Commit Message Format

Follow `.claude/rules/git.md`. Keep the subject line under 72 characters — no bullet lists in the body.

```
type(area): short description
```

| Type | Use for |
|---|---|
| `feat` | new feature or capability |
| `fix` | bug fix or correction |
| `refactor` | restructuring without behavior change |
| `test` | adding or updating tests |
| `docs` | documentation only |
| `chore` | tooling, build, dependency bumps |
| `ci` | GitHub Actions, Dockerfile, supervisord, nginx |

Areas: `backend` · `frontend` · `database` · `telegraf` · `docker` · `api` · `ci` · `docs` · `architecture`

## Rules

- NEVER commit `.env` files, `backend/.venv/`, `certs/`, `*.key`, `*.pem`, `*.p12`, `*.jks`
- NEVER use `git add -A` or `git add .` — always stage specific files by name
- NEVER skip the confirmation step, even if the user seems impatient
- NEVER amend an existing commit — always create a new one
- NEVER use `--no-verify` unless the user explicitly requests it and explains why
- Always update `CHANGELOG.md` before committing
- If `git status` shows nothing to commit: tell the user and stop

## Safety Checks

Before proposing the commit, verify:
- [ ] No `.env` files in the staged list
- [ ] No `backend/.venv/` content in the staged list
- [ ] No `certs/` directory contents in the staged list
- [ ] No files matching `*.key`, `*.pem`, `*.p12`, `*.jks`
- [ ] No new credentials in the diff (beyond the dev-default `COUCHDB_PASSWORD=password` already in the compose files)
- [ ] `CHANGELOG.md` has been updated
- [ ] `README.md` is still accurate, or has been updated in the same change

If any check fails: **abort and tell the user**.
