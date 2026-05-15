# Feature Scopes

This directory holds short scope notes for non-trivial changes to the PLC Datalink RFC1006 project. Each feature gets its own folder:

```
docs/features/<feature-name>/
├── scope.md          # produced by /01-requirements
└── ...               # optional: notes, diagrams, QA evidence
```

## When to create a scope note
Create one when a change is non-trivial — adding a new endpoint, a new UI screen, a new PLC tag data type, a new container, or anything that affects the MQTT payload, REST API, or CouchDB document schema.

Skip scope notes for typo fixes, log-level tweaks, single-line bug fixes, or cosmetic refactors.

## Naming
`<kebab-case-feature-name>/scope.md` — short, descriptive, no version numbers.

## Workflow
Scope notes are produced by the `/01-requirements` skill and may be followed by `/02-architecture` if the change involves structural decisions worth recording as ADRs. See `.claude/rules/workflow.md`.
