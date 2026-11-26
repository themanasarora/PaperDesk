# Format Selector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A scholar picks the target template from a dropdown and is checked against that rule set only.

**Architecture:** Rule sets become data modules in a `rules/` package, collected in a registry. `checker.check()` already takes a rules dict; it gains a few structural switches (page name, heading style, table numbering, keywords label). `app.py` reads a `ruleset` form field, looks it up in the registry, and shows an unverified/stale notice.

**Tech Stack:** Python 3, Flask 3.1, python-docx 1.2, pytest 9.

**Spec:** `docs/design-format-selector.md`

## Global Constraints

- Rules stay static data. No AI call on uploads for this feature.
- The checker only reports; it never edits the author's document.
- Default rule set key: `"ieee_conference"`.
- Staleness threshold: 180 days from `last_verified`.
- An unknown `ruleset` form value returns HTTP 400 and is never echoed into the page.
- A rule set with `verified: False` always shows a visible "Unverified draft rules" notice in the web report and the markdown report.
- Baseline must not change: with `ieee_conference`, `samples/test_paper_flawed.docx` gives 9 errors / 3 warnings and `samples/test_paper_clean.docx` gives 0 / 0.
- The project is not a git repository, so tasks end with a full test run instead of a commit.
- Plan deviation from the design (my call): `figure_label` is dropped. All three templates use "Fig.", and the regexes would still only match "Fig.", so a label key would do nothing. `table_numbering` ("roman" / "arabic") is added because Springer tables use Arabic numerals and would otherwise be flagged wrongly.

## Review Focus

- A form value `ruleset=<script>` or any unknown key: HTTP 400, no crash, value not echoed. (Task 4)
- No `ruleset` field at all (old form, API client): falls back to `ieee_conference`. (Task 4)
- Body text that starts with a number ("2 samples were excluded...") must not be read as a numeric heading. (Task 2)
- Numeric headings with subsections (1, 1.1, 1.2, 2) and an unnumbered "References" heading: only top-level order is checked and nothing is flagged. (Task 2)
- An A4 document checked against a US Letter rule set reports the page size and names "US Letter"; against an A4 rule set it does not. (Task 2)

## File Structure

- Create `rules/__init__.py`: registry, defaults, notice logic.
- Create `rules/ieee_conference.py`, `rules/ieee_journal.py`, `rules/springer_lncs.py`: one `RULES` dict each.
- Delete `rules_ieee.py` (moved into `rules/ieee_conference.py`).
- Modify `checker.py`: switches, `classify(paragraphs, rules=None)`, CLI flag, markdown notice.
- Modify `app.py`: dropdown, lookup, notice.
- Create `conftest.py` (docx builder fixture), `test_rulesets.py`, `test_checker_rulesets.py`, `test_format_selector.py`.
- Modify `README.md`; set the design doc status to "approved".

---

### Task 1: Rules package, defaults, notices

**Files:**
- Create: `rules/__init__.py`, `rules/ieee_conference.py` (content of the old `rules_ieee.py` as `RULES`)
- Delete: `rules_ieee.py`
- Modify: `checker.py` (imports; `rules["roman_headings"]` becomes `rules["heading_style"] == "roman"`), `app.py` (imports)
- Test: `test_rulesets.py`

**Interfaces:**
- Produces, in `rules/__init__.py`:
  - `DEFAULT: str = "ieee_conference"`
  - `RULESETS: dict[str, dict]` (keys: ruleset key; values: raw rule dicts)
  - `DEFAULTS: dict` with `page_name="US Letter"`, `heading_style="roman"`, `keywords_label="Index Terms"`, `table_numbering="roman"`, `verified=False`, `source=""`, `last_verified=None`
  - `with_defaults(rules: dict) -> dict` (new dict, `DEFAULTS` overridden by `rules`)
  - `get_ruleset(key: str) -> dict` (returns `with_defaults(RULESETS[key])`; raises `KeyError` for unknown keys)
  - `rules_notice(rules: dict, today: datetime.date | None = None) -> str | None`
- `rules/ieee_conference.py` sets `heading_style: "roman"`, `verified: False`, and `name: "IEEE conference"`.

- [ ] **Step 1: Write failing tests in `test_rulesets.py`**
  - `test_default_key_is_registered`: `DEFAULT in RULESETS`.
  - `test_with_defaults_fills_missing_keys`: `with_defaults({"name": "x"})["table_numbering"] == "roman"` and `["verified"] is False`.
  - `test_with_defaults_does_not_mutate_input`: input dict keeps its original key set.
  - `test_get_ruleset_unknown_key_raises`: `pytest.raises(KeyError)` for `"nope"`.
  - `test_notice_unverified`: `rules_notice(get_ruleset("ieee_conference"))` contains `"Unverified draft rules"`.
  - `test_notice_stale`: `verified=True, last_verified="2026-01-01"`, `today=date(2026, 11, 27)` gives a string containing `"2026-01-01"`.
  - `test_notice_fresh_is_none`: `verified=True, last_verified="2026-11-01"`, same `today` gives `None`.
  - `test_notice_verified_without_date`: `verified=True, last_verified=None` gives a string containing `"not recorded"`.
