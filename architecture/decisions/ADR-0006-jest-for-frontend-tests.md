# ADR-0006: Jest as the Test Framework for the Angular 19 Frontend

**Status:** Accepted
**Date:** 2026-05-15
**Scope:** [docs/features/test-strategy/scope.md](../../docs/features/test-strategy/scope.md)

## Context
The greenfield Angular 19 frontend created under [ADR-0004](ADR-0004-frontend-greenfield-migration-strategy.md) ships **without any test framework**. [`frontend/angular.json`](../../frontend/angular.json) sets `schematics.skipTests: true` for components, directives, and pipes, so newly generated artefacts come with no spec at all. There are zero `.spec.ts` files in [`frontend/src/`](../../frontend/src/).

The [test-strategy scope](../../docs/features/test-strategy/scope.md) requires a baseline test suite per Angular layer (component, service, validator) plus a smoke test on `AppComponent`. To get there a test framework must be chosen and wired in once — the choice then affects every spec written from this point on.

Three viable options exist for an Angular 19 project in May 2026:

- **Karma + Jasmine** — the historic Angular default. Officially in maintenance mode; the Angular team has signalled a move away from Karma in upcoming majors. Browser-based runner, slow startup, no native ESM, configuration is non-trivial.
- **Jest** (via `jest-preset-angular`) — the de-facto community standard for Angular unit tests. Node-based (jsdom), fast watch mode, large mock/snapshot ecosystem. Not officially blessed by the Angular team but well-supported by the community and stable across Angular majors.
- **Vitest** — fast, ESM-native, conceptually closest to where the Angular team is moving. Angular support is still experimental in v19 (no first-party builder, community packages only).

Internal constraints from [`.claude/rules/frontend.md`](../../.claude/rules/frontend.md): no new npm packages without explicit approval, no UI frameworks that override the CI tokens. A test framework is not a UI framework, so the gate is "ADR + user approval" rather than refusal.

## Decision
Use **Jest** with **`jest-preset-angular`** as the unit/integration test framework for the frontend.

Concrete commitments:

1. Add dev dependencies `jest`, `jest-preset-angular`, `@types/jest`, `jest-environment-jsdom`. No other test-related npm packages.
2. Create `frontend/jest.config.ts`, `frontend/setup-jest.ts`, and `frontend/tsconfig.spec.json` (with `types: ["jest"]`).
3. Add scripts to [`frontend/package.json`](../../frontend/package.json): `test`, `test:watch`, `test:ci`. The `ng test` Karma builder is **not** wired up.
4. Flip [`frontend/angular.json`](../../frontend/angular.json) schematics `skipTests` to `false` for `@schematics/angular:component | directive | pipe` so every generated artefact gets a `.spec.ts`.
5. No coverage gate. Coverage may be reported but is not a CI failure criterion.

## Alternatives Considered
- **Option A — Karma + Jasmine.** Closest to Angular's historical default, comes pre-wired when `ng new` is invoked without `--skip-tests`.
  - Pros: zero-effort initial setup; team-familiar API; works out of the box.
  - Cons: maintenance mode, slow startup (~5–10 s warm-up), browser dependency complicates headless CI, and the Angular team has stated intent to deprecate. Locking new specs into a dying runner is a needless migration debt.

- **Option B — Vitest.** Modern, ESM-native, very fast.
  - Pros: speed, native ESM, aligned with where the wider JS ecosystem is moving.
  - Cons: Angular 19 has **no first-party Vitest builder**. Community packages (`@analogjs/vitest-angular`) exist but are bleeding edge and rev with breaking changes. Choosing it now means committing to ad-hoc migration work on every Angular minor.

- **Option C — Jest (chosen).** Node/jsdom-based, fast watch mode, broad community.
  - Pros: mature preset for Angular (`jest-preset-angular`), large mock/snapshot/expect API, fast cold and warm runs, no browser process. Same test framework concept that most other recent Angular projects in the wider ecosystem use. CI integration is trivial (single `npm test` invocation, exit-code driven).
  - Cons: not officially Angular-blessed; the preset abstracts a non-trivial transformer (`ng-jest-preset`) that occasionally needs version-pinning against new Angular majors. Adds ~80 MB to `node_modules`. jsdom is not a real browser — visual or layout-sensitive tests still need a Cypress/Playwright pass (deliberately out of scope, see [test-strategy/scope.md](../../docs/features/test-strategy/scope.md)).

## Consequences

**Positive**
- One `npm test` invocation runs the whole suite, fast cold-start, fast watch mode — enables the PostToolUse hook in [ADR-0007](ADR-0007-post-tool-use-hooks-test-auto-run.md) to stay under its ~3 s budget for focused test runs.
- Every generated component/directive/pipe ships with a spec, removing the "I forgot to write a test" failure mode.
- Migrating to Vitest later is feasible — Jest and Vitest share the bulk of their API surface — should Angular's first-party stance change.

**Negative / Trade-offs**
- Jest is not endorsed by the Angular team; we accept the risk that a future Angular major breaks `jest-preset-angular` until it catches up.
- jsdom diverges from real browser behaviour for some APIs (e.g., `ResizeObserver`, layout). Tests that need real layout must explicitly opt out of unit-testing and live in a future Cypress/Playwright pass.
- Adds ~80 MB to `node_modules` and lengthens `npm ci` by a few seconds.

**Migration / Compatibility**
- No existing tests to migrate. The decision is forward-only.
- The legacy Karma config does **not** exist (greenfield), so there is nothing to remove.
- All future-generated artefacts include a spec automatically — no manual cleanup needed.

## References
- Related ADRs: [ADR-0003](ADR-0003-frontend-ui-foundation-angular-cdk.md) (CDK-only UI foundation), [ADR-0004](ADR-0004-frontend-greenfield-migration-strategy.md) (greenfield migration), [ADR-0007](ADR-0007-post-tool-use-hooks-test-auto-run.md) (test auto-run hooks)
- Related scope: [docs/features/test-strategy/scope.md](../../docs/features/test-strategy/scope.md)
- External: [`jest-preset-angular` docs](https://thymikee.github.io/jest-preset-angular/), [Angular team note on Karma maintenance](https://blog.angular.dev/moving-angular-cli-to-jest-and-web-test-runner-ef85ef69ceca)
