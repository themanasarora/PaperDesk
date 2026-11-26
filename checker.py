"""PaperDesk checker: reads a .docx and reports formatting, structure and
citation-consistency problems against a rule set (see the rules/ package).

Usage:
    python3 checker.py samples/test_paper_flawed.docx [-o reports/out.md]

It only reports problems. It never edits the author's text.
"""
import argparse
import re
import sys
from dataclasses import dataclass

from docx import Document

from rules import DEFAULT, RULESETS, get_ruleset, rules_notice, with_defaults

ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
HEADING_RE = re.compile(r"^([IVXLC]+)\.\s+[A-Z][A-Z0-9 ,&\-]+$")
CAPTION_FIG_RE = re.compile(r"^Fig\.\s*(\d+)\.")
CAPTION_TABLE_RE = re.compile(r"^TABLE\s+([IVXLC]+)\.", re.I)
REF_LINE_RE = re.compile(r"^\[(\d+)\]\s+")
REF_DOTTED_RE = re.compile(r"^(\d+)\.?\s+\S")
CITE_RE = re.compile(r"\[([\d,\s–\-]+)\]")
FIG_REF_RE = re.compile(r"\bFig\.?\s*(\d+)")
TABLE_REF_RE = re.compile(r"\bTable\s+([IVXLC]+)\b", re.I)
HEADING_NUM_RE = re.compile(r"^(\d+(?:\.\d+)*)\s+[A-Z]")
CAPTION_TABLE_ARABIC_RE = re.compile(r"^Table\s+(\d+)\.", re.I)
TABLE_REF_ARABIC_RE = re.compile(r"\bTable\s+(\d+)\b", re.I)


@dataclass
class Issue:
    severity: str  # ERROR or WARN
    rule: str
    where: str
    detail: str
    fix: str


def roman_to_int(s: str) -> int:
    total, prev = 0, 0
    for ch in reversed(s):
        v = ROMAN[ch]
        total += -v if v < prev else v
        prev = max(prev, v)
    return total


