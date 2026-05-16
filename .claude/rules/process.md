# Process Rules

## Read Before Change (MANDATORY)
- ALWAYS read a file before modifying it — never assume contents from memory
- After context compaction, re-read files before continuing work
- Run `git diff` to verify what has already been changed in this session
- Check `architecture/decisions/` (if it exists) before making structural decisions
- Never guess at route paths, field names, service method names, container names, or CouchDB document keys — verify by reading

## Human-in-the-Loop
- Always ask for user approval before finalizing scope or architectural decisions
- Present options using clear choices rather than open-ended questions
- Never proceed to the next workflow phase without user confirmation
- Any change to MQTT payload structure, PLC address parsing, REST API surface, or CouchDB document schema requires explicit approval — these affect external consumers

## Status Updates (MANDATORY — Write-Then-Verify)
After completing work on any component:
1. **Read** the relevant code or config files BEFORE editing
2. **Write** changes using the Edit tool — do NOT just describe what you would write
3. **Re-read** the file AFTER editing only if uncertainty exists; otherwise trust the tool result
4. Update `CHANGELOG.md` for meaningful changes (if it exists)
5. Update relevant README sections if user-facing behavior changes

**NEVER:**
- Say "I've updated the file" without actually calling the Edit/Write tool
- Summarize changes in chat as a substitute for writing them to files
- Skip updates because it seems obvious or minor

## Scope Discipline
- Do not add features, refactor, or "improve" beyond what was asked
- Do not create helpers or abstractions for one-time operations
- Do not design for hypothetical future requirements
- Fix the root cause — do not use workarounds to bypass error handling or validation
- Do not introduce new dependencies in `requirements.txt` or `package.json` without explicit user approval
