#!/usr/bin/env python3
"""Stage 7: rule-based reporting-completeness measurement.

Why rules rather than a language model for this stage.  The quantity being
measured is lexical: does the title/abstract state X.  A documented rule has
three properties the model did not have in the pilot: it returns the same answer
on every run, its matched span IS the anchor (so verification is not a second
step that can fail), and any reader can inspect the term list and disagree with
it.  The pilot's model-based extraction marked all twelve constructs "not
reported" for abstracts that plainly named an offence type and a jurisdiction;
that is a failure of sensitivity, and a count built on it would understate the
very thing the paper measures.

Each detector returns (bool, span).  Spans are reported in the supplementary
extraction table so every flag can be checked against the source in one step.

Scope: title + abstract only.  Stated in the manuscript.
"""
import argparse, json, os, re, sys

ROOT = "/root/cultcrime"

GROUP_TERMS = r"(?:cult|cults|cultic|sect|sects|high[- ]control group|high[- ]demand group|" \
              r"destructive cult|new religious movement|new religious movements|charismatic group|commune)"
ROLE_TERMS = ["leader", "leaders", "leadership", "founder", "guru", "prophet", "core member",
              "core members", "rank-and-file", "follower", "followers", "ordinary member",
              "ordinary members", "recruit", "recruits", "defector", "defectors", "former member",
              "former members", "ex-member", "ex-members", "executor", "executors", "lieutenant",
              "inner circle", "outer circle", "victim", "victims"]
MECH_TERMS = ["indoctrination", "thought reform", "mind control", "brainwashing",
              "coercive control", "social isolation", "isolation", "trauma bond",
              "trauma bonding", "groupthink", "group think", "cognitive dissonance",
              "information control", "obedience", "mind control techniques",
              "manipulation", "manipulative", "undue influence", "love bombing",
              "thought stopping", "milieu control", "mystical manipulation",
              "demand for purity", "sacred science", "loaded language", "dispensed existence"]
OFFENCE_TERMS = ["homicide", "murder", "manslaughter", "assassination", "massacre",
                 "sexual abuse", "child abuse", "rape", "sexual assault", "incest",
                 "trafficking", "human trafficking", "slavery", "servitude",
                 "fraud", "financial fraud", "money laundering", "embezzlement", "tax evasion",
                 "assault", "kidnapping", "abduction", "false imprisonment", "imprisonment",
                 "terrorism", "terrorist attack", "arson", "drug trafficking", "drugs",
                 "theft", "burglary", "extortion", "blackmail", "stalking", "harassment",
                 "war crime", "genocide", "battery", "physical violence", "child sexual abuse",
                 "femicide", "poisoning", "chemical weapon", "biological weapon", "sarin"]
SEVERITY_TERMS = ["life sentence", "life imprisonment", "death penalty", "capital punishment",
                  "felony", "misdemeanour", "misdemeanor", "grade", "graded", "severity",
                  "aggravated", "years in prison", "years' imprisonment", "sentence of"]
LEGAL_TERMS = ["convicted", "conviction", "acquitted", "acquittal", "charged", "charge",
               "indicted", "indictment", "sentenced", "sentencing", "verdict", "judgment",
               "judgement", "court ruled", "the court", "tribunal", "found guilty",
               "not guilty", "criminal responsibility", "diminished responsibility",
               "insanity", "plea", "insanity plea", "prosecution", "prosecutor",
               "criminal proceedings", "trial", "appeal", "reduced sentence"]
SOURCE_TERMS = ["clinical", "forensic", "case file", "case files", "court record",
                "court records", "medical record", "police report", "interview", "interviews",
                "survey", "questionnaire", "self-report", "media", "newspaper", "archival",
                "archive", "ethnograph", "fieldwork", "sample of", "were recruited",
                "data were collected", "we collected", "database", "records of"]
COMPARE_TERMS = ["control group", "comparison group", "compared with", "compared to",
                 "in contrast", "baseline", "no comparison", "without a comparison",
                 "versus", "non-cult", "non-member", "non-members", "general population"]

