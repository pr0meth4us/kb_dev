#!/usr/bin/env python3
"""Transcribe a .docx to markdown, keeping paragraphs and tables in body order.

Usage:
  python3 scripts/docx_to_md.py <input.docx> <output.md> [--note "..."]
"""
import argparse
from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


def cell_text(cell):
    return " <br> ".join(p.text.strip() for p in cell.paragraphs if p.text.strip()).replace("|", "\\|")


def table_md(table):
    rows = []
    for row in table.rows:
        cells, seen = [], set()
        for c in row.cells:  # merged cells repeat; keep each once
            if id(c._tc) in seen:
                continue
            seen.add(id(c._tc))
            cells.append(cell_text(c))
        rows.append(cells)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * width]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(out)


def para_md(p):
    text = p.text.strip()
    if not text:
        return ""
    style = (p.style.name or "").lower()
    if style.startswith("heading"):
        level = "".join(ch for ch in style if ch.isdigit()) or "1"
        return "#" * min(int(level) + 1, 6) + " " + text
    if "list" in style or p._p.pPr is not None and p._p.pPr.numPr is not None:
        return "- " + text
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--note", default="")
    a = ap.parse_args()
    doc = Document(a.src)
    blocks = []
    for child in doc.element.body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            blocks.append(para_md(Paragraph(child, doc)))
        elif tag == "tbl":
            blocks.append(table_md(Table(child, doc)))
    header = f"<!-- Transcribed from {Path(a.src).name} with scripts/docx_to_md.py. {a.note} -->"
    Path(a.out).write_text(header + "\n\n" + "\n\n".join(b for b in blocks if b) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
