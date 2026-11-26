import pytest
from docx import Document
from docx.shared import Inches


@pytest.fixture
def build_docx(tmp_path):
    """build(paragraphs, page=(w, h), margins=(top, bottom, left, right)) -> path."""
    counter = {"n": 0}

    def build(paragraphs, page=(8.5, 11.0), margins=(0.75, 1.0, 0.625, 0.625)):
        doc = Document()
        sec = doc.sections[0]
        sec.page_width, sec.page_height = Inches(page[0]), Inches(page[1])
        sec.top_margin, sec.bottom_margin = Inches(margins[0]), Inches(margins[1])
        sec.left_margin, sec.right_margin = Inches(margins[2]), Inches(margins[3])
        for text in paragraphs:
            doc.add_paragraph(text)
        counter["n"] += 1
        path = tmp_path / f"doc{counter['n']}.docx"
        doc.save(path)
        return str(path)

    return build
