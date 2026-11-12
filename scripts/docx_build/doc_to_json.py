# ruff: noqa: SIM115   build tooling: plain scripts, not library code
"""Convert a Claude Docs prose read (the raw tool result JSON saved to a file) into
manuscript.json for build_docx.js.

Usage: python doc_to_json.py doc_read.json figures_dir manuscript.json
Blocks handled: paragraph (heading='1|2|3' or body), list (ordered/bullet), table, embed
(figure, matched by 'Figure N' in its caption), pending (skipped). Inline: <bold>, citation
groups like (1,2) or (4–15) become cite parts; everything else is text.
"""
import html
import json
import os
import re
import sys

src, figdir, out = sys.argv[1:4]
raw = open(src, encoding="utf-8").read()
# the saved tool result may be a JSON list with a text field holding JSON, or the JSON itself
def _find_result(obj):
    """The saved tool result may be the JSON object, a JSON string, or a list of {type, text}
    parts of which one holds the JSON (others are notices)."""
    if isinstance(obj, dict) and "data" in obj:
        return obj
    if isinstance(obj, list):
        for item in obj:
            t = item.get("text", "") if isinstance(item, dict) else ""
            i = t.find("{")
            if i >= 0:
                try:
                    cand = json.JSONDecoder().raw_decode(t[i:])[0]
                except json.JSONDecodeError:
                    continue
                if isinstance(cand, dict) and "data" in cand:
                    return cand
    raise ValueError("no doc read result found in the saved file")


try:
    d = _find_result(json.loads(raw))
except json.JSONDecodeError:
    d = _find_result(json.JSONDecoder().raw_decode(raw[raw.find("{"):])[0])
xml = d["data"]["xml"]

FIG_FILES = {1: "figure1_validation.png", 2: "figure2_pair_ratios.png", 3: "figure3_onset.png",
             4: "figure4_summary.png", 5: "figure5_text_matched.png"}
FIG_ASPECT = {1: 738 / 1344, 2: 784 / 1344, 3: 720 / 1344, 4: 898 / 1344, 5: 1512 / 1344}
CITE = re.compile(r"\((\d{1,2}(?:[,–—-]\d{1,2})*)\)")


def expand(group: str):
    nums = []
    for part in group.split(","):
        if re.search(r"[–—-]", part):
            a, b = re.split(r"[–—-]", part)
            nums.extend(range(int(a), int(b) + 1))
        else:
            nums.append(int(part))
    return nums


def inline(frag: str):
    """XML fragment of a paragraph's children -> list of parts."""
    parts = []
    # tokens: <bold>..</bold>, <italic>..</italic>, text, chips
    for m in re.finditer(r"<(bold|italic)>(.*?)</\1>|<text[^>]*>(.*?)</text>|<(date|mention)[^>]*/>", frag, re.DOTALL):
        if m.group(1):
            inner = re.sub(r"<[^>]+>", "", m.group(2))
            parts.append({"text": html.unescape(inner), m.group(1) == "bold" and "bold" or "italic": True})
        elif m.group(3) is not None:
            inner = m.group(3)
            # nested bold inside text
            for b in re.finditer(r"<(bold|italic)>(.*?)</\1>|([^<]+)", inner, re.DOTALL):
                if b.group(1):
                    parts.append({"text": html.unescape(re.sub(r"<[^>]+>", "", b.group(2))), b.group(1) == "bold" and "bold" or "italic": True})
                elif b.group(3):
                    parts.append({"text": html.unescape(b.group(3))})
        else:
            parts.append({"text": "2026-11-12" if m.group(4) == "date" else "Matthew Halma"})
    # split citations out of plain text parts
    out = []
    for p in parts:
        if p.get("bold") or p.get("italic") or not p.get("text"):
            out.append(p)
            continue
        t, last = p["text"], 0
        for c in CITE.finditer(t):
            if c.start() > last:
                out.append({"text": t[last:c.start()]})
            out.append({"cite": expand(c.group(1))})
            last = c.end()
        if last < len(t):
            out.append({"text": t[last:]})
    return out or [{"text": ""}]


