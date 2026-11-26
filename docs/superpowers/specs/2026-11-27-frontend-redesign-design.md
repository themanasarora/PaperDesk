# Frontend redesign: design (approved 2026-11-27)

## Intent and why
PaperDesk's page is plain: a heading, a dropdown, a file picker, red/yellow boxes. A scholar must trust it enough to upload an unpublished paper, so the page needs to look credible and guide a first-time user. Chosen direction: "B, step by step" (Template, Upload, Report) in indigo.

## Goals
- Look trustworthy and clear for MTech/PhD scholars.
- Same behaviour: the form still posts to `/check`, same error messages and status codes.
- Honest privacy copy: the uploaded paper's temp file is deleted right after the check (`finally` block in `app.py`); if wording suggestions are on, paragraphs are sent to the Anthropic API and the page says so next to the checkbox.

## Non-goals
Landing/marketing page, login, payment, hosting, changes to `checker.py` or `rules/`.

## Anti-goals
Anything that changes check results; any privacy claim the code does not back up.

## Approaches considered
- A: academic minimal (one centered card), quietest, fastest.
- B: step by step with left rail and template cards (chosen by the user).
- C: split hero, busiest.

## Design
- Left rail: Template, Upload, Report. One page, small JavaScript stepper (no extra routes). Without JavaScript all steps stay visible and the form still works.
- Step 1: template cards (IEEE conference, IEEE journal, Springer LNCS, Custom) with a one-line description each. Custom reveals the template .docx input. Cards write the selected key into a hidden/radio `ruleset` field, so the form payload is unchanged.
- Step 2: .docx drop zone (file input `paper`), optional wording checkbox (`wording`, only if `suggest.available()`) with the API disclosure, delete-after-check note, submit button "Check my paper".
- Step 3 (after a result): two summary cards (errors, warnings), the rules notice as a banner, findings as bordered rows with red/amber tags, optional wording suggestions, "Check another paper" link, existing footer caveat.
- Error responses re-render with the chosen template kept and the error message shown; exact message strings unchanged.
- Files: `templates/index.html`, `static/style.css` (and `static/app.js`) replace the inline `PAGE` string; `app.py` uses `render_template`.

## Constraints
- 50 existing tests stay green; tests assert exact message strings.
- Indigo palette from mockup B (#3B3F9E accent). Works on a phone-width screen.

## Left to the builder
Exact spacing, copy for card descriptions, and small-screen layout.
