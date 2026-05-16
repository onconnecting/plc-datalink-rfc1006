# Delivery Workflow

## Workflow Sequence
For new features or non-trivial changes:
```
/requirements → /architecture → /backend + /frontend + /database → /qa → /deploy → /operations → /commit
```

For quick fixes or small changes, skip directly to the relevant implementation skill (`/backend`, `/frontend`, or `/database`).

## Skill Map
| Skill | Purpose |
|---|---|
| `/help` | Tell me where I am and what to do next |
| `/requirements` | Scope a new feature or change (use case, acceptance criteria) |
| `/architecture` | Record significant design decisions as ADRs |
| `/backend` | Implement Python/Flask routes, services, models, OpenAPI changes, Telegraf integration |
| `/frontend` | Implement Angular components, services, models, modals |
| `/database` | Change CouchDB schema, config, or init scripts |
| `/qa` | Validate API (curl), UI (browser), and end-to-end PLC→MQTT flow |
| `/deploy` | Build and push images, deploy via docker-compose (local or ACR) |
| `/operations` | Container ops: logs, restart, supervisord, CouchDB backup, troubleshooting |
| `/commit` | Review changes, update CHANGELOG, propose and commit |

## Phase Gates
- For new features: never start implementation without a clear scope (at minimum a written acceptance criterion)
- Never skip QA before deploying to a shared environment
- Never proceed to the next phase without explicit user confirmation
- Any change to PLC address parsing, MQTT payload format, or REST API must be backward-compatible OR explicitly approved as a breaking change

## Handoffs Between Skills
- After completing a skill, suggest the next skill to the user
- Format: "Next step: Run `/skillname` to [action]"
- Handoffs are always user-initiated, never automatic
