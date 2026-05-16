# Frontend Implementation Checklist

## Before Starting
- [ ] Scope note read (`docs/features/<name>/scope.md`) if applicable
- [ ] Relevant ADRs read (`architecture/decisions/`) if applicable
- [ ] `.claude/rules/frontend.md` re-read for conventions
- [ ] Existing components / services / models inspected to avoid duplication
- [ ] Backend endpoints to be consumed verified in OpenAPI spec

## Components
- [ ] New or modified component lives in the right feature directory (`create-configuration`, `configuration-overview`, `plc-states`, `header`, `modals`)
- [ ] Component has `.ts`, `.html`, `.css`, and (if non-trivial) `.spec.ts`
- [ ] Registered in `app.module.ts` (or its owning module) if newly created
- [ ] Template stays declarative — no business logic inline

## Services
- [ ] Backend calls go through a service (no `HttpClient` calls in components)
- [ ] URLs are relative (`/config/...`, `/machine/...`) — nginx serves on the same origin
- [ ] Methods return `Observable<T>` typed against an interface in `models/`
- [ ] Error responses surface a useful message to the user

## Models (`frontend/src/app/models/`)
- [ ] Field names mirror backend JSON exactly (camelCase)
- [ ] Optional fields marked with `?` only where the backend may omit them
- [ ] If the backend model changed, the TypeScript model was updated in the same commit

## Validation
- [ ] PLC IP / MQTT IP validated as IPv4
- [ ] Port fields validated as 1–65535
- [ ] PLC address validated against `<area>.<type><address>[.extra]`
- [ ] Required-field errors surface in the UI before submission

## nginx (if applicable)
- [ ] `nginx-custom.conf` proxies match real backend routes (no wildcards covering missing routes)
- [ ] No new locations without confirming backend support

## Verification
- [ ] `docker-compose -f dc-plc-datalink-rfc1006-local.yml build plc-datalink-rfc1006-frontend` succeeds
- [ ] Stack starts and the UI loads at `http://localhost`
- [ ] Golden path exercised in a Chromium-based browser
- [ ] At least one failure path tested (invalid input, conflict response, network error)
- [ ] No console errors in devtools

## Documentation
- [ ] `README.md` updated if user-visible behavior changed (new field, button, flow)
- [ ] CHANGELOG.md updated (when `/commit` runs)
- [ ] Note in commit body if a screenshot in `images/` is now stale

## Dependencies
- [ ] No new npm package added without explicit user approval
- [ ] If a package was added, `frontend/Dockerfile` build still succeeds