- [ ] **Step 2: Run `python3 -m pytest test_rulesets.py -q`.** Expected: collection error (no `rules` package).
- [ ] **Step 3: Implement the package as specified above.** Staleness rule: older than 180 days (strictly more) is stale. Move the old dict verbatim, then apply the changes listed under Produces.
- [ ] **Step 4: Run `python3 -m pytest test_rulesets.py -q`.** Expected: all pass.
- [ ] **Step 5: Run the old script test `python3 test_app.py`.** Expected output still contains `9 errors, 3 warnings` for flawed and `0 errors, 0 warnings` for clean.

---

### Task 2: Checker switches

**Files:**
- Modify: `checker.py` (`classify`, `check`, regexes)
- Create: `conftest.py`
- Test: `test_checker_rulesets.py`

**Interfaces:**
- Consumes: `get_ruleset`, `with_defaults` from Task 1.
- `conftest.py` provides fixture `build_docx(tmp_path)` returning `build(paragraphs: list[str], page: tuple[float, float] = (8.5, 11.0), margins: tuple[float, float, float, float] = (0.75, 1.0, 0.625, 0.625)) -> str` (path of a saved .docx; margins are top, bottom, left, right).
- Produces: `classify(paragraphs, rules: dict | None = None) -> list[str]` (None means `get_ruleset(DEFAULT)`); `check(path, rules=None)` where `None` means the default rule set. New regex `HEADING_NUM_RE` for headings like `1 Introduction`, `1.1 Background`.
- Behaviour:
  - Page-size message uses `rules["page_name"]`.
  - The missing-keywords message and fix use `rules["keywords_label"]`.
  - With `heading_style == "numeric"`, a heading is: starts with digits and optional `.digits` groups, a space, an uppercase letter, at most 12 words, no trailing period. Unnumbered `References` (any case) is a heading. Only top-level numbers (no dot) are checked, expected 1, 2, 3...
  - With `table_numbering == "arabic"`, table captions are `Table 1.` and references are `Table 1`; the "Table N" messages print Arabic numerals.
  - Roman behaviour is unchanged.

- [ ] **Step 1: Write failing tests in `test_checker_rulesets.py`** (filter results by `{i.rule for i in issues}`; abstract and body font noise is ignored):
  - `test_ieee_baseline_unchanged`: flawed sample gives exactly 9 ERROR and 3 WARN; clean sample gives 0 and 0.
  - `test_a4_document_fails_letter_ruleset`: A4 doc `(8.27, 11.69)`, default rules: `"Page size"` present and its detail contains `"US Letter"`.
  - `test_a4_document_passes_a4_ruleset`: same doc, rules `with_defaults({**get_ruleset("ieee_conference"), "page_name": "A4", "page_width_in": 8.27, "page_height_in": 11.69})`: `"Page size"` absent.
  - `test_keywords_label_in_message`: doc without a keywords line, rules with `keywords_label="Keywords"`: `"Index terms"` issue detail contains `"Keywords"`.
  - `test_numeric_headings_with_subsections_pass`: paragraphs `["Title", "Author", "Abstract— ...", "Keywords: a, b", "1 Introduction", "text", "1.1 Background", "text", "1.2 Scope", "text", "2 Methods", "text", "References"]`, numeric rules: `"Heading numbering"` absent.
  - `test_numeric_headings_out_of_order_flagged`: same but `"3 Results"` after `"1 Introduction"`: issue present, detail contains `"section 2 was expected"`.
  - `test_number_led_body_text_is_not_a_heading`: `classify` on `["Title", "Author", "Abstract— x", "2 samples were excluded from the study", "2 Samples were excluded from the study."]` with numeric rules: both labelled `"body"`.
  - `test_arabic_table_captions`: numeric+arabic rules, doc with caption `"Table 1. Results"` and body text `"See Table 1 for results."`: neither `"Table not referenced"` nor `"Table referenced but missing"` is present.
- [ ] **Step 2: Run `python3 -m pytest test_checker_rulesets.py -q`.** Expected: the new-behaviour tests FAIL; `test_ieee_baseline_unchanged` passes.
- [ ] **Step 3: Implement the behaviour above in `checker.py`.** Fill rule defaults once at the top of `check()` with `with_defaults`. `classify` must pick heading and table-caption regexes from `rules`.
- [ ] **Step 4: Run the whole suite `python3 -m pytest -q` and `python3 test_app.py`.** Expected: all pass; script output unchanged for clean and flawed.

---

### Task 3: IEEE journal and Springer LNCS placeholder rule sets

**Files:**
- Create: `rules/ieee_journal.py`, `rules/springer_lncs.py`
- Modify: `rules/__init__.py` (register both)
- Test: `test_rulesets.py` (add)

