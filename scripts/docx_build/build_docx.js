// Build the manuscript .docx from manuscript.json. Citations are emitted as placeholder runs
// (⟦CITE:1,2⟧) and the bibliography as ⟦BIBL⟧ paragraphs; zotero_fields.py turns them into
// Zotero fields afterwards. Usage: node build_docx.js manuscript.json out.docx
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType,
  ImageRun, AlignmentType, BorderStyle, ShadingType, LevelFormat, PageBreak,
} = require("docx");

const [, , jsonPath, outPath] = process.argv;
const ms = JSON.parse(fs.readFileSync(jsonPath, "utf8"));
const FONT = "Arial";
const PAGE_W = 12240, MARGIN = 1440, TEXT_W = PAGE_W - 2 * MARGIN;   // US Letter, 1" margins

function runs(parts, base = {}) {
  // parts: [{text, bold, italic}, {cite:[n,...]}]
  const out = [];
  for (const p of parts) {
    if (p.cite) {
      out.push(new TextRun({ text: `⟦CITE:${p.cite.join(",")}⟧`, font: FONT, size: 22, ...base }));
    } else {
      out.push(new TextRun({ text: p.text, bold: !!p.bold, italics: !!p.italic, font: FONT, size: 22, ...base }));
    }
  }
  return out;
}

const border = { style: BorderStyle.SINGLE, size: 4, color: "999999" };
const borders = { top: border, bottom: border, left: border, right: border };

function cell(parts, width, header) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    borders,
    shading: header ? { type: ShadingType.CLEAR, fill: "EEEEEE", color: "auto" } : undefined,
    margins: { top: 60, bottom: 60, left: 80, right: 80 },
    children: [new Paragraph({ children: runs(parts, { size: 18, bold: header || undefined }), spacing: { before: 0, after: 0 } })],
  });
}

function table(t) {
  const ncol = t.header.length;
  const widths = t.widths ? t.widths.map(w => Math.round(w * TEXT_W)) : Array(ncol).fill(Math.floor(TEXT_W / ncol));
  const diff = TEXT_W - widths.reduce((a, b) => a + b, 0);
  widths[widths.length - 1] += diff;
  const rows = [new TableRow({ tableHeader: true, children: t.header.map((h, i) => cell(h, widths[i], true)) })];
  for (const r of t.rows) rows.push(new TableRow({ children: r.map((c, i) => cell(c, widths[i], false)) }));
  return new Table({ width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: widths, rows });
}

const children = [];
let numberingUsed = false;
for (const b of ms.blocks) {
  switch (b.type) {
    case "title":
      children.push(new Paragraph({ heading: HeadingLevel.TITLE, children: runs([{ text: b.text }], { size: 32, bold: true }) }));
      break;
    case "byline":
      children.push(new Paragraph({ children: runs(b.parts || [{ text: b.text }]), spacing: { before: 0, after: 240 } }));
      break;
    case "heading": {
      const lvl = { 1: HeadingLevel.HEADING_1, 2: HeadingLevel.HEADING_2, 3: HeadingLevel.HEADING_3 }[b.level];
      children.push(new Paragraph({ heading: lvl, children: runs([{ text: b.text }], { bold: true, size: b.level === 1 ? 28 : b.level === 2 ? 24 : 22 }) }));
      break;
    }
    case "para":
      children.push(new Paragraph({ children: runs(b.parts), spacing: { before: 0, after: 160, line: 300 }, alignment: AlignmentType.LEFT }));
      break;
    case "list":
      numberingUsed = true;
      for (const item of b.items) {
        children.push(new Paragraph({
          children: runs(item), spacing: { before: 0, after: 80, line: 300 },
          numbering: { reference: b.ordered ? "num" : "bul", level: 0, instance: b.instance || 0 },
        }));
      }
      break;
    case "table":
      if (b.caption) children.push(new Paragraph({ children: runs(b.caption, { bold: true, size: 20 }), spacing: { before: 200, after: 80 }, keepNext: true }));
      children.push(table(b));
      if (b.note) children.push(new Paragraph({ children: runs(b.note, { size: 18 }), spacing: { before: 60, after: 200 } }));
      else children.push(new Paragraph({ children: [], spacing: { before: 0, after: 160 } }));
      break;
    case "figure": {
      const buf = fs.readFileSync(b.file);
      const scale = b.width || 1.0;
      const w = Math.round(6.3 * 96 * scale), h = Math.round(w * b.aspect);
      children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200, after: 80 }, keepNext: true,
        children: [new ImageRun({ type: "png", data: buf, transformation: { width: w, height: h } })] }));
      children.push(new Paragraph({ children: runs(b.caption, { size: 20 }), spacing: { before: 0, after: 240 } }));
      break;
    }
    case "bibl":
      children.push(new Paragraph({ children: runs([{ text: "⟦BIBL⟧" }]) }));
      for (const e of b.entries) children.push(new Paragraph({ style: "Bibliography", children: runs([{ text: `⟦BIBENTRY⟧${e}` }], { size: 20 }), spacing: { before: 0, after: 100 } }));
      children.push(new Paragraph({ children: runs([{ text: "⟦/BIBL⟧" }]) }));
      break;
    case "pagebreak":
      children.push(new Paragraph({ children: [new PageBreak()] }));
      break;
  }
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Bibliography", name: "Bibliography", basedOn: "Normal", next: "Normal", run: { font: FONT, size: 20 }, paragraph: { spacing: { before: 0, after: 100 }, indent: { left: 360, hanging: 360 } } },
    ],
    title: { run: { font: FONT, size: 32, bold: true }, paragraph: { spacing: { before: 0, after: 120 }, alignment: AlignmentType.LEFT } },
    heading1: { run: { font: FONT, size: 28, bold: true }, paragraph: { spacing: { before: 360, after: 120 }, keepNext: true } },
    heading2: { run: { font: FONT, size: 24, bold: true }, paragraph: { spacing: { before: 280, after: 100 }, keepNext: true } },
    heading3: { run: { font: FONT, size: 22, bold: true, italics: true }, paragraph: { spacing: { before: 200, after: 80 }, keepNext: true } },
  },
  numbering: {
    config: [
      { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] },
      { reference: "num", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 360 } } } }] },
    ],
  },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: 15840 }, margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN } } },
    children,
  }],
});

Packer.toBuffer(doc).then(buf => { fs.writeFileSync(outPath, buf); console.log("wrote", outPath, buf.length, "bytes"); });
