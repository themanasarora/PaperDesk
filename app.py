"""PaperDesk web app: upload a .docx, get a check report.

Run:  python3 app.py     (then open http://127.0.0.1:5000)
The uploaded file is read from a temporary file that is deleted right after the
check. Nothing is stored and manuscript text is never logged.
"""
import datetime
import os
import tempfile

from flask import Flask, render_template, request

import checker
import suggest
import template_rules
from rules import DEFAULT, RULESETS, get_ruleset, rules_notice

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

CUSTOM = "custom"
CUSTOM_LABEL = "Custom (read rules from the journal's template)"


def render(report=None, error=None, status=200, ruleset=DEFAULT, rules=None):
    if rules is None:
        rules = ({"name": "Custom template", "verified": True,
                  "last_verified": datetime.date.today().isoformat()}
                 if ruleset == CUSTOM else get_ruleset(ruleset))
    return render_template(
        "index.html", report=report, error=error, ai=suggest.available(), rules=rules["name"],
        notice=rules_notice(rules), current=ruleset,
        rulesets=[(k, get_ruleset(k)["name"]) for k in RULESETS] + [(CUSTOM, CUSTOM_LABEL)]), status


def is_zip(f) -> bool:
    head = f.stream.read(4)
    f.stream.seek(0)
    return head == b"PK\x03\x04"  # .docx is a zip file


def rules_from_upload(tpl):
    """Rules read from an uploaded template; the temporary copy is always deleted."""
    tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
    try:
        tpl.save(tmp)
        tmp.close()
        name = "Custom template (" + os.path.basename(tpl.filename)[:60] + ")"
        return template_rules.rules_from_template(tmp.name, name=name)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


@app.errorhandler(413)
def too_large(_e):
    return render(error="File is larger than 10 MB.", status=413)


@app.get("/")
def index():
    return render()


@app.post("/check")
def check_upload():
    key = request.form.get("ruleset") or DEFAULT
    if key not in RULESETS and key != CUSTOM:
        return render(error="Unknown template.", status=400)
    if key == CUSTOM:
        tpl = request.files.get("template")
        if not tpl or not tpl.filename:
            return render(error="Custom needs a template .docx.", status=400, ruleset=key)
        if not tpl.filename.lower().endswith(".docx") or not is_zip(tpl):
            return render(error="The template file does not look like a valid .docx.", status=400, ruleset=key)
        try:
            rules = rules_from_upload(tpl)
        except Exception:
            return render(error="Could not read the template. Try re-saving it as .docx from Word.",
                          status=400, ruleset=key)
    else:
        rules = get_ruleset(key)
    f = request.files.get("paper")
    if not f or not f.filename:
        return render(error="Please choose a .docx file.", status=400, ruleset=key)
    if not f.filename.lower().endswith(".docx"):
        return render(error="Only Word .docx files are supported.", status=400, ruleset=key)
    if not is_zip(f):
        return render(error="That file does not look like a valid .docx.", status=400, ruleset=key)

    tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
    try:
        f.save(tmp)
        tmp.close()
        try:
            issues = checker.check(tmp.name, rules)
            wording = []
            if request.form.get("wording") and suggest.available():
                from docx import Document
                doc = Document(tmp.name)
                labels = checker.classify(doc.paragraphs, rules)
                body = [(i + 1, p.text.strip()) for i, (p, l) in enumerate(zip(doc.paragraphs, labels))
                        if l == "body" and len(p.text.split()) >= 15]
                try:
                    wording = suggest.suggest(body)
                except Exception:
                    wording = []  # suggestions are optional; the check result still shows
        except Exception:
            return render(error="Could not read this document. Try re-saving it as .docx from Word.",
                          status=400, ruleset=key)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    report = {
        "errors": [x for x in issues if x.severity == "ERROR"],
        "warns": [x for x in issues if x.severity == "WARN"],
        "suggestions": wording,
    }
    return render(report=report, ruleset=key, rules=rules)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
