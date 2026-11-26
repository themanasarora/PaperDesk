"""PaperDesk web app: upload a .docx, get a check report.

Run:  python3 app.py     (then open http://127.0.0.1:5000)
The uploaded file is read from a temporary file that is deleted right after the
check. Nothing is stored and manuscript text is never logged.
"""
import os
import tempfile

from flask import Flask, render_template_string, request

import checker
import suggest
from rules import DEFAULT, get_ruleset

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

PAGE = """
<!doctype html><title>PaperDesk</title>
<style>
 body{font-family:system-ui,sans-serif;max-width:760px;margin:2rem auto;padding:0 1rem;line-height:1.5}
 .err{border-left:4px solid #b3261e;padding:.3rem .8rem;margin:.6rem 0;background:#fdf1f0}
 .warn{border-left:4px solid #b26a00;padding:.3rem .8rem;margin:.6rem 0;background:#fff7e8}
 .sug{border-left:4px solid #1a73e8;padding:.3rem .8rem;margin:.6rem 0;background:#eef4ff}
 small{color:#555} code{background:#eee;padding:0 .2rem}
</style>
<h1>PaperDesk</h1>
<p>Pre-submission check for your manuscript. It reports problems; it never rewrites your paper.</p>
{% if error %}<p class="err"><b>{{ error }}</b></p>{% endif %}
{% if report is none %}
<form method="post" action="/check" enctype="multipart/form-data">
  <p><input type="file" name="paper" accept=".docx" required></p>
  {% if ai %}<p><label><input type="checkbox" name="wording"> Also show optional wording suggestions
     (sends paragraph text to an AI service)</label></p>{% endif %}
  <p><button type="submit">Check my paper</button></p>
  <small>Word (.docx) only, up to 10 MB. Rule set: {{ rules }}.</small>
</form>
{% else %}
<h2>Result: {{ report.errors|length }} errors, {{ report.warns|length }} warnings</h2>
{% if not report.errors and not report.warns %}<p>No problems found against this rule set.</p>{% endif %}
{% for x in report.errors %}<div class="err"><b>{{ x.rule }}</b>: {{ x.detail }}<br>
  <small>Where: {{ x.where }}<br>Fix: {{ x.fix }}</small></div>{% endfor %}
{% for x in report.warns %}<div class="warn"><b>{{ x.rule }}</b>: {{ x.detail }}<br>
  <small>Where: {{ x.where }}<br>Fix: {{ x.fix }}</small></div>{% endfor %}
{% if report.suggestions %}<h2>Optional wording suggestions</h2>
<p><small>Language only. Check each one yourself and follow your publisher's policy on disclosing AI assistance.</small></p>
{% for s in report.suggestions %}<div class="sug"><small>Paragraph {{ s.paragraph }} &mdash; {{ s.reason }}</small><br>
 <b>Original:</b> {{ s.original }}<br><b>Suggestion:</b> {{ s.suggestion }}</div>{% endfor %}{% endif %}
<p><a href="/">Check another paper</a></p>
<small>This tool checks formatting against a draft rule set; confirm requirements with your conference or journal.</small>
{% endif %}
"""


def render(report=None, error=None, status=200):
    return render_template_string(PAGE, report=report, error=error, ai=suggest.available(),
                                  rules=get_ruleset(DEFAULT)["name"]), status


@app.get("/")
def index():
    return render()


@app.post("/check")
def check_upload():
    f = request.files.get("paper")
    if not f or not f.filename:
        return render(error="Please choose a .docx file.", status=400)
    if not f.filename.lower().endswith(".docx"):
        return render(error="Only Word .docx files are supported.", status=400)
    head = f.stream.read(4)
    f.stream.seek(0)
    if head != b"PK\x03\x04":  # .docx is a zip file
        return render(error="That file does not look like a valid .docx.", status=400)

    tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
    try:
        f.save(tmp)
        tmp.close()
        try:
            issues = checker.check(tmp.name)
            wording = []
            if request.form.get("wording") and suggest.available():
                from docx import Document
                doc = Document(tmp.name)
                labels = checker.classify(doc.paragraphs)
                body = [(i + 1, p.text.strip()) for i, (p, l) in enumerate(zip(doc.paragraphs, labels))
                        if l == "body" and len(p.text.split()) >= 15]
                try:
                    wording = suggest.suggest(body)
                except Exception:
                    wording = []  # suggestions are optional; the check result still shows
        except Exception:
            return render(error="Could not read this document. Try re-saving it as .docx from Word.",
                          status=400)
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
    return render(report=report)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