**Interfaces:**
- Consumes: registry from Task 1.
- Produces: registry keys `"ieee_journal"` (name `"IEEE journal"`) and `"springer_lncs"` (name `"Springer LNCS"`). Numeric values are copied from the conference rule set as placeholders; Manas replaces them later. Structure keys are set for the template family: IEEE journal `heading_style="roman"`, `table_numbering="roman"`, `page_name="US Letter"`; Springer `heading_style="numeric"`, `table_numbering="arabic"`, `page_name="A4"` with `page_width_in=8.27`, `page_height_in=11.69`, `keywords_label="Keywords"`. Both have `verified=False`, `source=""`, `last_verified=None`, and a module docstring saying every value must be checked against the official template, then `verified`, `source` and `last_verified` filled in.

- [ ] **Step 1: Write failing tests (add to `test_rulesets.py`).**
  - `test_all_three_rulesets_registered`: `{"ieee_conference", "ieee_journal", "springer_lncs"} <= set(RULESETS)`.
  - `test_new_rulesets_are_unverified`: `get_ruleset(k)["verified"] is False` for the two new keys.
  - `test_springer_structure`: `heading_style == "numeric"`, `table_numbering == "arabic"`, `page_name == "A4"`, `keywords_label == "Keywords"`.
  - `test_ieee_journal_structure`: `heading_style == "roman"`.
  - `test_every_ruleset_has_required_keys`: each `get_ruleset(k)` contains `name, page_width_in, page_height_in, margins_in, margin_tolerance_in, body_font, body_size_pt, abstract_words, require_index_terms, heading_style, table_numbering, keywords_label, flag_double_spaces, require_figure_table_references`.
- [ ] **Step 2: Run `python3 -m pytest test_rulesets.py -q`.** Expected: new tests FAIL.
- [ ] **Step 3: Create the two modules and register them.**
- [ ] **Step 4: Run `python3 -m pytest -q`.** Expected: all pass.

---

### Task 4: Dropdown, notice, CLI, docs

**Files:**
- Modify: `app.py`, `checker.py` (`to_markdown`, CLI), `README.md`, `docs/design-format-selector.md` (status line)
- Test: `test_format_selector.py`

**Interfaces:**
- Consumes: `RULESETS`, `DEFAULT`, `get_ruleset`, `rules_notice`, `check`.
- Produces: form field `ruleset`; `render(report=None, error=None, status=200, ruleset=DEFAULT)` shows the select (current key preselected), and in the report view the rule set name plus the notice when `rules_notice(...)` is not None. `to_markdown(path, issues, rules)` adds the notice line under "Rule set". CLI gains `--ruleset KEY` (choices from `RULESETS`, default `DEFAULT`).
- Behaviour: missing or empty `ruleset` means `DEFAULT`; an unknown key returns 400 with the message "Unknown template." and the submitted value is never rendered.

- [ ] **Step 1: Write failing tests in `test_format_selector.py`** using `app.app.test_client()`, posting `samples/test_paper_clean.docx` as `paper`:
  - `test_form_lists_every_ruleset`: `GET /` contains `<select name="ruleset"` and an `<option value="KEY"` for each registry key.
  - `test_missing_ruleset_defaults_to_ieee_conference`: status 200, body contains `"IEEE conference"`.
  - `test_springer_selected_shows_name_and_unverified_notice`: `ruleset=springer_lncs`: status 200, body contains `"Springer LNCS"` and `"Unverified draft rules"`.
  - `test_unknown_ruleset_rejected_and_not_echoed`: `ruleset="<script>alert(1)</script>"`: status 400, body contains `"Unknown template"`, body does not contain `"<script>alert"`.
  - `test_stale_notice_in_report` (monkeypatch `RULESETS["ieee_conference"]` to `verified=True, last_verified="2020-01-01"`): body contains `"2020-01-01"`.
  - `test_markdown_report_contains_notice`: `to_markdown(...)` for `springer_lncs` contains `"Unverified draft rules"`.
- [ ] **Step 2: Run `python3 -m pytest test_format_selector.py -q`.** Expected: FAIL.
- [ ] **Step 3: Implement.** Replace the hard-coded `IEEE_CONFERENCE` use in `app.py` with a lookup per request; add the `<select>` to the form; pass the chosen rules into `checker.check` and the template. Add the README section "Choosing a template" (how to add a rule file, the unverified flag, `last_verified`). Change the design doc status line to "approved; implementation plan in docs/superpowers/plans/".
- [ ] **Step 4: Run `python3 -m pytest -q`, then `python3 test_app.py`, then `python3 checker.py samples/test_paper_flawed.docx --ruleset ieee_conference`.** Expected: pytest all pass; script output unchanged; CLI prints a report with `9 errors, 3 warnings`.
- [ ] **Step 5: Start `python3 app.py`, open `http://127.0.0.1:5000`, and confirm the dropdown shows the three templates.** Stop the server afterwards.
