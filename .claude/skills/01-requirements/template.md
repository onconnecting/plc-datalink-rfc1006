# Feature Scope: [Feature Name]

**Status:** Scoped
**Created:** YYYY-MM-DD
**Branch:** feat/<kebab-name>

## Summary
_One sentence describing the change._

## Why
_What problem does this solve? Who asked for it?_

## In Scope
- [ ] Item 1
- [ ] Item 2

## Out of Scope
- Not covering X
- Not covering Y

## Affected Areas
| Area | Touched? | Notes |
|---|---|---|
| `backend/src/routes.py` | yes/no | … |
| `backend/src/plc_datalink_rfc1006_model.py` | yes/no | … |
| `backend/src/services/*` | yes/no | … |
| `backend/openapi/plc_datalink_rfc1006_api.yml` | yes/no | … |
| `backend/config/dynamic_startup_telegraf.sh` | yes/no | … |
| `frontend/src/app/` | yes/no | … |
| `database/config/*` | yes/no | … |
| CouchDB document schema | yes/no | … |
| `dc-plc-datalink-rfc1006-*.yml` | yes/no | … |
| `**/dockerfile-*` | yes/no | … |
| `.github/workflows/` | yes/no | … |
| `README.md` / OpenAPI | yes/no | … |

## Acceptance Criteria
- [ ] Criterion 1 (specific, verifiable, e.g. "GET /machine/state returns `{State: 'RUNNING'}` for a running machine")
- [ ] Criterion 2

## Edge Cases & Constraints
- What happens when the PLC is unreachable?
- What happens when CouchDB is unavailable?
- What happens to documents created before this change?

## Breaking Changes & Migration
_None / or list them with migration steps._

## Dependencies
_Other features, library bumps, infrastructure changes._

---
<!-- Filled in by later skills -->

## Architecture Decisions
_ADRs added by `/architecture` (link from `architecture/decisions/`)_

## QA Evidence
_Filled in by `/qa`_

## Operations Notes
_Filled in by `/operations` if operational behavior changes_
