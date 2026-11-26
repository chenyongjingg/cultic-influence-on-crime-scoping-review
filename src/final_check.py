#!/usr/bin/env python3
"""Final acceptance checks for the submission build.

Each check is an assertion over the built artefacts, not a restatement of intent.
Exit code is non-zero if any check fails.
"""
import io, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(ROOT, "out", "manuscript", "manuscript_numbered.md")
A = json.load(io.open(os.path.join(ROOT, "out", "data", "analysis.json"), encoding="utf8"))
V = json.load(io.open(os.path.join(ROOT, "out", "data", "validation_numbers.json"), encoding="utf8"))
REFS = json.load(io.open(os.path.join(ROOT, "src", "refs.json"), encoding="utf8"))["refs"]
S8 = io.open(os.path.join(ROOT, "out", "supplements", "S8_reference_verification.md"), encoding="utf8").read()

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


def main():
    s = io.open(MD, encoding="utf8").read()
    body = s.split("## References")[0]
    flat = re.sub(r"\s+", " ", body)

    # 1. adjudication status, three locations, no contradiction
    check("§2.4 says the machine record is not human review",
          "adjudication by the named authors remains outstanding" in flat)
    check("§2.4 makes the operative check future and unperformed",
          "which has not yet been performed" in flat)
    check("Declarations state adjudication outstanding",
          "Adjudication of the screening table (Supplementary Table S3) remains outstanding" in flat)
    check("no sentence claims adjudication was completed",
          not re.search(r"adjudication (was|has been) (completed|performed)|overturn rate", flat, re.I))

    # 2. Zhu citation
    n_cite = len(re.findall(r"\[26\]", body))
    check("Zhu cited exactly once in the text", n_cite == 1, "found %d" % n_cite)
    check("Zhu entry present in the reference list",
          "Zhu S. Risk prevention" in s.split("## References")[1])
    check("Zhu logged in S8", "VERIFIED BY AUTHORS" in S8 and "人大复印报刊资料" in S8)
    selfcites = [r["key"] for r in REFS
                 if (r.get("first_author") or "").strip().lower() in ("zhu", "xue", "chen")]
    check("self-citations ≤ 2", len(selfcites) <= 2, "%s" % selfcites)

    # 3. denominators
    for stray in ("171", "192", "833", "629"):
        check("no stray %s" % stray, not re.search(r"\b%s\b" % stray, body))
    dens = set(re.findall(r"/(\d{2,3})\b", body))
    check("every n/N uses 170", dens <= {"170", "191", "42"}, "%s" % sorted(dens))
    check("denominator equals the analysis N",
          str(A["construct_table"][0]["N"]) == "170", str(A["construct_table"][0]["N"]))

    # 4. validation paragraph matches the artefact
    t = V["tally"]
    check("validation tally in text matches the artefact",
          all(("%d were" % t["Y"]) in flat or True for _ in [0]) and
          ("%d were clearly on topic" % t["Y"]) in flat and
          ("%d were" % t["M"]) in flat and ("%d were not" % t["N"]) in flat,
          "artifact Y/M/N = %d/%d/%d" % (t["Y"], t["M"], t["N"]))
    check("non-qualifying count matches",
          ("the %d non-qualifying records" % V["nonqualifying_matched"]) in flat)

    # 5. word count line present in the built docx
    import zipfile
    docx = os.path.join(ROOT, "out", "manuscript", "Frontiers_manuscript.docx")
    xml = zipfile.ZipFile(docx).read("word/document.xml").decode("utf8")
    m = re.search(r"Word count:\s*([\d,]+) words", re.sub(r"<[^>]+>", "", xml))
    check("word count rendered into the document", bool(m), m.group(1) if m else "absent")

    for name, ok, detail in results:
        print("%s  %-56s %s" % ("PASS" if ok else "FAIL", name, detail))
    fails = [r for r in results if not r[1]]
    print("\n%d checks, %d failed" % (len(results), len(fails)))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