def int_to_roman(n: int) -> str:
    out = ""
    for val, sym in ((50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= val:
            out += sym
            n -= val
    return out


def expand_cites(group: str):
    nums = set()
    for part in re.split(r",", group):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(\d+)\s*[–\-]\s*(\d+)$", part)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            nums.update(range(min(a, b), max(a, b) + 1))
        elif part.isdigit():
            nums.add(int(part))
    return nums


def is_numeric_heading(text: str) -> bool:
    """'1 Introduction', '1.1 Background': a short line with no final period."""
    return bool(HEADING_NUM_RE.match(text)) and len(text.split()) <= 12 and not text.endswith(".")


def table_numbering(rules):
    """(caption regex, reference regex, parse group -> int, show int -> label)."""
    if rules["table_numbering"] == "arabic":
        return CAPTION_TABLE_ARABIC_RE, TABLE_REF_ARABIC_RE, int, str
    return CAPTION_TABLE_RE, TABLE_REF_RE, lambda g: roman_to_int(g.upper()), int_to_roman


def reference_re(rules):
    return REF_DOTTED_RE if rules["reference_style"] == "dotted" else REF_LINE_RE


def snippet(text: str, n: int = 60) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 3] + "..."


def classify(paragraphs, rules=None):
    """Label each paragraph: title, author, abstract, index, heading,
    caption_fig, caption_table, reference, body, blank."""
    rules = with_defaults(rules or get_ruleset(DEFAULT))
    cap_table_re = table_numbering(rules)[0]
    ref_re = reference_re(rules)
    dotted = rules["reference_style"] == "dotted"
    in_refs = False
    numeric = rules["heading_style"] == "numeric"
    labels = []
    seen_abstract = False
    for i, p in enumerate(paragraphs):
        t = p.text.strip()
        if not t:
            labels.append("blank")
        elif i == 0:
            labels.append("title")
        elif not seen_abstract and not t.lower().startswith("abstract"):
            labels.append("author")
        elif t.lower().startswith("abstract"):
            seen_abstract = True
            labels.append("abstract")
        elif t.lower().startswith("index terms") or t.lower().startswith("keywords"):
            labels.append("index")
        elif ref_re.match(t) and (in_refs or not dotted):
            labels.append("reference")
        elif (is_numeric_heading(t) or t.lower() == "references") if numeric else (HEADING_RE.match(t) or t == "REFERENCES"):
            in_refs = in_refs or t.lower() == "references"
            labels.append("heading")
        elif CAPTION_FIG_RE.match(t):
            labels.append("caption_fig")
        elif cap_table_re.match(t):
            labels.append("caption_table")
        else:
            labels.append("body")
    return labels


def effective_font(doc, p, run):
    name = run.font.name or p.style.font.name or doc.styles["Normal"].font.name
    size = run.font.size or p.style.font.size or doc.styles["Normal"].font.size
    return name, (size.pt if size else None)


def check(path: str, rules=None):
    rules = with_defaults(rules or get_ruleset(DEFAULT))
    doc = Document(path)
    paras = doc.paragraphs
    labels = classify(paras, rules)
    issues = []
    add = lambda *a: issues.append(Issue(*a))

    # ---- page setup ----
    sec = doc.sections[0]
    w, h = sec.page_width.inches, sec.page_height.inches
    if rules["page_width_in"] is not None and (
            abs(w - rules["page_width_in"]) > 0.02 or abs(h - rules["page_height_in"]) > 0.02):
        add("ERROR", "Page size", "document",
            f"Page is {w:.2f} x {h:.2f} in; expected {rules['page_width_in']} x {rules['page_height_in']} in ({rules['page_name']}).",
            f"Set the paper size to {rules['page_name']}.")
    tol = rules["margin_tolerance_in"]
    got = {"top": sec.top_margin.inches, "bottom": sec.bottom_margin.inches,
           "left": sec.left_margin.inches, "right": sec.right_margin.inches}
    for side, want in (rules["margins_in"] or {}).items():  # None = not checked
        if abs(got[side] - want) > tol:
            add("ERROR", "Margin", "document",
                f"{side.capitalize()} margin is {got[side]:.2f} in; expected {want} in.",
                f"Set the {side} margin to {want} in.")

    # ---- body font and size ----
    for i, (p, lab) in enumerate(zip(paras, labels)):
        if lab != "body" or (rules["body_font"] is None and rules["body_size_pt"] is None):
            continue
        bad = set()
        for run in p.runs:
            if not run.text.strip():
                continue
            name, size = effective_font(doc, p, run)
            if rules["body_font"] is not None and name != rules["body_font"]:
                bad.add(f"font {name}")
            if rules["body_size_pt"] is not None and size != rules["body_size_pt"]:
                bad.add(f"size {size}")
        if bad:
            add("ERROR", "Body text style", f"paragraph {i + 1}: \"{snippet(p.text)}\"",
                f"Found {', '.join(sorted(bad))}; expected {rules['body_font'] or 'any font'}"
                f" {rules['body_size_pt'] or 'any size'} pt.",
                "Apply the body text style to this paragraph.")

    # ---- abstract ----
    abs_idx = [i for i, l in enumerate(labels) if l == "abstract"]
    if not abs_idx:
        add("ERROR", "Abstract", "document", "No abstract found.", "Add an abstract after the title block.")
    else:
        text = re.sub(r"^abstract\s*[—\-:–]*\s*", "", paras[abs_idx[0]].text.strip(), flags=re.I)
        words = len(text.split())
        lo, hi = rules["abstract_words"] or (0, float("inf"))  # None = not checked
        if words < lo or words > hi:
            add("ERROR", "Abstract length", f"paragraph {abs_idx[0] + 1}",
                f"Abstract has {words} words; expected {lo}-{hi}.",
                "Expand or shorten the abstract to fit the range.")

    # ---- index terms ----
    if rules["require_index_terms"] and "index" not in labels:
        add("ERROR", "Index terms", "document", f"No {rules['keywords_label']} line found.",
            f"Add a '{rules['keywords_label']}' line after the abstract.")

    # ---- heading order ----
    if rules["heading_style"] == "roman":
        seq = []
        for i, (p, lab) in enumerate(zip(paras, labels)):
            if lab == "heading":
                m = HEADING_RE.match(p.text.strip())
                if m:
                    seq.append((i, m.group(1), roman_to_int(m.group(1))))
        for expected, (i, rom, val) in enumerate(seq, 1):
            if val != expected:
                add("ERROR", "Heading numbering", f"paragraph {i + 1}: \"{snippet(paras[i].text)}\"",
                    f"Heading numbered {rom} but section {expected} was expected.",
                    "Renumber headings in order (I, II, III, ...).")
                break  # one report; later numbers follow from this one

    elif rules["heading_style"] == "numeric":
        seq = [(i, m.group(1)) for i, (p, lab) in enumerate(zip(paras, labels))
               if lab == "heading" and (m := HEADING_NUM_RE.match(p.text.strip())) and "." not in m.group(1)]
        for expected, (i, num) in enumerate(seq, 1):
            if int(num) != expected:
                add("ERROR", "Heading numbering", f"paragraph {i + 1}: \"{snippet(paras[i].text)}\"",
                    f"Heading numbered {num} but section {expected} was expected.",
                    "Renumber headings in order (1, 2, 3, ...).")
                break

    # ---- citations vs references ----
    ref_nums = []
    for p, lab in zip(paras, labels):
        if lab == "reference":
            ref_nums.append(int(reference_re(rules).match(p.text.strip()).group(1)))
    cited = {}
    for i, (p, lab) in enumerate(zip(paras, labels)):
        if lab in ("body", "abstract"):
            for m in CITE_RE.finditer(p.text):
                for n in expand_cites(m.group(1)):
                    cited.setdefault(n, i + 1)
    for n, para_no in sorted(cited.items()):
        if n not in ref_nums:
            add("ERROR", "Citation without reference", f"paragraph {para_no}",
                f"Citation [{n}] has no entry in the reference list.",
                f"Add reference [{n}] or correct the citation number.")
    for n in ref_nums:
        if n not in cited:
            add("WARN", "Reference never cited", f"reference [{n}]",
                f"Reference [{n}] is not cited anywhere in the text.",
                "Cite it where relevant or remove it.")
    if ref_nums and ref_nums != list(range(1, len(ref_nums) + 1)):
        add("WARN", "Reference numbering", "reference list",
            "Reference numbers are not 1, 2, 3 ... in order.", "Renumber the references.")

    # ---- figures and tables ----
    if rules["require_figure_table_references"]:
        cap_re, ref_re, parse_no, show_no = table_numbering(rules)
        fig_caps = {int(CAPTION_FIG_RE.match(p.text.strip()).group(1))
                    for p, l in zip(paras, labels) if l == "caption_fig"}
        tab_caps = {parse_no(cap_re.match(p.text.strip()).group(1))
                    for p, l in zip(paras, labels) if l == "caption_table"}
        fig_refs, tab_refs = {}, {}
        for i, (p, lab) in enumerate(zip(paras, labels)):
            if lab in ("body", "abstract"):
                for m in FIG_REF_RE.finditer(p.text):
                    fig_refs.setdefault(int(m.group(1)), i + 1)
                for m in ref_re.finditer(p.text):
                    tab_refs.setdefault(parse_no(m.group(1)), i + 1)
        for n, para_no in sorted(fig_refs.items()):
            if n not in fig_caps:
                add("ERROR", "Figure referenced but missing", f"paragraph {para_no}",
                    f"Fig. {n} is mentioned but no caption 'Fig. {n}.' exists.",
                    "Insert the figure with a caption or fix the number.")
        for n in sorted(fig_caps - set(fig_refs)):
            add("WARN", "Figure not referenced", f"Fig. {n}", f"Fig. {n} is never mentioned in the text.",
                "Refer to it in the text.")
        for n in sorted(tab_caps - set(tab_refs)):
            add("WARN", "Table not referenced", f"Table {show_no(n)}",
                f"Table {show_no(n)} is never mentioned in the text.", "Refer to it in the text.")
        for n, para_no in sorted(tab_refs.items()):
            if n not in tab_caps:
                add("ERROR", "Table referenced but missing", f"paragraph {para_no}",
                    f"Table {show_no(n)} is mentioned but no caption exists.",
                    "Insert the table or fix the number.")

    # ---- double spaces ----
    if rules["flag_double_spaces"]:
        for i, (p, lab) in enumerate(zip(paras, labels)):
            if lab in ("body", "abstract") and "  " in p.text:
                add("WARN", "Double space", f"paragraph {i + 1}: \"{snippet(p.text)}\"",
                    f"{p.text.count('  ')} double space(s) found.", "Replace double spaces with single spaces.")

    return issues


def to_markdown(path, issues, rules=None):
    rules = rules or get_ruleset(DEFAULT)
    errors = [x for x in issues if x.severity == "ERROR"]
    warns = [x for x in issues if x.severity == "WARN"]
    lines = [f"# PaperDesk check report", "",
             f"- File: `{path}`", f"- Rule set: {rules['name']}",
             f"- Result: **{len(errors)} errors, {len(warns)} warnings**", ""]
    notice = rules_notice(rules)
    if notice:
        lines[4:4] = [f"- **{notice}**"]
    if not issues:
        lines.append("No problems found against this rule set.")
    for title, group in (("Errors (fix before submitting)", errors), ("Warnings (please review)", warns)):
        if group:
            lines += [f"## {title}", ""]
            for k, x in enumerate(group, 1):
                lines += [f"{k}. **{x.rule}**: {x.detail}", f"   - Where: {x.where}", f"   - Fix: {x.fix}"]
            lines.append("")
    lines += ["---", "This report lists problems only. It did not change your document. "
              "Rules are a draft; confirm them against the conference's own instructions."]
    return "\n".join(lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("--ruleset", choices=sorted(RULESETS), default=DEFAULT)
    ap.add_argument("-o", "--out")
    args = ap.parse_args()
    chosen = get_ruleset(args.ruleset)
    found = check(args.docx, chosen)
    md = to_markdown(args.docx, found, chosen)
    if args.out:
        open(args.out, "w").write(md)
        print("wrote", args.out)
    else:
        print(md)
    sys.exit(1 if any(x.severity == "ERROR" for x in found) else 0)
