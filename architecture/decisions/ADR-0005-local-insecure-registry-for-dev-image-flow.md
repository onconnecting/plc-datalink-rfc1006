# ADR-0005: Local Insecure Docker Registry for DEV Build-Push-Pull Loop

**Status:** Accepted
**Date:** 2026-05-15
**Scope:** [docs/features/dev-prod-split/scope.md](../../docs/features/dev-prod-split/scope.md)

## Context
The repo currently ships two Compose stacks:

- [`dc-plc-datalink-rfc1006-local.yml`](../../dc-plc-datalink-rfc1006-local.yml) — builds all three images from source and runs them in one step (`up -d --build`).
- [`dc-plc-datalink-rfc1006-acr.yml`](../../dc-plc-datalink-rfc1006-acr.yml) — pulls pre-built images from `onconnecting.azurecr.io` and runs them.

A `Makefile` wraps both with target shortcuts (`make build`, `make up`, `make build-acr`, etc.).

Two operational gaps prompt this decision:

1. **DEV behaves differently from PROD.** The local stack conflates "build" with "deploy". Registry-/tag-related defects (missing tag, wrong path, daemon misconfiguration, registry-auth issues) only show up in the ACR flow, i.e. in PROD, where they are the most expensive to find.
2. **PROD target is still undefined.** There is no committed PROD server, no PROD-only Compose file, no PROD tag strategy. Anything pre-empting PROD now is speculative work.

Additional constraints:

- DEV runs on a single internal host (`192.168.0.121`). DEV and PROD will not run on the same host simultaneously — there is no port or container-name conflict to solve.
- The user wants Compose called directly (not through a Makefile) so that the executed command is visible at the prompt and debuggable without a wrapper. See [feedback-tooling-compose-only memory](../../.claude/projects/-home-ofitz-plc-datalink-rfc1006/memory/feedback-tooling-compose-only.md) for the rationale.
- No outbound dependency on ACR for DEV: the loop must work even if the developer has no `az login`.

## Decision
1. **Introduce a self-hosted Docker registry on the DEV host.** A new Compose stack [`dc-registry-local.yml`](../../dc-registry-local.yml) runs `registry:2` listening on `192.168.0.121:5000`, with persistent storage in a named volume `plc-datalink-rfc1006-registry-data`. The registry is **insecure** (HTTP, no auth, no TLS) — acceptable because it is reachable only from the internal LAN, contains no production artefacts, and serves a single internal developer.

2. **Replace `dc-plc-datalink-rfc1006-local.yml` with `dc-plc-datalink-rfc1006-dev.yml`.** Each app service in the new file carries **both** an `image:` directive pointing at `192.168.0.121:5000/plc-datalink-rfc1006-{database,backend,frontend}:dev` **and** the existing `build:` block. This lets a single Compose file drive the full DEV loop:
   ```
   docker compose -f dc-plc-datalink-rfc1006-dev.yml build      # build, tag for local registry
   docker compose -f dc-plc-datalink-rfc1006-dev.yml push       # push to 192.168.0.121:5000
   docker compose -f dc-plc-datalink-rfc1006-dev.yml pull       # pull back from registry (proves the flow)
   docker compose -f dc-plc-datalink-rfc1006-dev.yml up -d --no-build
   ```

3. **Image-tag strategy for DEV: `dev` only.** Every build overwrites the same tag in the registry. No SHA-, branch-, or timestamp-suffixed tags. Rollback is by rebuilding from an older commit, not by selecting an older tag.

4. **Compose-only tooling — delete the Makefile.** Workflow commands live in the README as raw `docker compose` invocations. Backend `ruff` calls (formerly `make lint` / `make format`) move into the README's backend section.

5. **PROD scope is deferred.** [`dc-plc-datalink-rfc1006-acr.yml`](../../dc-plc-datalink-rfc1006-acr.yml) stays exactly as it is. No PROD-host decisions, no PROD tag strategy, no CI changes. A future ADR will record those once the PROD target is defined.

## Alternatives Considered
- **Option A — Keep `local.yml` as today, do nothing.**
  - Pros: Zero work.
  - Cons: DEV still differs from PROD in the failure modes that matter (registry, tags, daemon config). The original motivation — find these defects in DEV — is not addressed.

- **Option B — DEV pulls directly from ACR with a `dev` tag.**
  - Pros: One registry for the whole org; no new infrastructure on `192.168.0.121`.
  - Cons: Requires every developer to have ACR access, pollutes the production registry with experimental tags, and makes the DEV loop dependent on outbound network/auth to Azure. Defeats the "DEV works offline from ACR" constraint.

- **Option C — Local registry with self-signed TLS + auth.**
  - Pros: Closer to a production-grade registry; could be reused later for shared dev.
  - Cons: Substantial setup cost (cert generation, distribution, htpasswd, daemon `ca.crt` per host) for a single internal user on a single LAN host. Over-engineered for the actual threat model.

- **Option D — Local registry via hostname (`registry.local:5000`) instead of IP.**
  - Pros: Image references survive a server-IP change.
  - Cons: Requires every pulling host to maintain `/etc/hosts` or a DNS entry, with no current second host that benefits. The hardcoded IP is mitigated by an optional `LOCAL_REGISTRY` `.env` variable (see Consequences) without forcing a name-resolution layer.

- **Option E — Hybrid: source mounts / hot-reload in DEV.**
  - Pros: Faster inner loop, no rebuild on every change.
  - Cons: Requires dual-mode Dockerfiles (dev with mounts, prod without) and diverges DEV further from PROD — the opposite of the goal. Explicitly out of scope for this ADR.

