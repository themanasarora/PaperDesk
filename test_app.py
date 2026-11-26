import io, glob, tempfile, os
from docx import Document
from docx.shared import Pt
import app, suggest

c = app.app.test_client()
tmpdir = tempfile.gettempdir()
before = set(glob.glob(os.path.join(tmpdir, "*.docx")))

def post(name, data, fn=None):
    return c.post("/check", data={"paper": (io.BytesIO(data), fn or name)}, content_type="multipart/form-data")

r = c.get("/"); print("GET /:", r.status_code, "upload form" if b"Check my paper" in r.data else "MISSING FORM")

clean = open("samples/test_paper_clean.docx","rb").read()
flawed = open("samples/test_paper_flawed.docx","rb").read()
r = post("c.docx", clean); print("clean:", r.status_code, "0 errors" if b"0 errors, 0 warnings" in r.data else "UNEXPECTED")
r = post("f.docx", flawed); print("flawed:", r.status_code, "9 errors, 3 warnings" if b"9 errors, 3 warnings" in r.data else "UNEXPECTED")
r = post("notes.txt", b"hello"); print("txt upload:", r.status_code, b"Only Word" in r.data)
r = post("fake.docx", b"not a zip at all"); print("fake docx:", r.status_code, b"valid .docx" in r.data)
r = post("bad.docx", b"PK\x03\x04garbagegarbage"); print("corrupt zip:", r.status_code, b"Could not read" in r.data)
r = c.post("/check", data={}, content_type="multipart/form-data"); print("no file:", r.status_code)

# HTML escaping: paragraph with script tag in wrong font
d = Document(); d.add_paragraph("Title"); d.add_paragraph("Test Author")
d.add_paragraph("Abstract—short"); 
p = d.add_paragraph(); run = p.add_run("<script>alert(1)</script> text"); run.font.name = "Arial"
buf = io.BytesIO(); d.save(buf)
r = post("x.docx", buf.getvalue())
print("escaping:", r.status_code, "escaped" if b"&lt;script&gt;" in r.data and b"<script>alert" not in r.data else "NOT ESCAPED")

after = set(glob.glob(os.path.join(tmpdir, "*.docx")))
print("leftover temp files:", len(after - before))

# suggest safeguards
print("no key -> available:", suggest.available(), "| suggest returns:", suggest.suggest([(1, "text")]))
o = "Models like BERT [2] reach 91.5 percent accuracy."
print("keeps content:", suggest.preserves_content(o, "Models such as BERT [2] reach 91.5 percent accuracy."))
print("blocks number change:", not suggest.preserves_content(o, "Models like BERT [2] reach 95.1 percent accuracy."))
print("blocks citation change:", not suggest.preserves_content(o, "Models like BERT [3] reach 91.5 percent accuracy."))
