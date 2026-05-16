# QA Evidence: <Feature Name>

**Tested:** YYYY-MM-DD
**Environment:** local | acr-staging | acr-prod
**Tester:** QA Engineer (AI)
**Git ref:** <branch / commit hash>
**Scope note:** docs/features/<feature-name>/scope.md

---

## Acceptance Criteria

### AC-1: <Criterion Name>
- [x] PASS — <what was verified>
- [ ] FAIL — <observed vs. expected>

### AC-2: <Criterion Name>
- [x] PASS

---

## API Validation (curl)

### Endpoint: <METHOD /path>
- [x] Happy path: 200 with expected body
- [x] Missing required field: 400 with specific error
- [x] Not found: 404
- [x] Conflict: 409 (where applicable)
- [x] Response shape matches OpenAPI spec
- [ ] ISSUE: <description>

---

## UI Validation (browser)

- [x] Create Configuration: valid input is accepted
- [x] Configuration Overview: new entry appears, Start/Edit/Remove work
- [x] PLC States: state transitions Connected ↔ Disconnected
- [x] Validation: invalid IPv4 / port / PLC address rejected with a clear message
- [x] Devtools console: no runtime errors
- [ ] ISSUE: <description>

---

## Data Path Validation (PLC → Telegraf → MQTT)

- [ ] Not exercised — no PLC / MQTT broker available
- [ ] Exercised:
  - [x] Telegraf process started under supervisord
  - [x] MQTT payload received with expected shape
  - [x] Field values match PLC tag values

---

## Container Health

- [x] All three containers running (`docker ps`)
- [x] Backend logs clean
- [x] Database logs clean
- [x] Frontend (nginx) logs clean
- [x] supervisord shows expected processes (`docker exec ... supervisorctl status`)
- [ ] ISSUE: <description>

---

## Security Audit

- [x] No credentials in the diff
- [x] `machine_name` sanitized before file operations
- [x] No new published ports
- [x] No suspicious new dependencies in `requirements.txt` / `package.json`
- [ ] VULNERABILITY: <description — treat as Critical>

---

## Regression Check

- [x] Existing curl tests in `backend/test/` pass
- [x] Existing UI flows still work
- [x] Existing example Telegraf configs still load
- [x] Existing CouchDB documents still parse

---

## Issues Found

### ISSUE-1: <Title>
- **Severity:** Critical | High | Medium | Low
- **Component:** backend route | service | model | frontend component | nginx | database | telegraf | docker
- **Steps to Reproduce:**
  1. <Step 1>
  2. <Step 2>
  3. Expected: <what should happen>
  4. Actual: <what actually happens>
- **Priority:** Fix before release | Fix in next feature | Nice to have

---

## Coverage Gaps
- <e.g. "MQTT data path not exercised — no broker available">

---

## Summary
- **Acceptance Criteria:** X / Y passed
- **Issues Found:** N total (C critical, H high, M medium, L low)
- **Security Audit:** Pass | Issues found
- **Production Ready:** YES / NO
- **Recommendation:** Release / Fix issues first