- **Option F (chosen) — Local insecure registry + Compose with combined `image:` + `build:` + `dev` tag.**
  - Pros: DEV exercises the same `pull → up` mechanics as PROD, works offline from ACR, no auth/TLS overhead for the LAN-only use case, single Compose file for build + push + pull + run, no Makefile indirection.
  - Cons: Requires a one-time `/etc/docker/daemon.json` insecure-registry entry per pulling host; `dev` tag overwrite means the registry slowly accumulates orphaned layers (garbage-collect manually if needed).

- **Option G — Multi-tag strategy (`dev` + git-SHA or timestamp).**
  - Pros: Lets developers pin/rollback specific builds.
  - Cons: Adds tag-management ceremony without a current use case (no parallel DEV environments, no QA-vs-DEV pinning needs). Easy to introduce later if a need emerges.

## Consequences
**Positive**
- DEV exercises the same `image: → pull → up` mechanics that PROD will use, so registry/tag/daemon defects surface before they reach ACR.
- No ACR dependency for daily DEV work — `az login` is only needed to release to PROD.
- A single Compose file drives the whole DEV loop; no Makefile, no shell aliases, no per-developer scripts.
- The registry is process-isolated from the app stack — `docker compose -f dc-registry-local.yml down` stops the registry without touching the app, and vice versa. Different lifecycles, different files.
- Future ADR for PROD has a clean, narrowly scoped problem: "pick the PROD target and tag strategy", with the DEV loop already validated.

**Negative / Trade-offs**
- The DEV host carries new infrastructure (`registry:2`) and a named volume that must be managed (occasional `registry garbage-collect`, disk-usage monitoring). Operational cost is small but non-zero.
- `192.168.0.121:5000` is hardcoded in `image:` strings. Mitigation: introduce `LOCAL_REGISTRY` in `.env.example` so the address can be overridden without editing Compose files. If/when the DEV host moves, the Compose file does not need to change.
- One-time per-host setup: add `{"insecure-registries":["192.168.0.121:5000"]}` to `/etc/docker/daemon.json` and `systemctl restart docker`. Documented in README; no automation provided.
- Insecure registry on the LAN is a deliberate exposure decision. Acceptable for an internal dev environment but **must not** be reused for PROD or for any host outside the LAN. A future PROD ADR must re-decide registry security.
- Removing the Makefile breaks any IDE task/run-config that referenced `make` targets. Mitigated by README documentation of the equivalent `docker compose` commands.
- Convention "both compose files must stay in sync" in [.claude/rules/docker.md](../../.claude/rules/docker.md) now applies to **dev.yml + acr.yml** (not local.yml + acr.yml). The rule file is updated as a follow-up to this ADR.

**Migration / Compatibility**
- **External consumers (MQTT subscribers, REST clients, CouchDB doc readers):** no change. Payload, API, and schema are untouched.
- **PROD (ACR-based) deployments:** no change. `dc-plc-datalink-rfc1006-acr.yml` is byte-identical after this change.
- **CI (`.github/workflows/`):** no change. CI continues to build and push to ACR from `master`. The local registry is not involved in CI.
- **Existing developers:** `make`-based invocations stop working. README documents the replacement `docker compose` calls in the same change set. `make lint`/`make format` are replaced by direct `ruff check src test` / `ruff format src test` calls in `backend/`.
- **CouchDB data on `192.168.0.121`:** unaffected — volume `plc-datalink-rfc1006-database-data` keeps its name and mount path. Switching from `local.yml` to `dev.yml` does not touch data.
- **Coordination with [ADR-0004](ADR-0004-frontend-greenfield-migration-strategy.md):** the frontend-swap PR planned in ADR-0004 mentions updating `dc-plc-datalink-rfc1006-local.yml`. That file is being renamed/replaced by this ADR. The frontend swap-PR will instead update `dc-plc-datalink-rfc1006-dev.yml`, which is functionally equivalent. No semantic conflict; only a rename to track.

**Follow-ups required (out-of-scope for this ADR, in-scope for the implementation skills)**
- Update [.claude/rules/docker.md](../../.claude/rules/docker.md): replace the `local.yml` row in the compose-stacks table with `dev.yml` and note the registry stack; widen "both compose files must stay in sync" to cover `dev.yml` + `acr.yml`.
- Update [README.md](../../README.md): one-time daemon setup, the four-step `docker compose` loop, the registry start command, where the UI is reached (`http://192.168.0.121:80`), and the `ruff` replacement for `make lint`/`make format`.
- Add `LOCAL_REGISTRY=192.168.0.121:5000` to `.env.example`.
- Delete `dc-plc-datalink-rfc1006-local.yml` and `Makefile`.
- Append a CHANGELOG.md entry describing the tooling change.

## References
- Scope: [docs/features/dev-prod-split/scope.md](../../docs/features/dev-prod-split/scope.md)
- Convention to update: [.claude/rules/docker.md](../../.claude/rules/docker.md)
- Related ADR: [ADR-0004](ADR-0004-frontend-greenfield-migration-strategy.md) — frontend swap-PR will follow the dev.yml rename
- Compose stacks: [dc-plc-datalink-rfc1006-local.yml](../../dc-plc-datalink-rfc1006-local.yml) (to be removed), [dc-plc-datalink-rfc1006-acr.yml](../../dc-plc-datalink-rfc1006-acr.yml) (unchanged)
- Docker docs: <https://docs.docker.com/registry/insecure/>, <https://hub.docker.com/_/registry>
