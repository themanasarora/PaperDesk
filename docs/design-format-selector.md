# Format selector: short design

Status: awaiting approval from Manas. Nothing built yet.

## Intent
A scholar picks the template their paper targets (IEEE conference, IEEE journal, Springer LNCS, later "Custom") and PaperDesk checks against that rule set only. Why: scholars submit to many templates, and a single IEEE rule set would give wrong errors for everyone else.

## Goals
- Dropdown on the upload page, populated from a registry of rule sets.
- Adding a template = adding one rule file, no checker changes for ordinary values.
- Checker handles the structural differences between templates.
- Every rule file states its source and is marked "unverified" until Manas confirms it against the official template.

## Non-goals
- No Elsevier or other journals in this round.
- No PDF input, no LaTeX.
- The checker never edits the paper.

## Anti-goals
- Silently shipping unverified numbers as if they were official.
- A rule set that changes the checker's behaviour in ways the report doesn't explain.

## Approaches (picked: C)
- A. Registry + a rule file per template. Simple. Risk: values rest on whoever writes them.
- B. Read rules from the journal's own template .docx. No guessing for page setup and fonts, but it cannot see rules that exist only in PDF instructions.
- C (chosen). Ship A first, then add B as a "Custom" dropdown entry. Reason: A gives a working feature now, B removes the guessing later.

## Design
- `rules/` package: one module per template exposing a dict, plus `rules/__init__.py` with `RULESETS = {key: dict}` and `DEFAULT = "ieee_conference"`.
- Rule dict gains new keys, all with defaults so the old IEEE file keeps working: `page_name` ("US Letter" / "A4"), `heading_style` ("roman" / "numeric" / "none"), `keywords_label` ("Index Terms" / "Keywords"), `figure_label` (e.g. "Fig."), `verified` (bool) and `source` (URL or note).
- `checker.py`: heading check branches on `heading_style`; page message uses `page_name`; keyword check uses `keywords_label`. Old `rules_ieee.py` becomes `rules/ieee_conference.py`.
- `app.py`: `<select name="ruleset">`; the server looks the key up in `RULESETS` and rejects unknown keys (400). The report header shows the rule set name and a visible "unverified rules" notice when `verified` is False.
- Tests: each rule set loads and has all required keys; clean sample passes IEEE conference; flawed sample still gives 9 errors / 3 warnings; unknown ruleset key is rejected; heading-style numeric works on a small numeric-heading fixture.

## Rules change over time (decided: static now)
- Rules stay static data; no AI judge on uploads (cost, non-determinism, false errors).
- Each rule file also carries `last_verified` (ISO date) and `source` (official URL). The report shows the verified date and warns if it is older than 180 days.
- Later, not in this round: an offline monthly script asks an LLM to diff each official source against its rule file and lists differences for Manas to review by hand. It never runs on user uploads and never edits rule files itself.

## Who does what
- Claude: registry, checker switches, app dropdown, tests, placeholder files for IEEE journal and Springer LNCS copied from the conference defaults and marked unverified.
- Manas: fill and verify `rules/ieee_journal.py` and `rules/springer_lncs.py` from the official templates; later write `rules_from_template(docx) -> dict` for the Custom option (Claude reviews and wires it in).

## Left to the builder
File layout details, error wording, and how the unverified notice looks.
