# Word build for the submission

Turns the manuscript (a Claude Doc read saved as JSON) into `docs/submission/manuscript.docx`
with live Zotero fields, then the supplement, cover letter and RECORD checklist with pandoc.

```
npm install docx@9.5.1                                   # once, in this folder
python doc_to_json.py doc_read.json ../../docs/submission/figures manuscript.json
node build_docx.js manuscript.json raw.docx
python zotero_fields.py raw.docx ../../docs/submission/manuscript.docx zotero_items.json extra_items.json zotero_custom.xml
python ../build_supplement.py && cd ../../docs/submission && pandoc supplement.md -o supplement.docx
pandoc cover-letter.md -o cover-letter.docx && pandoc record-checklist.md -o RECORD-checklist.docx
```

`zotero_items.json` holds the 17 CSL items and library URIs from the author's own Zotero file;
`extra_items.json` holds items 18–22 (OpenVSafe, ICAN, VAERS, MedDRA, Levi & Lu) embedded for the
author to relink. `zotero_custom.xml` carries the Zotero document preferences; the style is set to
Springer NLM/Vancouver (brackets). No participant data is involved anywhere in this folder.
