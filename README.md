# PaperDesk (prototype)

Pre-submission checker for research manuscripts. Reports formatting, structure and
citation problems. Never writes or rewrites the author's content.

## Run
    pip install python-docx flask anthropic
    python3 app.py            # open http://127.0.0.1:5000
    python3 checker.py samples/test_paper_flawed.docx      # command line
    python3 test_app.py       # automated checks of the app

## Files
- rules/         one rule file per template (ieee_conference, ieee_journal, springer_lncs); see "Choosing a template"
- checker.py     reads .docx, finds problems
- suggest.py     optional wording suggestions (needs ANTHROPIC_API_KEY); language only,
                 dropped if numbers, [n] citations or capitalised terms change
- app.py         upload page + report page; temp files deleted right after the check
- make_sample.py builds the clean and flawed test papers

## Known limits
- Rules are from general knowledge of the IEEE template: verify before charging anyone.
- .docx only (no LaTeX, no PDF). Two-column layout, equations, text boxes and tracked
  changes are not checked.
- Wording suggestions were not tested against the live API in this build.
- Add a privacy note and terms before real users upload unpublished manuscripts.

## Choosing a template
The upload page has a Template dropdown. Each entry is a file in `rules/` listed in `rules/__init__.py`.
To add one: copy a rule file, change the values, and register it in `RULESETS`.
Every rule file has `verified`, `source` (official URL) and `last_verified` (ISO date). While `verified` is False,
reports show "Unverified draft rules"; after 180 days without re-verifying they show a stale-rules warning.
Command line: `python3 checker.py paper.docx --ruleset springer_lncs`.
