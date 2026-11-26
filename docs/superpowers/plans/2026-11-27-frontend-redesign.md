# Frontend Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace PaperDesk's plain inline page with the approved "B, step by step" design (Template, Upload, Report) without changing any check behaviour.

**Architecture:** Move the page out of the `PAGE` string in `app.py` into `templates/index.html`, `static/style.css` and `static/app.js`. `app.py` renders it with `render_template`; routes, status codes and error strings stay identical. Template choice becomes radio cards named `ruleset`; JavaScript only adds the step rail behaviour and the Custom reveal, and the form works with JavaScript off.

**Tech Stack:** Flask 3.1 (Jinja autoescape), plain CSS and JavaScript, pytest.

**Spec:** `docs/superpowers/specs/2026-11-27-frontend-redesign-design.md`

## Global Constraints

- The 50 existing tests stay green, except the four HTML-shape assertions listed in Task 1, which are updated on purpose (select/option becomes radio).
- Exact error strings unchanged: "Unknown template.", "Custom needs a template .docx.", "The template file does not look like a valid .docx.", "Could not read the template. Try re-saving it as .docx from Word.", "Please choose a .docx file.", "Only Word .docx files are supported.", "That file does not look like a valid .docx.", "Could not read this document. Try re-saving it as .docx from Word."
- Form: `method="post" action="/check" enctype="multipart/form-data"`; field names `ruleset`, `paper`, `template`, `wording` unchanged.
- Privacy copy must be true: "Your file is deleted right after the check." Wording-suggestions checkbox text must say paragraph text is sent to an AI service.
- Accent colour `#3B3F9E`; sentence case; no emoji; must work at phone width.
- No changes to `checker.py`, `rules/`, `template_rules.py`, `suggest.py`.

## Review Focus

1. File or template name containing HTML (`<img src=x onerror=1>.docx`) must appear escaped, never as live markup.
2. A paper with zero findings shows 0 and 0 in the summary cards and the "No problems found" message.
3. JavaScript off: every step visible, form still submits and works.
4. After any 400 error the chosen template stays selected and the error message is shown.
5. A file over 10 MB gets a friendly page ("File is larger than 10 MB.") with status 413, not Flask's default error page.

---

### Task 1: Move the page to templates and swap the dropdown for template cards

**Files:**
- Create: `templates/index.html`, `static/style.css`
- Modify: `app.py` (remove `PAGE`, use `render_template`), `test_format_selector.py` (four assertions)
- Test: `test_frontend.py` (new)

**Interfaces:**
- Consumes: existing `render(report, error, status, ruleset, rules)` in `app.py`.
- Produces: template context names unchanged (`report`, `error`, `ai`, `rules`, `notice`, `current`, `rulesets`); template cards are `<input type="radio" name="ruleset" value="<key>">` with `checked` on the key equal to `current`.

- [ ] **Step 1: Update the old HTML-shape assertions and add the new tests**

In `test_format_selector.py`: replace `'<select name="ruleset"' in html` with `'type="radio" name="ruleset"' in html`; replace `f'<option value="{key}"' in html` with `f'name="ruleset" value="{key}"' in html`; replace `b'<option value="springer_lncs" selected'` with `b'name="ruleset" value="springer_lncs" checked'`; replace `'<option value="custom"' in html` and `b'<option value="custom" selected'` with the radio equivalents (`value="custom"`, `value="custom" checked`).

In `test_frontend.py` (define a `client` fixture there: `app.app.config['TESTING']=True; return app.app.test_client()`):
```python
def test_default_template_card_is_checked(client):  # DEFAULT is ieee_conference
    html = client.get("/").data.decode()
    assert 'name="ruleset" value="ieee_conference" checked' in html

def test_stylesheet_is_served(client):
    r = client.get("/static/style.css")
    assert r.status_code == 200 and b"#3B3F9E" in r.data and b"@media" in r.data
```

- [ ] **Step 2: Run `pytest -q`; expect the changed and new tests to FAIL**

- [ ] **Step 3: Implement.** Create `templates/index.html` (same context and the same form fields, four template cards with a one-line description each, the Custom card, a `template` file input, the existing text for errors, report, suggestions and footer) and `static/style.css` (indigo palette, card and banner styles, `@media (max-width: 640px)` single column). In `app.py`, delete `PAGE`, import `render_template`, and render `index.html` with the same context.

- [ ] **Step 4: Run `pytest -q`; expect all tests PASS (50 plus the new ones)**

- [ ] **Step 5: Commit** `git add -A && git commit -m "Move page to templates; template cards replace dropdown"`

### Task 2: Step rail, upload step copy and the stepper script

**Files:**
- Create: `static/app.js`
- Modify: `templates/index.html`, `static/style.css`
- Test: `test_frontend.py`

**Interfaces:**
- Consumes: Task 1 template and `static/style.css`.
- Produces: rail items with `data-step="template" | "upload" | "report"`; the active step carries class `is-active`. Result page has `report` step active; GET and error pages have `template` or `upload` active.

