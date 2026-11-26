"""Builds two test papers from scratch with python-docx:
  samples/test_paper_clean.docx   - follows the draft IEEE rules
  samples/test_paper_flawed.docx  - same paper with planted mistakes

The paper is an original design overview. It contains no experimental results
and is only for testing the checker. It is not for submission anywhere.
"""
import sys
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

TITLE = "Automated Pre-Submission Checking for Academic Manuscripts: A Design Overview"
AUTHOR = "Test Author, Department of Computer Science, Example University"

ABSTRACT_CLEAN = (
    "Abstract—Researchers often lose time to avoidable formatting and consistency errors "
    "before a manuscript is even reviewed. This paper describes the design of a "
    "pre-submission checker that reads a word-processor document and reports problems in "
    "page layout, typography, section structure, abstract length, and the consistency "
    "between in-text citations and the reference list. The design separates deterministic "
    "rule checks from language-model assistance, so that every reported issue can be traced "
    "to an explicit rule, while a language model is used only for optional wording "
    "suggestions that the author reviews. We outline the rule set, the report format, and "
    "the safeguards that keep the tool from altering the scientific content of a paper. "
    "The goal is to help authors prepare submissions without replacing their own writing. "
    "Because the checks are explicit and repeatable, the same document always produces the "
    "same report, which makes the tool easy to audit and easy to extend to new publisher "
    "templates. The report groups findings by severity so that authors can fix blocking "
    "errors first and review minor warnings afterwards."
)
ABSTRACT_FLAWED = (
    "Abstract—This paper describes a pre-submission checker for manuscripts. "
    "It reports layout and citation problems to authors."
)
INDEX_TERMS = "Index Terms—manuscript preparation, document analysis, citation checking, formatting"

REFS = [
    "A. Vaswani et al., “Attention is all you need,” in Advances in Neural Information Processing Systems, 2017.",
    "J. Devlin, M.-W. Chang, K. Lee, and K. Toutanova, “BERT: Pre-training of deep bidirectional transformers for language understanding,” in Proc. NAACL-HLT, 2019.",
    "T. Brown et al., “Language models are few-shot learners,” in Advances in Neural Information Processing Systems, 2020.",
    "P. Lewis et al., “Retrieval-augmented generation for knowledge-intensive NLP tasks,” in Advances in Neural Information Processing Systems, 2020.",
]


def para(doc, text, size=10, font="Times New Roman", bold=False, italic=False,
         align=None):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = font
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if align is not None:
        p.alignment = align
    return p


def build(flawed: bool, path: str):
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    if flawed:
        sec.top_margin = sec.bottom_margin = sec.left_margin = sec.right_margin = Inches(1.0)
    else:
        sec.top_margin, sec.bottom_margin = Inches(0.75), Inches(1.0)
        sec.left_margin = sec.right_margin = Inches(0.625)

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(10)

    para(doc, TITLE, size=24, align=WD_ALIGN_PARAGRAPH.CENTER)
    para(doc, AUTHOR, size=10, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER)

    para(doc, ABSTRACT_FLAWED if flawed else ABSTRACT_CLEAN, size=9, bold=True)
    if not flawed:
        para(doc, INDEX_TERMS, size=9, bold=True, italic=True)

    # I. INTRODUCTION
    para(doc, "I. INTRODUCTION", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    intro1 = (
        "Preparing a manuscript for submission involves many small rules: margins, fonts, "
        "heading styles, reference formats, and limits on abstract length. Authors who miss "
        "them risk administrative rejection before any reviewer reads the work. Language models "
        "built on the transformer architecture [1] can now suggest wording changes, but wording "
        "help is only one part of the problem."
    )
    if flawed:
        # planted: Arial 12pt paragraph and double spaces
        para(doc, intro1, size=12, font="Arial")
        para(doc, "A checker should be predictable.  It should report what it found  and where.")
    else:
        para(doc, intro1)
        para(doc, "A checker should be predictable. It should report what it found and where.")
    para(doc, "This paper describes the design of such a checker. Section II reviews related "
              "background, Section III describes the system, and the remaining sections discuss "
              "the checks and limits of the approach.")

    # II. RELATED WORK
    para(doc, "II. RELATED WORK", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    related = (
        "Pre-trained language models such as BERT [2] and large generative models "
        + ("" if flawed else "[3] ")
        + "have been applied to grammar correction and text rewriting. Retrieval-augmented "
        "methods [4] ground generated text in source documents, which is useful when a tool "
        "must refer to a publisher's author guidelines instead of relying on memory."
    )
    para(doc, related)
    if flawed:
        para(doc, "Earlier work on layout analysis is also relevant [6].")

    # III. SYSTEM DESIGN
    para(doc, "III. SYSTEM DESIGN", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    para(doc, "The checker reads a .docx file, extracts its structure, and applies a rule set "
              "that describes one publisher's requirements. Fig. 1 shows the pipeline. Rules are "
              "stored as data, so a new journal can be supported by editing a configuration "
              "file instead of changing the code.")
    para(doc, "Fig. 1. Pipeline: document parsing, rule checks, optional wording suggestions, report.",
         size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
    if flawed:
        para(doc, "The report also lists reviewer-facing statistics, as shown in Fig. 2.")

    # IV. CHECKS IMPLEMENTED  (flawed: numbered V, skipping IV)
    para(doc, "V. CHECKS IMPLEMENTED" if flawed else "IV. CHECKS IMPLEMENTED",
         bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    checks_intro = ("The checks fall into four groups, summarised in "
                    + ("the list below." if flawed else "Table I."))
    para(doc, checks_intro)
    para(doc, "TABLE I. CHECK GROUPS", size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
    table = doc.add_table(rows=5, cols=2)
    table.style = "Table Grid"
    rows = [("Group", "Examples"),
            ("Page layout", "paper size, margins"),
            ("Typography", "body font and size, double spaces"),
            ("Structure", "abstract length, index terms, heading order"),
            ("Citations", "missing or unused references, figure references")]
    for r, (a, b) in enumerate(rows):
        table.cell(r, 0).text = a
        table.cell(r, 1).text = b

    # V. DISCUSSION  (flawed: VI)
    para(doc, "VI. DISCUSSION" if flawed else "V. DISCUSSION", bold=True,
         align=WD_ALIGN_PARAGRAPH.CENTER)
    para(doc, "Deterministic checks are easy to trust because each finding points to a rule. "
              "Language-model suggestions are optional and are always shown as suggestions, "
              "never applied automatically. The tool does not write or rewrite scientific "
              "content, and it cannot judge whether a result is correct. Publisher policies on "
              "disclosing assistance from software also vary and must be followed by the author.")

    # VI. CONCLUSION (flawed: VII)
    para(doc, "VII. CONCLUSION" if flawed else "VI. CONCLUSION", bold=True,
         align=WD_ALIGN_PARAGRAPH.CENTER)
    para(doc, "We described a design for a pre-submission checker that separates explicit rule "
              "checks from optional language assistance. Future work includes supporting more "
              "publisher templates and evaluating the tool with authors.")

    # REFERENCES
    para(doc, "REFERENCES", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    refs = REFS if not flawed else REFS  # flawed: ref [3] left uncited in body
    for i, r in enumerate(refs, 1):
        para(doc, f"[{i}] {r}", size=8)

    doc.save(path)
    print("wrote", path)


if __name__ == "__main__":
    build(False, "samples/test_paper_clean.docx")
    build(True, "samples/test_paper_flawed.docx")