COUNTRIES = ["afghanistan", "albania", "algeria", "argentina", "australia", "austria",
             "belgium", "brazil", "bulgaria", "cameroon", "canada", "chile", "china",
             "colombia", "croatia", "cuba", "czech", "denmark", "ecuador", "egypt",
             "estonia", "ethiopia", "finland", "france", "germany", "ghana", "greece",
             "hungary", "iceland", "india", "indonesia", "iran", "iraq", "ireland",
             "israel", "italy", "jamaica", "japan", "jordan", "kenya", "korea", "kuwait",
             "latvia", "lebanon", "liberia", "libya", "lithuania", "malaysia", "mexico",
             "morocco", "myanmar", "nepal", "netherlands", "new zealand", "nigeria",
             "norway", "pakistan", "peru", "philippines", "poland", "portugal", "qatar",
             "romania", "russia", "rwanda", "saudi", "senegal", "serbia", "singapore",
             "slovakia", "slovenia", "somalia", "south africa", "spain", "sri lanka",
             "sudan", "sweden", "switzerland", "syria", "taiwan", "tanzania", "thailand",
             "tunisia", "turkey", "uganda", "ukraine", "united arab emirates",
             "united kingdom", "great britain", "england", "scotland", "wales", "usa",
             "united states", "uruguay", "uzbekistan", "venezuela", "vietnam", "yemen",
             "zambia", "zimbabwe", "hong kong", "germany's", "poland's"]


def _span(m, text, width=90):
    s = max(0, m.start() - 20); e = min(len(text), m.end() + width)
    return re.sub(r"\s+", " ", text[s:e]).strip()


def any_term(text, terms, flags=re.I):
    pat = re.compile(r"\b(?:" + "|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True)) + r")\b", flags)
    m = pat.search(text)
    return (True, _span(m, text)) if m else (False, "")


def c1_group_def(text):
    """A definitional act applied to the group: define / operationalise / criteria /
    classify within the same sentence as a group term."""
    if not re.search(GROUP_TERMS, text, re.I):
        return (False, "")
    pat = re.compile(r"(definition|defined|define|defining|operationali[sz]\w*|criteria|"
                     r"criteri(?:on|a)|characteri[sz]ed by|classified as|identified as|"
                     r"we regard|distinguished from)", re.I)
    for sent in re.split(r"(?<=[.;!?])\s+", text):
        if re.search(GROUP_TERMS, sent, re.I) and pat.search(sent):
            return True, sent[:180]
    return (False, "")


def c2_role(text):
    found = [t for t in ROLE_TERMS if re.search(r"\b" + re.escape(t) + r"\b", text, re.I)]
    # require at least two distinct role terms: one term alone is a label, not a
    # role distinction (the construct is "distinguishes roles")
    uniq = {t.split()[0].rstrip("s") for t in found}
    if len(uniq) >= 2:
        m = re.search(r"\b" + re.escape(found[0]) + r"\b", text, re.I)
        return True, _span(m, text)
    return (False, found[:2] and "" or "")


def c3_duration(text):
    pats = [r"\b\d+(?:\.\d+)?\s*(?:year|month|week|day)s?\b",
            r"\b\d+\s*-\s*\d+\s*year",
            r"\b(?:years?|months?)\s+(?:in|inside|within|with)\s+(?:the\s+)?(?:group|cult|sect|movement|commune)",
            r"\bsince\s+leaving\b", r"\blength of (?:membership|involvement|stay)\b",
            r"\b(?:remained|stayed|was a member|were members)\s+for\b"]
    for p in pats:
        m = re.search(p, text, re.I)
        if m:
            return True, _span(m, text)
    return (False, "")


def c5_instrument(text):
    m = re.search(r"\b([A-Z][A-Za-z0-9\-]{1,}(?:\s+[A-Z][A-Za-z0-9\-]{1,}){0,5}\s+"
                  r"(?:Scale|Inventory|Questionnaire|Checklist|Test|Index|Survey|Interview|Schedule))\b", text)
    if m:
        return True, m.group(1)
    known = r"\b(GPA|Group Psychological Abuse|MMPI-?2?|PAI|SCL-90|PCL-?R|PCL-?SV|HCR-20|" \
            r"SVR-20|LSI-R|BITE|CAGE|AUDIT|PHQ-9|GAD-7|PTSD|DASS|BPRS|SCID|CAPS)\b"
    m = re.search(known, text)
    return (True, m.group(0)) if m else (False, "")


