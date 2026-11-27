"""Resolve Word's automatic list numbering to the labels a reader sees.

Real papers number headings and reference lists with Word lists, so the
number ("[3]", "II.", "1.2") is not in paragraph.text. rendered_labels()
works out what Word would print, so checks can read it.

Never raises: anything it can't understand gives an empty label.
"""
import re

from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from lxml import etree

NO_LABEL_FORMATS = {"bullet", "none"}
_PLACEHOLDER = re.compile(r"%([1-9])")


def _int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _val(element, tag):
    child = element.find(qn(f"w:{tag}"))
    return None if child is None else child.get(qn("w:val"))


def _numbering_root(doc):
    for rel in doc.part.rels.values():
        if rel.reltype.endswith("/numbering") and not rel.is_external:
            part = rel.target_part
            root = getattr(part, "element", None)
            return root if root is not None else etree.fromstring(part.blob)
    return None


def _definitions(root):
    """-> (abstracts {id: {ilvl: (fmt, text, start)}}, nums {id: (abstract id, {ilvl: start})})."""
    abstracts, nums = {}, {}
    for a in root.findall(qn("w:abstractNum")):
        aid = _int(a.get(qn("w:abstractNumId")))
        levels = {}
        for lvl in a.findall(qn("w:lvl")):
            ilvl = _int(lvl.get(qn("w:ilvl")))
            if ilvl is None:
                continue
            levels[ilvl] = (_val(lvl, "numFmt") or "decimal", _val(lvl, "lvlText") or "",
                            _int(_val(lvl, "start"), 1))
        if aid is not None:
            abstracts[aid] = levels
    for n in root.findall(qn("w:num")):
        nid = _int(n.get(qn("w:numId")))
        if nid is None:
            continue
        overrides = {}
        for o in n.findall(qn("w:lvlOverride")):
            ilvl = _int(o.get(qn("w:ilvl")))
            start = o.find(qn("w:startOverride"))
            if ilvl is not None and start is not None and _int(start.get(qn("w:val"))) is not None:
                overrides[ilvl] = _int(start.get(qn("w:val")))
        nums[nid] = (_int(_val(n, "abstractNumId")), overrides)
    return abstracts, nums


def _roman(n):
    if not 0 < n < 4000:
        return str(n)
    out = ""
    for value, sym in ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
                       (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= value:
            out += sym
            n -= value
    return out


def _format(n, fmt):
    if fmt == "upperRoman":
        return _roman(n)
    if fmt == "lowerRoman":
        return _roman(n).lower()
    if fmt in ("upperLetter", "lowerLetter"):
        if n < 1:
            return str(n)
        letter = chr(ord("A") + (n - 1) % 26) * ((n - 1) // 26 + 1)
        return letter if fmt == "upperLetter" else letter.lower()
    if fmt == "decimalZero":
        return f"{n:02d}"
    return str(n)


def _style_chain(paragraph):
    style, seen = paragraph.style, set()
    while style is not None and id(style) not in seen:
        seen.add(id(style))
        yield style.element
        style = style.base_style


def _paragraph_numbering(paragraph):
    """-> (numId, ilvl) from the paragraph, else its styles; numId None if none."""
    sources = []
    pPr = paragraph._p.pPr
    if pPr is not None:
        sources.append(pPr)
    sources += [el.pPr for el in _style_chain(paragraph) if el.pPr is not None]
    num_id = ilvl = None
    for pPr in sources:
        num_pr = pPr.find(qn("w:numPr"))
        if num_pr is None:
            continue
        if num_id is None and _val(num_pr, "numId") is not None:
            num_id = _int(_val(num_pr, "numId"))
        if ilvl is None and _val(num_pr, "ilvl") is not None:
            ilvl = _int(_val(num_pr, "ilvl"))
    return num_id, (0 if ilvl is None else ilvl)


class _Counters:
    def __init__(self, abstracts, nums):
        self.abstracts, self.nums = abstracts, nums
        self.current = {}      # abstract id -> {ilvl: value of the last paragraph at that level}
        self.pending = {}      # abstract id -> {ilvl: start value waiting for its first paragraph}
        self.seen_nums = set()

    def label(self, num_id, ilvl):
        if not num_id or num_id not in self.nums:
            return ""
        aid, overrides = self.nums[num_id]
        levels = self.abstracts.get(aid)
        if levels is None or ilvl not in levels:
            return ""
        fmt, text, start = levels[ilvl]
        cur = self.current.setdefault(aid, {})
        pending = self.pending.setdefault(aid, {})
        if num_id not in self.seen_nums:
            self.seen_nums.add(num_id)
            for lvl, value in overrides.items():
                pending[lvl] = value
                cur.pop(lvl, None)
        if fmt in NO_LABEL_FORMATS:
            return ""
        if ilvl in pending:
            cur[ilvl] = pending.pop(ilvl)
        elif ilvl in cur:
            cur[ilvl] += 1
        else:
            cur[ilvl] = start
        for deeper in [l for l in cur if l > ilvl]:
            del cur[deeper]

        def fill(match):
            lvl = int(match.group(1)) - 1
            lvl_fmt, _t, lvl_start = levels.get(lvl, ("decimal", "", 1))
            return _format(cur.get(lvl, pending.get(lvl, lvl_start)), lvl_fmt)

        return _PLACEHOLDER.sub(fill, text)


def rendered_labels(doc):
    """One label per paragraph in doc.paragraphs: '[3]', 'II.', '1.2' or ''."""
    try:
        root = _numbering_root(doc)
        if root is None:
            return [""] * len(doc.paragraphs)
        counters = _Counters(*_definitions(root))
        by_element = {}
        for p_el in doc.element.body.iter(qn("w:p")):  # table cells count too, like Word
            if p_el.xpath("ancestor::w:txbxContent"):
                continue
            try:
                num_id, ilvl = _paragraph_numbering(Paragraph(p_el, doc._body))
                by_element[p_el] = counters.label(num_id, ilvl)
            except Exception:
                by_element[p_el] = ""
        return [by_element.get(p._p, "") for p in doc.paragraphs]
    except Exception:
        return [""] * len(doc.paragraphs)
