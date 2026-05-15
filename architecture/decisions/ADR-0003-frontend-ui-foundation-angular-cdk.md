# ADR-0003: Frontend UI Foundation on @angular/cdk (no Bootstrap, Material, or Tailwind)

**Status:** Accepted
**Date:** 2026-05-15
**Scope:** [docs/features/frontend-ci-rewrite/scope.md](../../docs/features/frontend-ci-rewrite/scope.md)

## Context
The existing frontend (`frontend/`, Angular 17.3) is styled with **Bootstrap 3.4.1**. Bootstrap 3 is end-of-life, its visual defaults (pill radii, blue palette, condensed grid) collide with the binding onconnecting Corporate Identity ([`docs/design/onconnecting-ci/ci-manual_onconnecting.md`](../../docs/design/onconnecting-ci/ci-manual_onconnecting.md), v1.5), and component-level CSS in the current codebase routinely overrides Bootstrap with hard-coded hex/rgb values (e.g. `rgb(35, 142, 168)`). The result is two competing visual systems — Bootstrap's and onconnecting's — fighting each other in every template.

The frontend CI-rewrite ([scope](../../docs/features/frontend-ci-rewrite/scope.md)) commits to:

- Slate/Cyan palette driven entirely by CSS custom properties (`--color-*`, `--space-*`, `--radius-*`)
- Two-font system: Consolas for headlines/labels/PLC values, Calibri Light for body
- Sharp edges or minimal radii (max `--radius-lg` = 8 px)
- Headlines never bold, never centered
- No emojis, no exclamation chains, German UI tonality

A UI framework whose own defaults override these tokens is therefore a liability, not a help. We still need primitives that are hard to get right without a library: focus-trapped dialogs, accessible overlays/portals, ARIA-live regions for toasts, keyboard-navigable menus.

The constraint from [`.claude/rules/frontend.md`](../../.claude/rules/frontend.md) is explicit: *"Keine neuen npm-Pakete ohne explizite Freigabe — insbesondere keine UI-Frameworks (Material, Bootstrap, PrimeNG), die das CI überschreiben würden. Wenn ein UI-Helper nötig ist: ADR via `/architecture`."* This ADR is that gate.

## Decision
Build the onconnecting UI components (`oc-button`, `oc-input`, `oc-field`, `oc-table`, `oc-card`, `oc-toast`, `oc-dialog`, `oc-status-pill`) **directly on `@angular/cdk@19`** — using only its unstyled behavior primitives (`Dialog`, `Overlay`, `Portal`, `A11yModule`, `LiveAnnouncer`) — and reject Bootstrap, Angular Material, PrimeNG, and Tailwind for the rewrite.

Visual styling is owned 100 % by the project: every color, radius, spacing, and font reference comes from the CI tokens defined in `frontend-next/src/styles.css` / `_tokens.css`. No theme file from a third-party library is loaded.

## Alternatives Considered
- **Option A — Keep Bootstrap (any version) and theme it.**
  - Pros: Smallest diff; familiar grid utilities.
  - Cons: Bootstrap's component CSS (alerts, modals, buttons, form-control radii) ships its own opinions and must be overridden everywhere; we already proved this fails (`rgb(35, 142, 168)` hard-codes scattered across the legacy templates). Bootstrap 3 is EOL; Bootstrap 5 still ships a non-trivial CSS theme we'd actively fight. Stylelint rule "no raw hex outside `_tokens.css`" cannot coexist cleanly with a Bootstrap theme override layer.

- **Option B — Angular Material.**
  - Pros: First-party Angular components with strong a11y and a documented theming API; native Signals-aware in v19.
  - Cons: Material Design is a *visual* system, not just a behavioral one — its elevation/shadow, ripple, and rounded-corner aesthetics directly contradict the onconnecting CI ("scharfe Kanten oder minimaler Radius", "keine Schlagschatten"). Re-skinning Material to neutralize Material — possible in principle — produces a fragile theme that breaks on every minor version. The cost of fighting defaults outweighs the components we'd actually use.

- **Option C — Tailwind CSS (with or without a headless component kit).**
  - Pros: Utility-first, no opinionated component styling, easy to map design tokens.
  - Cons: Tailwind's value proposition is utilities-in-templates, which collides with the project's existing convention of token-driven component CSS (CI § Component CSS, see [.claude/rules/frontend.md](../../.claude/rules/frontend.md)). It also brings a build-time tooling layer (PostCSS pipeline, JIT scanner) we don't otherwise need, and the tokens would live in `tailwind.config.js` instead of CSS custom properties — duplicating the CI-mandated `--color-*` variables. Net: extra surface for no behavioral gain.

- **Option D — `@angular/cdk` only, with hand-written components (chosen).**
  - Pros: CDK gives us the hard parts (Overlay positioning, Focus-trap, LiveAnnouncer, Portal, keyboard managers) without shipping any visual style. We own every pixel via CI tokens. Stylelint "no raw hex" rule is trivially enforceable because there is no vendor stylesheet to exempt. Bundle size stays small (CDK primitives are tree-shakable).
  - Cons: We hand-write `oc-button`, `oc-input`, etc. — initial implementation cost is real (a handful of components). Maintenance falls on us. Accepted because (a) the component surface is small and stable, (b) CDK absorbs the genuinely difficult parts, and (c) every other option produced a worse outcome on either CI fidelity or maintenance.

## Consequences
**Positive**
- One source of visual truth: CI tokens. No vendor stylesheet to override or sync with major versions.
- Stylelint rule "no raw hex/rgb outside `_tokens.css`" becomes enforceable as a hard CI gate (see scope acceptance criterion).
- Accessibility primitives (focus trap, ARIA-live, overlay) are still industrial-grade thanks to CDK.
- Bundle stays lean: no Bootstrap CSS, no Material theme CSS, no Tailwind JIT runtime.
- Sharp-edge / no-shadow CI rules are easy to enforce because there is no library default to fight.

**Negative / Trade-offs**
- Initial implementation effort for `oc-*` components is non-zero (estimated handful of files; tracked under the scope acceptance criteria).
- No drop-in datepicker, tree, autocomplete, etc. — if such a need surfaces later, a new ADR is required to evaluate adding a CDK-derived community kit or building it in-house.
- Onboarding cost for contributors who expect Material/Bootstrap conventions; mitigated by the existing CI manual and `.claude/rules/frontend.md`.

**Migration / Compatibility**
- Applies to the **new** `frontend-next/` project only. The legacy `frontend/` (Angular 17.3 + Bootstrap) remains baubar until the swap PR described in [ADR-0004](ADR-0004-frontend-greenfield-migration-strategy.md).
- No runtime, API, or data-schema impact. CouchDB schema, MQTT payloads, REST routes, PLC address format — all untouched.
- `.claude/rules/frontend.md` already names this rule; this ADR is referenced from there so the rule has a traceable origin.

## References
- Scope: [docs/features/frontend-ci-rewrite/scope.md](../../docs/features/frontend-ci-rewrite/scope.md)
- Related ADR: [ADR-0004](ADR-0004-frontend-greenfield-migration-strategy.md) — Greenfield migration strategy
- Convention: [.claude/rules/frontend.md](../../.claude/rules/frontend.md) — CI tokens, no-new-UI-framework rule
- CI Manual: [docs/design/onconnecting-ci/ci-manual_onconnecting.md](../../docs/design/onconnecting-ci/ci-manual_onconnecting.md)
- Angular CDK: https://material.angular.io/cdk/categories