def c7_severity(text):
    m = re.search(r"\b\d+\s*(?:to\s*\d+\s*)?years?\b(?=[^.]{0,40}(?:prison|sentence|imprison))", text, re.I)
    if m:
        return True, _span(m, text)
    return any_term(text, SEVERITY_TERMS)


def c9_jurisdiction(text):
    m = re.search(r"\b(" + "|".join(re.escape(c) for c in COUNTRIES) + r")\b", text, re.I)
    if m:
        return True, _span(m, text, 60)
    m = re.search(r"\b(?:in|of|under)\s+(?:the\s+)?([A-Z][a-z]+)\s+(?:criminal|penal|legal|justice)\s+"
                  r"(?:code|law|system|court)", text)
    return (True, _span(m, text)) if m else (False, "")


COUNT_NOUNS = (r"participants|subjects|cases|court cases|members|former members|respondents|"
               r"records|articles|studies|papers|interviewees|survivors|offenders|"
               r"documents|court files|files|patients|clients|women|men|individuals|"
               r"persons|people|organisations|organizations|groups|movements|reports|"
               r"publications|texts|judgments|judgements|convictions|defendants|prisoners|"
               r"ex-members|informants|narratives|testimonies")


def c12_n(text):
    m = re.search(r"\bn\s*=\s*\d+\b", text)
    if m:
        return True, _span(m, text, 40)
    m = re.search(r"\b\d{1,5}\s+(?:[a-z\-]+\s+){0,2}(?:" + COUNT_NOUNS + r")\b", text, re.I)
    if m:
        return True, _span(m, text, 40)
    m = re.search(r"\b(?:comprised|consisted of|total of|sample of|we analysed|we analyzed|"
                  r"we reviewed|we examined|we interviewed|includes?)\s+(?:the\s+)?\d{1,5}\b", text, re.I)
    return (True, _span(m, text, 50)) if m else (False, "")


# BITE domains are not matched by their own names ("behaviour control" almost
# never appears literally in an abstract); they are inferred from the techniques
# that constitute each domain in Hassan's formulation.
DOMAIN_MAP = {
    "behaviour": ["isolation", "social isolation", "restriction of movement", "contact restriction",
                  "dress code", "dress", "sleep deprivation", "diet", "food restriction",
                  "financial control", "communal living", "segregation", "confinement"],
    "information": ["information control", "deception", "spying", "media", "censorship",
                    "milieu control", "loaded language", "lies", "secret", "propaganda",
                    "book banning", "surveillance"],
    "thought": ["indoctrination", "thought reform", "mind control", "brainwashing",
                "thought stopping", "cognitive dissonance", "groupthink", "sacred science",
                "doctrine", "absolute truth", "us versus them", "us vs them", "belief system",
                "worldview", "dogma"],
    "emotion": ["trauma bond", "trauma bonding", "guilt", "shame", "fear", "confession",
                "love bombing", "emotional control", "phobia", "anxiety", "dependency",
                "helplessness", "shunning", "exit costs"],
}
CRIME_CATS = [
    ("homicide/murder", ["homicide", "murder", "manslaughter", "assassination", "massacre",
                         "killing", "femicide"]),
    ("sexual abuse", ["sexual abuse", "rape", "sexual assault", "incest", "child sexual abuse",
                      "sexual exploitation"]),
    ("child abuse", ["child abuse", "child neglect", "physical abuse of children"]),
    ("trafficking", ["trafficking", "human trafficking", "sex trafficking", "labour trafficking"]),
    ("fraud/financial", ["fraud", "money laundering", "embezzlement", "tax evasion",
                         "financial crime", "ponzi", "extortion", "blackmail"]),
    ("drug", ["drug trafficking", "narcotics", "drugs", "methamphetamine", "cocaine"]),
    ("assault/violence", ["assault", "battery", "physical violence", "domestic violence",
                          "kidnapping", "abduction", "false imprisonment", "imprisonment"]),
    ("terrorism", ["terrorism", "terrorist attack", "terrorist", "chemical weapon",
                   "biological weapon", "sarin", "bombing", "arson"]),
    ("slavery/servitude", ["slavery", "servitude", "forced labour", "forced labor"]),
]


