# ADR-0007: PostToolUse Hooks Trigger Layer-Specific Tests After Edits

**Status:** Accepted
**Date:** 2026-05-15
**Scope:** [docs/features/test-strategy/scope.md](../../docs/features/test-strategy/scope.md)

## Context
The [test-strategy scope](../../docs/features/test-strategy/scope.md) requires that whenever code in one of the three application layers is touched, the corresponding test suite runs. Two enforcement mechanisms are available in this repo:

1. **Skill instructions** — append a "run tests after edits" step to [`.claude/skills/03-backend/SKILL.md`](../../.claude/skills/03-backend/SKILL.md), `04-frontend`, `05-database`. Claude executes the step when (and only when) the skill is invoked. Easy to author, but soft: any work that bypasses the skill (a direct Edit call, a forgetting model, a context-compacted run that drops the skill) also bypasses the tests.

2. **Harness hooks** — register PostToolUse hooks in [`.claude/settings.json`](../../.claude/settings.json) that match `Edit`/`Write` calls under specific paths and run the relevant test command. The harness executes hooks unconditionally; the model cannot skip them.

The two are not mutually exclusive. The choice is whether to commit to one, the other, or both.

Adjacent constraints:

- The repository already declares its allowed Bash commands in `.claude/settings.json` (`Bash(npm test:*)`, `Bash(ng test:*)`, and `Bash(docker compose:*)` are present today).
- A PostToolUse hook adds wall-clock latency to every matching Edit/Write. Long hooks make iterative work slow; the [scope](../../docs/features/test-strategy/scope.md) targets ~3 s per fired hook by running pytest/jest on the **changed module path** rather than the full suite.
- The model's responsibility to read and act on test output is preserved either way — hooks emit the test result, and Claude is expected to react.

## Decision
Use **both mechanisms in parallel**, with a clear division of responsibility:

1. **Skill instructions (process discipline).**
   Append a final step to each of `/03-backend`, `/04-frontend`, `/05-database` that says "after edits, run the layer-specific test command, report pass/fail in the chat, and proceed only if green or with explicit user confirmation". `/06-qa` is updated to reference the E2E test as part of the QA pass.

2. **PostToolUse hooks (runtime enforcement).**
   Register hooks in `.claude/settings.json` that fire on `Edit` and `Write` tool calls and execute the matching test command:

   | Path pattern matched | Command |
   |---|---|
   | `backend/src/**` | `cd backend && pytest -q <relevant test path>` |
   | `frontend/src/**` | `cd frontend && npm test -- --findRelatedTests <changed file>` |
   | `database/config/**` | `cd database && pytest -q test/python` |

   Hook behaviour:
   - **Advisory, not blocking.** A non-zero exit from the hook does **not** abort the originating Edit/Write — the failure is surfaced back to the model in the tool result, and Claude is responsible for addressing it before continuing.
   - **Focused.** Hooks run only the tests related to the changed file (`pytest <file>`, `jest --findRelatedTests <file>`), not the full suite, to stay within ~3 s.
   - **Idempotent.** A hook may fire multiple times in one task (every Edit/Write); the test command must tolerate being invoked while the prior run is still active in cache.

3. **Permissions.** Add `Bash(pytest:*)`, `Bash(cd backend && pytest:*)`, `Bash(cd frontend && npm test:*)`, `Bash(cd database && pytest:*)` to the allow-list in `.claude/settings.json`.

## Alternatives Considered
- **Option A — Skill instructions only.**
  - Pros: zero harness configuration, easy to read and modify, all logic lives in the skill markdown.
  - Cons: relies entirely on the model invoking the skill. Any direct `Edit` call outside a skill (which is common in mid-task pivots and after context compaction) skips the tests silently. The whole point of "tests after every change" is undermined.

- **Option B — PostToolUse hooks only.**
  - Pros: bulletproof — every `Edit`/`Write` on a matched path runs the suite, regardless of how Claude got there.
  - Cons: the skill text drifts away from reality (skill says nothing about tests; the harness silently runs them). New contributors and reviewers reading the skill have no idea the testing step exists. Bug-prone over time as `.claude/settings.json` and the skills diverge.

- **Option C — Both, advisory hooks (chosen).**
  - Pros: durable redundancy. Skill text stays the contract; hooks are the enforcement. The advisory mode preserves Claude's ability to fix follow-up issues (e.g., update the spec when intentionally renaming a function) without the harness aborting the chain mid-task.
  - Cons: two places to keep in sync when the test commands change. Slight per-Edit latency (~1–3 s) on every matching file. The model could in principle ignore a hook failure — mitigated by explicit instruction in each skill to surface and address hook results.

- **Option D — Both, blocking hooks (rejected).**
  - Pros: strictest possible enforcement; nothing proceeds with a red test.
  - Cons: a refactor that intentionally edits multiple files before fixing the spec is impossible — the first Edit aborts because the spec is now temporarily red. Forces unnatural micro-commits and makes multi-file changes painful. Strictness wins on paper, loses in practice.

## Consequences

**Positive**
- Tests run after every relevant change, whether the model invokes a skill or not.
- The skill markdown stays the human-readable source of truth for the workflow.
- Hook failures are loud (the tool result carries them) but recoverable — the model can fix forward.
- Same test commands work locally and in CI, so the future CI port is mostly a copy-paste of the hook command lines.

**Negative / Trade-offs**
- Per-Edit latency on matched paths. A `pytest <single test file>` invocation in this codebase is ~1.5–2.5 s warm. Acceptable but noticeable.
- Two enforcement points to keep in sync (skill + settings). Documented in [`.claude/rules/process.md`](../../.claude/rules/process.md) follow-up to flag drift.
- Permissions list grows. Specific entries are preferable to wildcards (`Bash(pytest:*)` rather than `Bash(*)`) to keep the security posture tight.

**Migration / Compatibility**
- No code migration. The hooks fire on edits made after their introduction.
- Existing manual test scripts (`backend/test/curl/*.sh`, `database/test/*.sh`) remain — they are out of the hook's path filter and continue to be invoked manually.
- If hook latency becomes a problem in practice, the focused-test pattern (`pytest <path>`, `jest --findRelatedTests`) can be tightened further, or hooks can be moved to a less-frequent trigger (e.g., on Bash(`git add`) rather than Edit/Write).

## References
- Related ADRs: [ADR-0006](ADR-0006-jest-for-frontend-tests.md) (Jest as the FE test runner — its speed is a prerequisite for this hook strategy), [ADR-0008](ADR-0008-testcontainers-couchdb-integration-tests.md) (DB test runner)
- Related scope: [docs/features/test-strategy/scope.md](../../docs/features/test-strategy/scope.md)
- External: [Claude Code hooks reference](https://docs.claude.com/en/docs/claude-code/hooks)
