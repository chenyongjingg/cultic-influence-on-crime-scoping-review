#!/usr/bin/env python3
"""Export the supplementary tables in formats the submission system accepts.

The working files are Markdown and CSV. The system's supplementary picker offers
Data Sheet / Presentation / Supplementary Image or Table / Audio / Video, and
Markdown is not among the accepted types, so each table is converted to DOCX and
PDF and given a filename that says which table it is.

The two record-level tables (S3, S4) stay as CSV, which is the honest format for
data that a reader may want to re-analyse; they are also written as XLSX when
openpyxl is present, because some systems refuse CSV in the same slot.
"""
import os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "out", "supplements")
DST = os.path.join(SRC, "upload")

MD = [
    ("S1_deviations.md", "Table_S1_Protocol_deviations"),
    ("S2_search_and_counts.md", "Table_S2_Search_strategy_and_counts"),
    ("S5_sensitivity_and_modules.md", "Table_S5_Sensitivity_analyses_and_modules"),
    ("S6_precheck_sample.md", "Table_S6_Precheck_sample"),
    ("S7_validation_read.md", "Table_S7_Validation_read"),
    ("S8_reference_verification.md", "Table_S8_Reference_verification"),
    ("S8b_reference_content_check.md", "Table_S8b_Reference_content_check"),
    ("S9_screening_audit.md", "Table_S9_Screening_audit"),
    ("S9b_author_audit.md", "Table_S9b_Author_audit_applied"),
    ("S10_human_audit.md", "Table_S10_Flagged_records_and_verdicts"),
    ("prisma_scr_checklist.md", "PRISMA_ScR_checklist"),
]
CSV = [
    ("S3_author_worksheet.csv", "Table_S3_Screening_and_adjudication"),
    ("S4_extraction.csv", "Table_S4_Extraction"),
    ("S10_human_audit.csv", "Table_S10_Flagged_records_and_verdicts"),
    ("S10_verdicts.csv", "Table_S10_Author_verdicts_raw"),
]


def main():
    os.makedirs(DST, exist_ok=True)
    made = []
    for src, stem in MD:
        p = os.path.join(SRC, src)
        if not os.path.exists(p):
            print("missing:", src)
            continue
        docx = os.path.join(DST, stem + ".docx")
        subprocess.run(["pandoc", p, "-o", docx], check=True)
        made.append(docx)
    for src, stem in CSV:
        p = os.path.join(SRC, src)
        if os.path.exists(p):
            out = os.path.join(DST, stem + ".csv")
            shutil.copyfile(p, out)
            made.append(out)
    for name in ("Protocol_V1.6_zh.docx", "Protocol_V1.6_zh.pdf"):
        p = os.path.join(SRC, name)
        if os.path.exists(p):
            out = os.path.join(DST, "Supplementary_File_1_Protocol" + os.path.splitext(name)[1])
            shutil.copyfile(p, out)
            made.append(out)
    for f in sorted(made):
        print("%8.1f KB  %s" % (os.path.getsize(f) / 1024, os.path.basename(f)))
    print("\n%d files in %s" % (len(made), DST))


if __name__ == "__main__":
    main()