def bite_domains(text):
    out = []
    for dom, terms in DOMAIN_MAP.items():
        if any(re.search(r"\b" + re.escape(t) + r"\b", text, re.I) for t in terms):
            out.append(dom)
    return out


def crime_categories(text):
    found = []
    for cat, terms in CRIME_CATS:
        if any(re.search(r"\b" + re.escape(t) + r"\b", text, re.I) for t in terms):
            found.append(cat)
    return found or ["other/unspecified"]


DETECTORS = {
    "C1_group_def": c1_group_def,
    "C2_role": c2_role,
    "C3_duration": c3_duration,
    "C4_mechanism": lambda t: any_term(t, MECH_TERMS),
    "C5_instrument": c5_instrument,
    "C6_offence": lambda t: any_term(t, OFFENCE_TERMS),
    "C7_severity": c7_severity,
    "C8_legal": lambda t: any_term(t, LEGAL_TERMS),
    "C9_jurisdiction": c9_jurisdiction,
    "C10_source": lambda t: any_term(t, SOURCE_TERMS),
    "C11_comparison": lambda t: any_term(t, COMPARE_TERMS),
    "C12_n": c12_n,
}
ORDER = list(DETECTORS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inp", default="data/processed/included.jsonl")
    ap.add_argument("--out", default="data/processed/extracted.jsonl")
    args = ap.parse_args()
    recs = [json.loads(l) for l in open(os.path.join(ROOT, args.inp))]
    stats = {"records": 0, "by_construct": {}}
    with open(os.path.join(ROOT, args.out), "w") as f:
        for r in recs:
            ab = (r.get("abstract") or "").strip()
            if len(ab) < 30:
                # no abstract: the measurement is not made.  Recording it as a row
                # of negatives would silently convert missing data into absence,
                # which is exactly the error the reporting set is meant to remove.
                f.write(json.dumps({**r, "extraction": None, "error": "no_abstract"},
                                   ensure_ascii=False) + "\n")
                stats["records_no_abstract"] = stats.get("records_no_abstract", 0) + 1
                continue
            text = re.sub(r"\s+", " ", ((r.get("title") or "") + ". " + ab)).strip()
            clean = {}
            for k, fn in DETECTORS.items():
                v, q = fn(text)
                clean[k] = {"v": bool(v), "q": q}
                if v:
                    stats["by_construct"][k] = stats["by_construct"].get(k, 0) + 1
            clean["bite_domains"] = bite_domains(text)
            clean["crime_types"] = crime_categories(text)
            clean["theory_terms"] = [t for t in ("coercive control", "bounded choice",
                                                 "cognitive dissonance", "groupthink",
                                                 "trauma bond", "differential association",
                                                 "social control", "neutralization",
                                                 "neutralisation", "obedience to authority",
                                                 "learned helplessness", "attachment theory")
                                     if re.search(re.escape(t), text, re.I)]
            f.write(json.dumps({**r, "extraction": clean}, ensure_ascii=False) + "\n")
            stats["records"] += 1
    stats["flags_true"] = sum(stats["by_construct"].values())
    stats["verified"] = stats["flags_true"]   # rule anchors are exact by construction
    stats["unverified"] = 0
    stats["instrument"] = "rule-based lexical detectors (measure.py)"
    json.dump(stats, open(os.path.join(ROOT, "data/processed/extract_stats.json"), "w"), indent=1)
    for k in ORDER:
        print("%-16s %d/%d" % (k, stats["by_construct"].get(k, 0), stats["records"]))
    print("MEASURE_DONE", stats["records"])


if __name__ == "__main__":
    main()