- [ ] **Step 1: Write failing tests**
```python
def test_rail_lists_three_steps(client):
    html = client.get("/").data.decode()
    for step in ("template", "upload", "report"):
        assert f'data-step="{step}"' in html

def test_privacy_line_present(client):
    assert "Your file is deleted right after the check." in client.get("/").data.decode()

def test_wording_checkbox_discloses_ai_when_available(client, monkeypatch):
    monkeypatch.setattr("suggest.available", lambda: True)
    html = client.get("/").data.decode()
    assert 'name="wording"' in html and "sent to an AI service" in html

def test_wording_checkbox_hidden_when_unavailable(client, monkeypatch):
    monkeypatch.setattr("suggest.available", lambda: False)
    assert 'name="wording"' not in client.get("/").data.decode()

def test_form_works_without_script(client):  # all steps in the markup, file input required
    html = client.get("/").data.decode()
    assert 'name="paper"' in html and "required" in html and 'action="/check"' in html

def test_script_is_served(client):
    assert client.get("/static/app.js").status_code == 200
```
- [ ] **Step 2: Run `pytest test_frontend.py -q`; expect FAIL**
- [ ] **Step 3: Implement the rail and the step copy in `templates/index.html`; `static/app.js` marks the active step on load and on card selection, reveals the `template` file input only when Custom is selected, and shows the chosen file's name in the drop zone. Without JavaScript all sections are visible.**
- [ ] **Step 4: Run `pytest -q`; expect all PASS**
- [ ] **Step 5: Commit** `git commit -am "Add step rail, privacy copy and stepper script"`

### Task 3: Report step, friendly oversize error and escaping

**Files:**
- Modify: `templates/index.html`, `static/style.css`, `app.py`
- Test: `test_frontend.py`

**Interfaces:**
- Consumes: `report.errors`, `report.warns` (items have `rule`, `detail`, `where`, `fix`), `report.suggestions`, `notice`.
- Produces: summary cards with `data-count="errors"` and `data-count="warnings"` holding the integer; findings as `<div class="finding finding-error|finding-warn">`; `app.errorhandler(413)` returns `render(error="File is larger than 10 MB.", status=413)`.

- [ ] **Step 1: Write failing tests** (use the file's existing `build_docx`/sample helpers and `post(client, ...)` pattern)
```python
def test_report_shows_count_cards(client):          # flawed sample: 9 errors, 3 warnings (IEEE conference)
    html = post_flawed(client)
    assert 'data-count="errors">9<' in html and 'data-count="warnings">3<' in html
    assert 'class="finding finding-error"' in html and 'data-step="report"' in html

def test_clean_paper_shows_zero_and_no_problems(client):
    html = post_clean(client)
    assert 'data-count="errors">0<' in html and "No problems found against this rule set." in html

def test_oversize_upload_is_friendly(client):
    big = (io.BytesIO(b"PK\x03\x04" + b"0" * (10 * 1024 * 1024 + 1)), "big.docx")
    r = client.post("/check", data={"ruleset": "ieee_conference", "paper": big},
                    content_type="multipart/form-data")
    assert r.status_code == 413 and b"File is larger than 10 MB." in r.data

def test_template_filename_is_escaped(client):
    r = post_custom_with_template_name(client, "<img src=x onerror=1>.docx")
    assert b"<img src=x" not in r.data

def test_error_keeps_template_and_message(client):
    r = client.post("/check", data={"ruleset": "springer_lncs"}, content_type="multipart/form-data")
    assert r.status_code == 400 and b"Please choose a .docx file." in r.data
    assert b'name="ruleset" value="springer_lncs" checked' in r.data
```
`post_flawed`, `post_clean`, `post_custom_with_template_name` are small helpers in `test_frontend.py` wrapping the existing sample files in `samples/` and the `build_docx` fixture.
- [ ] **Step 2: Run `pytest test_frontend.py -q`; expect FAIL**
- [ ] **Step 3: Implement the report layout in the template and CSS; add the 413 handler in `app.py` (`@app.errorhandler(413)`).**
- [ ] **Step 4: Run `pytest -q`; expect all PASS**
- [ ] **Step 5: Commit** `git commit -am "Report step with count cards; friendly 413; escaping test"`

### Task 4: Look at it, then document

**Files:**
- Modify: `README.md` (one short "Look and feel" note: where the templates and styles live)

- [ ] **Step 1:** Start the app (`python3 app.py`) and capture screenshots of the upload screen, a flawed-paper report and a 400 error at desktop and 390 px width, using headless Chromium via Playwright if installed (otherwise `pip install playwright --break-system-packages && playwright install chromium`; if that is blocked, say so and skip).
- [ ] **Step 2:** Read the screenshots; fix any overlap, unreadable contrast or cut-off text in `static/style.css`; re-run `pytest -q` (all PASS).
- [ ] **Step 3: Commit** `git commit -am "Polish after visual check; README note"` and send the screenshots to the user.
