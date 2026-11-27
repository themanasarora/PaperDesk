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

from numbering import rendered_labels
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
HEADING_NUM_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+[A-Z]")
HEADING_ROMAN_ANY_RE = re.compile(r"^([IVXLC]+)\.\s+[A-Z]")
CAPTION_TABLE_UPPER_RE = re.compile(r"^TABLE\s+([IVXLC]+)\b")
CAPTION_TABLE_UPPER_ARABIC_RE = re.compile(r"^TABLE\s+(\d+)\b")
CAPTION_ONLY_RE = re.compile(r"^TABLE\s+(?:[IVXLC]+|\d+)\.?$")
HEADING_STYLE_RE = re.compile(r"^heading\s*(\d)", re.I)
LABEL_ROMAN_RE = re.compile(r"^([IVXLC]+)\.(?:\s|$)")
LABEL_ARABIC_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?(?:\s|$)")
LABEL_LETTER_RE = re.compile(r"^[A-Z]\.(?:\s|$)")
LEADING_NUMBER_RE = re.compile(r"^(?:[IVXLC]+|\d+(?:\.\d+)*|[A-Z])[.)]?\s+")
NEVER_NUMBERED = ("references", "acknowledg", "appendix")   # headings the templates leave unnumbered
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


def table_caption_number(text: str, rules):
    """Table number if `text` starts a table caption, else None.
    Accepts "TABLE I" (IEEE style, no period) and "Table I." (with period)."""
    if rules["table_numbering"] == "arabic":
        for rx in (CAPTION_TABLE_ARABIC_RE, CAPTION_TABLE_UPPER_ARABIC_RE):
            m = rx.match(text)
            if m:
                return int(m.group(1))
        return None
    for rx in (CAPTION_TABLE_RE, CAPTION_TABLE_UPPER_RE):
        m = rx.match(text)
        if m:
            return roman_to_int(m.group(1).upper())
    return None


def style_name(p) -> str:
    try:
        return p.style.name or ""
    except Exception:
        return ""


def heading_level(p):
    m = HEADING_STYLE_RE.match(style_name(p))
    return int(m.group(1)) if m else None


def visible_text(p, numbers, i) -> str:
    """Paragraph text as printed: Word's automatic number, then the text."""
    raw = p.text.strip()
    num = (numbers[i] if numbers and i < len(numbers) else "").strip()
    return f"{num} {raw}".strip() if raw and num else raw


def strip_leading_number(text: str) -> str:
    return LEADING_NUMBER_RE.sub("", text, count=1).strip()


def is_references_heading(text: str) -> bool:
    return strip_leading_number(text).lower() == "references"


def is_never_numbered(text: str) -> bool:
    return strip_leading_number(text).lower().startswith(NEVER_NUMBERED)


def heading_number(vis: str):
    """('roman', n) | ('arabic', n) | ('sub', None) for 1.1 / A. | None if unnumbered."""
    m = LABEL_ROMAN_RE.match(vis)
    if m and roman_to_int(m.group(1)) <= 20:
        return "roman", roman_to_int(m.group(1))
    arabic = LABEL_ARABIC_RE.match(vis)
    if arabic:
        return ("sub", None) if "." in arabic.group(1) else ("arabic", int(arabic.group(1)))
    return ("sub", None) if LABEL_LETTER_RE.match(vis) or m else None


def is_heading_text(vis: str, rules) -> bool:
    if rules["heading_style"] == "numeric":
        return is_numeric_heading(vis)
    if HEADING_RE.match(vis):
        return True
    m = HEADING_ROMAN_ANY_RE.match(vis)
    return bool(m) and roman_to_int(m.group(1)) <= 20 and len(vis.split()) <= 12 and not vis.endswith(".")


