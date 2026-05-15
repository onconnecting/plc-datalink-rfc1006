# ADR-0004: Frontend Greenfield Migration via `frontend-next/` with Directory Swap

**Status:** Accepted
**Date:** 2026-05-15
**Scope:** [docs/features/frontend-ci-rewrite/scope.md](../../docs/features/frontend-ci-rewrite/scope.md)

## Context
The frontend CI-rewrite ([scope](../../docs/features/frontend-ci-rewrite/scope.md)) is not a styling pass. The legacy `frontend/` (Angular 17.3) is built on architectural choices that are no longer current and that compound on every touched file:

- Legacy NgModule architecture (`AppModule` aggregates everything; no standalone components)
- `HttpClientModule` and constructor-DI throughout — superseded by `provideHttpClient()` and `inject()` since Angular 17
- Default change detection; no Signals
- `Observable.subscribe(next, error)` two-argument callbacks (deprecated)
- Bootstrap 3.4.1 (EOL) intertwined with templates
- Hard-coded hex/rgb values, English labels, emojis in toasts (`✓`, `⚠️`)
- `BackendRequestService` returns `any`; PLC-address validation lives in templates rather than reusable validators

In addition, the rewrite changes language (English → German UI), tonality (CI manual), brand identity (Bootstrap-default → onconnecting logo), component model (NgModule → standalone), DI style, control flow, form typing, and visual system. Every file touched would have to be rewritten more or less in full.

Two orthogonal questions need a decision:

1. **In-place rewrite vs. greenfield parallel project** — how to land the change without breaking the running stack.
2. **How to ship the final swap** — once the new code is green, how does it become `frontend/`?

## Decision
1. **Build the new frontend as a parallel, greenfield project at `frontend-next/`.** It is a brand-new Angular 19 LTS app generated from scratch, not a clone of `frontend/`. Models, service signatures, route paths, and acceptance criteria are copied; code is not. The legacy `frontend/` stays in the tree and remains baubar throughout the rewrite branch.

2. **CI runs both projects in parallel** until the swap. A second matrix entry / job in [`.github/workflows/`](../../.github/workflows/) builds `frontend-next/` (Production build + lint) on every push; it does **not** push images to ACR. The existing `frontend/` job continues to gate the release stack.

3. **Cut over with a small, separate "swap PR".** Once `frontend-next/` meets every scope acceptance criterion and is reviewed:
   - Delete or archive the legacy `frontend/` directory.
   - Rename `frontend-next/` → `frontend/` (the directory rename is the swap).
   - Update [`dc-plc-datalink-rfc1006-local.yml`](../../dc-plc-datalink-rfc1006-local.yml), [`dc-plc-datalink-rfc1006-acr.yml`](../../dc-plc-datalink-rfc1006-acr.yml), and the `.github/workflows/` job names to point at the new directory only.
   - This PR is intentionally small (mostly moves/renames + compose/CI line edits) so review is fast and rollback is one revert.

4. **No backward-compatibility shim, no parallel deployment.** The production image still maps to a single frontend container; the swap PR replaces its source directory in one commit.

## Alternatives Considered
- **Option A — In-place rewrite on `frontend/`.**
  - Pros: One directory, no rename ceremony.
  - Cons: Every commit on the rewrite branch breaks the running build for everyone else; the existing ACR pipeline either has to skip the directory or fail constantly; reviewers cannot diff "legacy vs. new" because the legacy is gone after the first big commit. Worst on collaboration, worst on rollback, worst on review hygiene.

- **Option B — Greenfield in `frontend-next/`, then deploy *both* simultaneously under different paths/ports.**
  - Pros: Lets users compare side-by-side; ultra-safe migration.
  - Cons: Requires nginx routing changes, two containers, two ACR tags, two CI jobs in steady state, and a deprecation campaign. Way over-engineered for a small internal tool with no external users to migrate. Adds the operational burden we're explicitly trying to avoid.

- **Option C — Greenfield in `frontend-next/`, swap by directory rename (chosen).**
  - Pros: Legacy stays buildable until cutover; CI gates both during the transition; the swap PR is mechanically small and easy to review/revert; consumers see exactly one moment of change (the merge of the swap PR); no double-deploy footprint.
  - Cons: Two directories live in the tree during development — contributors must know which one is "live" (mitigated: `frontend/` stays the deployed one until the swap PR merges; the rewrite branch is the only place `frontend-next/` exists).

- **Option D — Branch with `frontend/` removed and replaced from day 1.**
  - Pros: Cleanest end state in fewest commits.
  - Cons: Removes the ability to compare against the legacy implementation while developing, and means the rewrite branch can't share CI matrix runs with main. Equivalent to Option A from an operational standpoint.

## Consequences
**Positive**
- Legacy `frontend/` keeps the production stack buildable throughout the rewrite — `dc-plc-datalink-rfc1006-acr.yml` and the local stack remain runnable on main and on the rewrite branch.
- The swap is a single, mechanical, reviewable PR — directory rename plus three or four line edits to compose/CI files.
- Rollback is `git revert <swap-PR>` and a redeploy — no data migration, no schema concerns.
- Both implementations are buildable side-by-side, so reviewers can A/B screens during the QA phase.

**Negative / Trade-offs**
- Two frontend directories coexist on the rewrite branch. Risk of contributors editing the wrong one is mitigated by the convention "legacy is `frontend/`, new work lives in `frontend-next/` until swap".
- CI runs two frontend jobs in parallel for the duration of the branch — small extra cost (≈ one Node build per push).
- The repo briefly contains the rewrite under a non-canonical name (`frontend-next/`). Tooling that scans `frontend/` only (e.g. IDE workspace settings) needs awareness during the transition; the swap PR restores the canonical path.

**Migration / Compatibility**
- **API / MQTT / CouchDB schema:** no change. Scope explicitly forbids contract changes.
- **Container layout:** unchanged — still a single frontend image served by nginx on port 80. The swap PR updates compose `build.context` from `./frontend` (legacy code, soon-to-be-removed) to either the new `./frontend` (post-rename) or a temporary `./frontend-next` if a multi-step rename is preferred.
- **ACR image tag:** unchanged. The image content changes; the tag and pull path do not.
- **Local dev:** during the rewrite branch, `npm install && npm run build` in `frontend-next/` for the new UI; `frontend/` remains the deployed UI until the swap PR.
- **Backout plan:** if the swap PR is reverted, the legacy `frontend/` directory comes back (it is preserved in git history) and the previous compose/CI lines are restored in the same revert.

## References
- Scope: [docs/features/frontend-ci-rewrite/scope.md](../../docs/features/frontend-ci-rewrite/scope.md)
- Related ADR: [ADR-0003](ADR-0003-frontend-ui-foundation-angular-cdk.md) — UI foundation on `@angular/cdk`
- Convention: [.claude/rules/frontend.md](../../.claude/rules/frontend.md) — frontend layout and CI rules
- Compose stacks: [dc-plc-datalink-rfc1006-local.yml](../../dc-plc-datalink-rfc1006-local.yml), [dc-plc-datalink-rfc1006-acr.yml](../../dc-plc-datalink-rfc1006-acr.yml)
- CI workflows: [.github/workflows/](../../.github/workflows/)