blocks = []
# top-level blocks: paragraph, list, table, embed, pending
for m in re.finditer(r"<(paragraph|list|table|embed|pending)\b([^>]*)(?:/>|>(.*?)</\1>)", xml, re.DOTALL):
    kind, attrs, body = m.group(1), m.group(2), m.group(3) or ""
    if kind == "pending":
        continue
    if kind == "paragraph":
        h = re.search(r"heading='(\d)'", attrs)
        text_parts = inline(body)
        plain = "".join(p.get("text", "") for p in text_parts).strip()
        if h and h.group(1) == "1":
            blocks.append({"type": "title", "text": plain})
        elif h:
            blocks.append({"type": "heading", "level": int(h.group(1)), "text": plain})
        elif "<date" in body and "<mention" in body:
            blocks.append({"type": "byline", "text": plain})
        elif plain:
            blocks.append({"type": "para", "parts": text_parts})
    elif kind == "list":
        ordered = "kind='ordered'" in attrs
        start = re.search(r"start='(\d+)'", attrs)
        items = [inline(li) for li in re.findall(r"<listItem[^>]*>(.*?)</listItem>", body, re.DOTALL)]
        if ordered and any(p.get("text", "").startswith(("Bellavite", "Platschek")) for it in items for p in it[:1]) or ordered and start:
            blocks.append({"type": "bibl_part", "items": items})
        else:
            blocks.append({"type": "list", "ordered": ordered, "items": items})
    elif kind == "table":
        rows = []
        for r in re.findall(r"<row[^>]*>(.*?)</row>", body, re.DOTALL):
            cells = re.findall(r"<cell[^>]*>(.*?)</cell>", r, re.DOTALL)
            rows.append([inline(re.sub(r"</?paragraph[^>]*>", "", c)) for c in cells])
        if rows:
            blocks.append({"type": "table", "header": rows[0], "rows": rows[1:]})
    elif kind == "embed":
        cap = html.unescape(re.search(r"caption='([^']*)'", attrs).group(1))
        n = int(re.search(r"Figure (\d)", cap).group(1))
        blocks.append({"type": "figure", "file": os.path.join(figdir, FIG_FILES[n]), "aspect": FIG_ASPECT[n],
                       "caption": [{"text": f"Figure {n}. ", "bold": True}, {"text": cap.split("·", 1)[1].strip() if "·" in cap else cap}]})

# merge the bibliography parts (list starting at 1, then lists starting at 18, 19) into one bibl
merged, bib = [], []
for b in blocks:
    if b["type"] == "bibl_part":
        for it in b["items"]:
            bib.append(f"{len(bib) + 1}. " + "".join(p.get("text", "") for p in it))
    else:
        if bib:
            merged.append({"type": "bibl", "entries": bib}); bib = []
        merged.append(b)
if bib:
    merged.append({"type": "bibl", "entries": bib})
# give each ordered list its own numbering instance so numbering restarts
inst = 0
for b in merged:
    if b["type"] == "list" and b["ordered"]:
        b["instance"] = inst; inst += 1
# table captions: a preceding bold "Table N." paragraph becomes the caption
final = []
for b in merged:
    if b["type"] == "table" and final and final[-1]["type"] == "para" and final[-1]["parts"] and \
            final[-1]["parts"][0].get("bold") and final[-1]["parts"][0]["text"].startswith("Table"):
        b["caption"] = final.pop()["parts"]
    final.append(b)
json.dump({"blocks": final}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(final), "blocks;", sum(1 for b in final if b["type"] == "figure"), "figures;",
      sum(1 for b in final if b["type"] == "table"), "tables;",
      [len(b["entries"]) for b in final if b["type"] == "bibl"], "bibliography entries")
