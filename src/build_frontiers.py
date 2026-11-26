#!/usr/bin/env python3
"""Build the Frontiers-formatted DOCX from the filled markdown.

Two things are borrowed rather than invented:
  * the paragraph styles come from a manuscript that was actually submitted to this
    journal (Title 16 pt bold centred, Normal Times New Roman 12 pt, Heading 1/2/3),
    passed to pandoc as --reference-doc;
  * the front-matter block follows the same file's layout (Author List, affiliation,
    correspondence, running title, keywords, article type).

The word count on the first page is computed here from the main text, excluding the
abstract, figure captions, tables and references, because Frontiers asks for that
number rather than for the file's total.
"""
import argparse, io, os, re, subprocess, sys

from docx import Document
from docx.shared import Pt

FRONT_PREFIXES = ("Authors:", "Affiliation:", "Correspondence:",
                  "Running title:", "Keywords:", "Article type:", "Word count:")


def strip_placeholders(s):
    return re.sub(r"\{\{[^}]+\}\}", "", s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", default="out/manuscript/manuscript_numbered.md")
    ap.add_argument("--reference", default=r"D:/Frontier综述/project/submission/upload/Manuscript.docx")
    ap.add_argument("--out", default="out/manuscript/Frontiers_manuscript.docx")
    ap.add_argument("--figdir", default="out/figures")
    args = ap.parse_args()

    md = io.open(args.md, encoding="utf8").read()

    # ---- word count: main text only, from Introduction to before References
    body = md.split("\n## 1. Introduction", 1)[1].split("\n## References", 1)[0]
    body = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", body)          # images
    body = re.sub(r"^##+ .*$", "", body, flags=re.M)          # headings
    body = re.sub(r"^\*\*Figure [0-9S]+\.\*\*.*$", "", body, flags=re.M)
    body = re.sub(r"^\|.*$", "", body, flags=re.M)            # table rows
    words = len(re.findall(r"\b[\w’'-]+\b", strip_placeholders(body)))
    md = md.replace("{{WORDCOUNT}}", "{:,}".format(words))

    # ---- split front matter for pandoc's title block
    lines = md.split("\n")
    title = lines[0].lstrip("# ").strip()
    tmp = "out/manuscript/_frontiers_tmp.md"
    rest = "\n".join(lines[1:])
    # promote every heading one level: with the title in the YAML block, pandoc maps
    # '#' to Heading 1, so the section headings have to start at one '#'
    rest = re.sub(r"^(#{2,5}) ", lambda m: "#" * (len(m.group(1)) - 1) + " ", rest, flags=re.M)
    io.open(tmp, "w", encoding="utf8").write("---\ntitle: \"%s\"\n---\n%s" % (title.replace('"', "'"), rest))

    cmd = ["pandoc", tmp, "-o", args.out, "--resource-path", args.figdir,
           "--reference-doc", args.reference]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-800:]); sys.exit(1)

    # ---- apply the Frontmatter styles that pandoc does not map by itself
    doc = Document(args.out)
    for para in doc.paragraphs:
        t = para.text.strip()
        if any(t.startswith(p) for p in FRONT_PREFIXES):
            para.style = doc.styles["Author List"]
        elif t == "Abstract":
            para.style = doc.styles["Author List"]
        elif t.startswith("**Title.**"):
            pass
    # keep the label bold
    for para in doc.paragraphs:
        t = para.text.strip()
        if any(t.startswith(p) for p in FRONT_PREFIXES) and para.runs:
            para.runs[0].bold = True
    # keep each figure caption with the image that follows it
    for para in doc.paragraphs:
        if para.text.strip().startswith("Figure ") or para.text.strip().startswith("Table "):
            para.paragraph_format.keep_with_next = True

    # tables: Frontiers sets table text smaller than body text so five columns fit
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    para.paragraph_format.space_before = Pt(0)
                    para.paragraph_format.space_after = Pt(0)
                    for run in para.runs:
                        run.font.size = Pt(9)
                        run.font.name = "Times New Roman"

    doc.save(args.out)

    print("main-text words:", words)
    print("written:", args.out, os.path.getsize(args.out), "bytes")


if __name__ == "__main__":
    main()
