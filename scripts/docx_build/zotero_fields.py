# ruff: noqa: SIM115   build tooling: plain scripts, not library code
"""Turn ⟦CITE:n,m⟧ placeholder runs and the ⟦BIBL⟧ block into Zotero fields, and copy the
Zotero document preferences (docProps/custom.xml) from the user's own file.

Usage: python zotero_fields.py in.docx out.docx zotero_items.json extra_items.json custom.xml
"""
import json
import os
import random
import re
import shutil
import string
import sys
import tempfile
import zipfile
from xml.sax.saxutils import escape

src, dst, items_path, extra_path, custom_path = sys.argv[1:6]
lib = json.load(open(items_path, encoding="utf-8"))
extra = json.load(open(extra_path, encoding="utf-8"))
# numbering: 1..17 in the order the user's file cites them (lib["order"]), then extras
numbered = {i + 1: lib["items"][k] for i, k in enumerate(lib["order"])}
for n, it in extra.items():
    numbered[int(n)] = it
SCHEMA = "https://github.com/citation-style-language/schema/raw/master/csl-citation.json"


def cid():
    return "".join(random.choices(string.ascii_letters + string.digits, k=8))


def fld(instr, result_runs):
    return ('<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
            f'<w:r><w:instrText xml:space="preserve"> {escape(instr)} </w:instrText></w:r>'
            '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
            f'{result_runs}'
            '<w:r><w:fldChar w:fldCharType="end"/></w:r>')


def cite_field(nums, rpr):
    items = []
    for n in nums:
        it = numbered[n]
        items.append({"id": it["id"], "uris": it["uris"], "itemData": it["itemData"]})
    # Springer / Vancouver with brackets; consecutive runs collapse to a range, as the style does
    runs, start = [], None
    for i, n in enumerate(nums):
        if start is None:
            start = n
        if i == len(nums) - 1 or nums[i + 1] != n + 1:
            runs.append(str(start) if start == n else (f"{start},{n}" if n == start + 1 else f"{start}–{n}"))
            start = None
    plain = "[" + ",".join(runs).replace(",", ", ") + "]"
    data = {"citationID": cid(),
            "properties": {"formattedCitation": plain, "plainCitation": plain, "noteIndex": 0},
            "citationItems": items, "schema": SCHEMA}
    instr = "ADDIN ZOTERO_ITEM CSL_CITATION " + json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return fld(instr, f'<w:r>{rpr}<w:t xml:space="preserve">{escape(plain)}</w:t></w:r>')


tmp = tempfile.mkdtemp()
with zipfile.ZipFile(src) as z:
    z.extractall(tmp)
docp = os.path.join(tmp, "word", "document.xml")
xml = open(docp, encoding="utf-8").read()

# 1. citations: a whole run whose text is exactly the placeholder
run_re = re.compile(r'<w:r>(?:(?!</w:r>).)*?⟦CITE:([0-9,]+)⟧(?:(?!</w:r>).)*?</w:r>', re.DOTALL)


def repl_cite(m):
    nums = [int(x) for x in m.group(1).split(",")]
    rpr = re.search(r'<w:rPr>.*?</w:rPr>', m.group(0), re.DOTALL)
    return cite_field(nums, rpr.group(0) if rpr else "")


xml, n_cites = run_re.subn(repl_cite, xml)

# 2. bibliography: paragraphs between ⟦BIBL⟧ and ⟦/BIBL⟧ become one ZOTERO_BIBL field
start = xml.index("⟦BIBL⟧")
end = xml.index("⟦/BIBL⟧")
p_start = xml.rfind("<w:p>", 0, start)
p_end = xml.index("</w:p>", end) + len("</w:p>")
block = xml[p_start:p_end]
entries = re.findall(r'<w:p>.*?</w:p>', block, re.DOTALL)[1:-1]   # drop the marker paragraphs
bibl_instr = 'ADDIN ZOTERO_BIBL {"uncited":[],"omitted":[],"custom":[]} CSL_BIBLIOGRAPHY'
out_paras = []
for i, p in enumerate(entries):
    p = p.replace("⟦BIBENTRY⟧", "")
    if i == 0:
        # open the field before the first run of the first paragraph
        p = re.sub(r'(<w:p>(?:<w:pPr>.*?</w:pPr>)?)', lambda m: m.group(1) + '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
                   f'<w:r><w:instrText xml:space="preserve"> {escape(bibl_instr)} </w:instrText></w:r>'
                   '<w:r><w:fldChar w:fldCharType="separate"/></w:r>', p, count=1, flags=re.DOTALL)
    if i == len(entries) - 1:
        p = p[:-len("</w:p>")] + '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>'
    out_paras.append(p)
xml = xml[:p_start] + "".join(out_paras) + xml[p_end:]
open(docp, "w", encoding="utf-8").write(xml)

# 3. Zotero prefs: docProps/custom.xml + rel + content type
custom = open(custom_path, encoding="utf-8").read()
custom = custom.replace("http://www.zotero.org/styles/nlm-citation-sequence",
                        "http://www.zotero.org/styles/springer-vancouver-brackets")
open(os.path.join(tmp, "docProps", "custom.xml"), "w", encoding="utf-8").write(custom)
rels_p = os.path.join(tmp, "_rels", ".rels")
rels = open(rels_p, encoding="utf-8").read()
if "custom.xml" not in rels:
    rels = rels.replace("</Relationships>",
                        '<Relationship Id="rIdCustom" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties" Target="docProps/custom.xml"/></Relationships>')
    open(rels_p, "w", encoding="utf-8").write(rels)
ct_p = os.path.join(tmp, "[Content_Types].xml")
ct = open(ct_p, encoding="utf-8").read()
if "custom.xml" not in ct:
    ct = ct.replace("</Types>",
                    '<Override PartName="/docProps/custom.xml" ContentType="application/vnd.openxmlformats-officedocument.custom-properties+xml"/></Types>')
    open(ct_p, "w", encoding="utf-8").write(ct)

if os.path.exists(dst):
    os.remove(dst)
with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(tmp):
        for f in files:
            full = os.path.join(root, f)
            z.write(full, os.path.relpath(full, tmp).replace(os.sep, "/"))
shutil.rmtree(tmp)
print(f"{n_cites} citation fields, {len(entries)} bibliography entries -> {dst}")
