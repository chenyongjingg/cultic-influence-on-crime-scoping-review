#!/usr/bin/env python3
"""Export a DOCX to PDF through Word (COM), so the PDF is the document a reader sees.

Word is used rather than a headless converter because the only reliable way to check
that the journal styles survived is to look at the page the journal's own template
would produce. The script fails loudly if Word cannot open the file — a silently
empty export is worse than no export.
"""
import os, sys, time
import win32com.client as win32

src = os.path.abspath(sys.argv[1])
dst = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.splitext(src)[0] + ".pdf"
if not os.path.exists(src):
    sys.exit("missing: %s" % src)
if os.path.exists(dst):
    os.remove(dst)

word = win32.DispatchEx("Word.Application")
word.Visible = False
word.DisplayAlerts = 0
doc = None
try:
    doc = word.Documents.Open(src, ReadOnly=True, AddToRecentFiles=False)
    doc.SaveAs(dst, FileFormat=17)  # wdFormatPDF
finally:
    if doc is not None:
        doc.Close(False)
    word.Quit()

for _ in range(20):
    if os.path.exists(dst) and os.path.getsize(dst) > 1000:
        break
    time.sleep(0.5)
print("PDF:", dst, os.path.getsize(dst) if os.path.exists(dst) else "MISSING")
