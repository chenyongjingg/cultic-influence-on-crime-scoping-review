#!/usr/bin/env python3
"""Final acceptance checks for the submission build.

Each check is an assertion over the built artefacts, not a restatement of intent.
Exit code is non-zero if any check fails.

The corpus these checks describe is the audited one: the machine set of 191 minus
the 28 records the first author excluded after reading the 30 the full-corpus audit
flagged. Every claim below is checked against the built manuscript, so a sentence
that drifts back to the pre-audit wording fails the build.
"""
import io, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(ROOT, "out", "manuscript", "manuscript_numbered.md")
A = json.load(io.open(os.path.join(ROOT, "out", "data", "analysis.json"), encoding="utf8"))
V = json.load(io.open(os.path.join(ROOT, "out", "data", "validation_numbers.json"), encoding="utf8"))
AA = json.load(io.open(os.path.join(ROOT, "out", "data", "author_audit.json"), encoding="utf8"))
REFS = json.load(io.open(os.path.join(ROOT, "src", "refs.json"), encoding="utf8"))["refs"]
S8 = io.open(os.path.join(ROOT, "out", "supplements", "S8_reference_verification.md"), encoding="utf8").read()

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


def main():
    s = io.open(MD, encoding="utf8").read()
    body = s.split("## References")[0]
    flat = re.sub(r"\s+", " ", body)
    N = A["construct_table"][0]["N"]

    # 1. screening is described as it was performed
    check("§2.4 describes the second pass and its weaker test",
          "went to a second pass" in flat and "lexical crime anchor" in flat)
    check("§2.4 gives the machine-set count from the artefact",
          re.search(r"machine set was %d records" % A["adjudication"]["machine_included"], flat) is not None)
    check("Declarations state that no human screening of the full corpus was performed",
          "no independent human screening of the full corpus was performed" in flat)
    check("no sentence claims adjudication is outstanding",
          not re.search(r"adjudication (by the named authors )?remains outstanding|has not yet been performed",
                        flat, re.I))
    check("the audit is cited with its flagged count",
          ("%d records that the full-corpus audit" % A["screening_audit"]["flagged_for_human_read"]["n"]) in flat)
    check("the audit exclusions are reported from the artefact",
          ("excluded %d of them" % AA["author_excluded"]) in flat)

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
    # 191 is now a legitimate number: it is the machine set before the audit
    check("the machine-set count 191 appears only as the pre-audit set",
          len(re.findall(r"\b191\b", body)) <= 1, "%d occurrence(s)" % len(re.findall(r"\b191\b", body)))
    for stray in ("171", "192", "833", "629"):
        check("no stray %s" % stray, not re.search(r"\b%s\b" % stray, body))
    dens = set(re.findall(r"/(\d{2,3})\b", body))
    check("every n/N uses the audited denominator", dens <= {str(N), "42"}, "%s" % sorted(dens))
    check("denominator equals the analysis N", str(N) == "142", str(N))

    # 4. validation paragraph matches the artefact
    t = V["tally"]
    check("validation tally in text matches the artefact",
          ("%d were clearly on topic" % t["Y"]) in flat and
          ("%d were" % t["M"]) in flat and ("%d were not" % t["N"]) in flat,
          "artifact Y/M/N = %d/%d/%d" % (t["Y"], t["M"], t["N"]))
    check("non-qualifying count matches the audited corpus",
          ("of the %d judged not on topic, %d remain" % (t["N"], V["nonqualifying_matched"])) in flat,
          "%d of %d remain" % (V["nonqualifying_matched"], t["N"]))

    # 5. word count line present in the built docx
    import zipfile
    docx = os.path.join(ROOT, "out", "manuscript", "Frontiers_manuscript.docx")
    xml = zipfile.ZipFile(docx).read("word/document.xml").decode("utf8")
    m = re.search(r"Word count:\s*([\d,]+) words", re.sub(r"<[^>]+>", "", xml))
    check("word count rendered into the document", bool(m), m.group(1) if m else "absent")

    for name, ok, detail in results:
        print("%s  %-62s %s" % ("PASS" if ok else "FAIL", name, detail))
    fails = [r for r in results if not r[1]]
    print("\n%d checks, %d failed" % (len(results), len(fails)))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