def classify(paragraphs, rules=None, numbers=None):
    """Label each paragraph: title, author, abstract, index, heading, reference,
    reference_text, caption_fig, caption_table, caption_text, body, blank.

    `numbers` are Word's automatic list numbers (numbering.rendered_labels), so
    auto-numbered headings and reference lists are recognised like typed ones."""
    rules = with_defaults(rules or get_ruleset(DEFAULT))
    ref_re = reference_re(rules)
    dotted = rules["reference_style"] == "dotted"
    in_refs = False
    labels = []
    seen_abstract = False
    prev_caption_only = False
    for i, p in enumerate(paragraphs):
        raw = p.text.strip()
        low = raw.lower()
        vis = visible_text(p, numbers, i)
        caption_only, label = False, None
        if not raw:
            label = "blank"
        elif i == 0:
            label = "title"
        elif not seen_abstract and not low.startswith("abstract"):
            label = "author"
        elif low.startswith("abstract"):
            seen_abstract = True
            label = "abstract"
        elif low.startswith("index terms") or low.startswith("keywords"):
            label = "index"
        elif is_references_heading(vis):
            in_refs = True
            label = "heading"
        elif ref_re.match(vis) and (in_refs or not dotted):
            label = "reference"
        elif heading_level(p) is not None or (not in_refs and is_heading_text(vis, rules)):
            in_refs = False
            label = "heading"
        elif in_refs:
            label = "reference_text"
        elif CAPTION_FIG_RE.match(raw):
            label = "caption_fig"
        elif table_caption_number(raw, rules) is not None:
            label = "caption_table"
            caption_only = bool(CAPTION_ONLY_RE.match(raw))
        elif prev_caption_only and len(raw.split()) <= 30:
            label = "caption_text"   # the title line under a bare "TABLE I"
        else:
            label = "body"
        labels.append(label)
        if label != "blank":
            prev_caption_only = caption_only
    return labels


def effective_font(doc, p, run):
    name = run.font.name or p.style.font.name or doc.styles["Normal"].font.name
    size = run.font.size or p.style.font.size or doc.styles["Normal"].font.size
    return name, (size.pt if size else None)


def check(path: str, rules=None):
    rules = with_defaults(rules or get_ruleset(DEFAULT))
    doc = Document(path)
    paras = doc.paragraphs
    numbers = rendered_labels(doc)
    labels = classify(paras, rules, numbers)
    vis = [visible_text(p, numbers, i) for i, p in enumerate(paras)]
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

    # ---- heading numbering ----
    kinds = {"roman": ("roman", "Roman numerals (I, II, III, ...)", "Arabic numbers (1., 2., ...)", int_to_roman),
             "numeric": ("arabic", "Arabic numbers (1, 2, 3, ...)", "Roman numerals (I., II., ...)", str)}
    if rules["heading_style"] in kinds:
        want, want_name, other_name, show = kinds[rules["heading_style"]]
        sequence, wrong = [], []
        for i, lab in enumerate(labels):
            if lab != "heading" or is_never_numbered(paras[i].text.strip()):
                continue
            kind, value = heading_number(vis[i]) or (None, None)
            if kind is None:
                if heading_level(paras[i]) in (1, 2):  # level 3+ may be run-in or lettered
                    add("ERROR", "Heading numbering", f"paragraph {i + 1}: \"{snippet(paras[i].text)}\"",
                        f"Heading \"{snippet(paras[i].text, 40)}\" has no number.",
                        f"Number the headings with {want_name}.")
            elif kind == want:
                sequence.append((i, value))
            elif kind in ("roman", "arabic"):
                wrong.append(i)
        if wrong:
            add("ERROR", "Heading numbering", f"paragraph {wrong[0] + 1}: \"{snippet(paras[wrong[0]].text)}\"",
                f"Headings are numbered with {other_name}; this template uses {want_name}.",
                f"Number the headings with {want_name}.")
        for expected, (i, value) in enumerate(sequence, 1):
            if value != expected:
                add("ERROR", "Heading numbering", f"paragraph {i + 1}: \"{snippet(paras[i].text)}\"",
                    f"Heading numbered {show(value)} but section {expected} was expected.",
                    "Renumber headings in order" + (" (I, II, III, ...)." if want == "roman" else " (1, 2, 3, ...)."))
                break  # one report; later numbers follow from this one

    # ---- citations vs references ----
    ref_nums = [int(reference_re(rules).match(vis[i]).group(1))
                for i, lab in enumerate(labels) if lab == "reference"]
    unnumbered_refs = "reference_text" in labels and not ref_nums
    cited = {}
    for i, (p, lab) in enumerate(zip(paras, labels)):
        if lab in ("body", "abstract"):
            for m in CITE_RE.finditer(p.text):
                for n in expand_cites(m.group(1)):
                    cited.setdefault(n, i + 1)
    if unnumbered_refs:
        add("WARN", "Reference numbering", "reference list",
            "The reference list is not numbered, so citations like [1] cannot be matched to entries.",
            "Number the references [1], [2], ... in the order they are cited.")
    for n, para_no in sorted(cited.items()) if not unnumbered_refs else []:
        if n not in ref_nums:
            add("ERROR", "Citation without reference", f"paragraph {para_no}",
                f"Citation [{n}] has no entry in the reference list.",
                f"Add reference [{n}] or correct the citation number.")
    for n in ([] if unnumbered_refs else ref_nums):
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
        tab_caps = {table_caption_number(p.text.strip(), rules)
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
