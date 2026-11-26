# PaperDesk (prototype)

Pre-submission checker for research manuscripts. Reports formatting, structure and
citation problems. Never writes or rewrites the author's content.

## Run
    pip install python-docx flask anthropic
    python3 app.py            # open http://127.0.0.1:5000
    python3 checker.py samples/test_paper_flawed.docx      # command line
    python3 test_app.py       # automated checks of the app

## Files
- rules_ieee.py  draft IEEE conference rules (edit values here)
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
