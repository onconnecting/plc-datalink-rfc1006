# Architecture Decision Records (ADRs)

This directory holds Architecture Decision Records for the PLC Datalink RFC1006 project. ADRs capture **why** a structural decision was made — they are *not* general documentation and should not duplicate code or README content.

## When to write an ADR
Write an ADR when a change is structural and hard to reverse, for example:
- A new container or external dependency
- A change to the REST API surface
- A change to the CouchDB document schema or MQTT payload shape
- A change to the PLC address parser
- A new data type, build system, or framework choice

Skip ADRs for refactors, bug fixes, dependency bumps, or cosmetic changes.

## Naming
`ADR-XXXX-<short-kebab-title>.md`, with a four-digit number incrementing from `0001`.

## Template
Copy [`ADR-0000-template.md`](ADR-0000-template.md) and bump the number.

## Workflow
ADRs are typically created by the `/02-architecture` skill after `/01-requirements` has produced a scope note. See `.claude/rules/workflow.md`.
